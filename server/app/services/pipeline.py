"""
pipeline.py — The analysis pipeline orchestrator.
Stages 1-6 are owned by Person A. Stages 7-8 (AI + report) are stubs
that will be filled by Person B's ai_analyst.py and report_generator.py.

Stage order (Reference §8):
  1. storage.save()           → sha256/md5/size; hash-cache check
  2. static_analysis.run()   → app_metadata, permissions, components, cert
  3. decompiler.run()        → jadx → storage/decompiled/<scan_id>/
  4. pattern_scanner.scan()  → pattern_hits[]
  5. ioc_extractor.extract() → domains/ips/urls/phones/base64
  6. rules_engine.score()    → rule_score, severity, triggers[]
  7. ai_analyst.analyze()    → LLM → ai_analysis JSON (Person B)
  8. report_generator.build()→ report_markdown (Person B)
"""

import json
import logging
import time
import traceback
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models import Scan
from app.services import (
    decompiler,
    ioc_extractor,
    pattern_scanner,
    rules_engine,
    static_analysis,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Track count of currently running scans for concurrency cap
_running_scans: int = 0


# ---------------------------------------------------------------------------
# Status helper
# ---------------------------------------------------------------------------

_PROGRESS_HINTS = {
    "queued":           "Queued — waiting to start",
    "static_analysis":  "Running static analysis (stage 2/8)",
    "decompiling":      "Decompiling bytecode (stage 3/8)",
    "pattern_scanning": "Scanning decompiled code (stage 4/8)",
    "ioc_extraction":   "Extracting indicators of compromise (stage 5/8)",
    "scoring":          "Computing risk score (stage 6/8)",
    "ai_analysis":      "AI behavioral analysis in progress (stage 7/8)",
    "building_report":  "Generating investigation report (stage 8/8)",
    "completed":        "Analysis complete",
    "failed":           "Analysis failed",
}


def _set_status(scan_id: str, status: str, db: Session, extra: dict = None):
    """Update Scan.status and progress_hint in the DB."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if scan:
        scan.status = status
        scan.progress_hint = _PROGRESS_HINTS.get(status, status)
        if extra:
            for k, v in extra.items():
                setattr(scan, k, v)
        db.commit()
    logger.info("[%s] Status → %s", scan_id, status)


def _json_dump(obj) -> Optional[str]:
    """Safely JSON-serialize an object."""
    if obj is None:
        return None
    try:
        return json.dumps(obj)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Concurrency guard
# ---------------------------------------------------------------------------

def get_running_count() -> int:
    return _running_scans


# ---------------------------------------------------------------------------
# Main pipeline entry point (called via FastAPI BackgroundTasks)
# ---------------------------------------------------------------------------

def run_pipeline(scan_id: str, apk_path: str, original_filename: str):
    """
    Full 8-stage analysis pipeline.
    Runs in a background thread; creates its own DB session.
    Any stage failure is caught and logged — partial results always shipped.
    """
    global _running_scans

    start_time = time.monotonic()
    db = SessionLocal()

    try:
        _running_scans += 1
        _run_stages(scan_id, apk_path, original_filename, db, start_time)
    except Exception as exc:
        logger.error("[%s] Unhandled pipeline error: %s\n%s", scan_id, exc, traceback.format_exc())
        try:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            _set_status(scan_id, "failed", db, {
                "error_message": str(exc)[:500],
                "duration_ms": duration_ms,
            })
        except Exception:
            pass
    finally:
        _running_scans -= 1
        db.close()


def _run_stages(scan_id: str, apk_path: str, original_filename: str, db: Session, start_time: float):
    """Inner pipeline — each stage is wrapped in try/except for resilience."""

    # -------------------------------------------------------------------------
    # Stage 2: Static analysis
    # -------------------------------------------------------------------------
    _set_status(scan_id, "static_analysis", db)
    static_result = {}
    try:
        static_result = static_analysis.run(apk_path)
        if static_result.get("error"):
            logger.warning("[%s] Static analysis partial error: %s", scan_id, static_result["error"])
    except Exception as exc:
        logger.error("[%s] Stage 2 (static_analysis) failed: %s", scan_id, exc, exc_info=True)

    # Persist static results
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if scan:
        scan.app_metadata    = _json_dump(static_result.get("app_metadata"))
        scan.permissions     = _json_dump(static_result.get("permissions"))
        scan.components      = _json_dump(static_result.get("components"))
        scan.manifest_flags  = _json_dump(static_result.get("manifest_flags"))
        scan.certificate     = _json_dump(static_result.get("certificate"))
        scan.embedded_payloads = _json_dump(static_result.get("embedded_payloads"))
        db.commit()

    # -------------------------------------------------------------------------
    # Stage 3: Decompilation
    # -------------------------------------------------------------------------
    _set_status(scan_id, "decompiling", db)
    decompiled_ok = False
    try:
        decompiled_ok = decompiler.run(scan_id, apk_path)
    except Exception as exc:
        logger.error("[%s] Stage 3 (decompiler) failed: %s", scan_id, exc, exc_info=True)

    # -------------------------------------------------------------------------
    # Stage 4: Pattern scanning (only if decompilation succeeded)
    # -------------------------------------------------------------------------
    _set_status(scan_id, "pattern_scanning", db)
    pattern_hits = []
    if decompiled_ok:
        try:
            code_rules = rules_engine._RULES.get("code_rules", [])
            if not code_rules:
                rules_engine._ensure_loaded()
                code_rules = rules_engine._RULES.get("code_rules", [])
            pattern_hits = pattern_scanner.scan(scan_id, code_rules)
        except Exception as exc:
            logger.error("[%s] Stage 4 (pattern_scanner) failed: %s", scan_id, exc, exc_info=True)
    else:
        logger.info("[%s] Skipping pattern scan — no decompiled output", scan_id)

    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if scan:
        scan.pattern_hits = _json_dump(pattern_hits)
        db.commit()

    # -------------------------------------------------------------------------
    # Stage 5: IOC extraction
    # -------------------------------------------------------------------------
    _set_status(scan_id, "ioc_extraction", db)
    iocs = {}
    try:
        iocs = ioc_extractor.extract(scan_id, apk_path)
    except Exception as exc:
        logger.error("[%s] Stage 5 (ioc_extractor) failed: %s", scan_id, exc, exc_info=True)

    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if scan:
        scan.iocs = _json_dump(iocs)
        db.commit()

    # -------------------------------------------------------------------------
    # Stage 6: Rules engine scoring
    # -------------------------------------------------------------------------
    _set_status(scan_id, "scoring", db)
    scoring_result = {"rule_score": 0, "severity": "SAFE", "triggers": []}
    try:
        scoring_result = rules_engine.score(
            permissions       = static_result.get("permissions", []),
            pattern_hits      = pattern_hits,
            iocs              = iocs,
            manifest_flags    = static_result.get("manifest_flags", {}),
            certificate       = static_result.get("certificate", {}),
            embedded_payloads = static_result.get("embedded_payloads", {}),
            app_metadata      = static_result.get("app_metadata", {}),
            decompiled_available = decompiled_ok,
        )
    except Exception as exc:
        logger.error("[%s] Stage 6 (rules_engine) failed: %s", scan_id, exc, exc_info=True)

    rule_score = scoring_result.get("rule_score", 0)
    severity   = scoring_result.get("severity", "SAFE")
    triggers   = scoring_result.get("triggers", [])

    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if scan:
        # Store triggers inside pattern_hits field (or as a merged JSON blob)
        # We merge triggers into pattern_hits for the ScoreBreakdown UI
        scan.rule_score  = rule_score
        scan.final_score = rule_score   # AI may adjust ±5 later (Person B)
        scan.severity    = severity
        # Re-store pattern_hits merged with triggers for the UI
        merged_hits = _merge_hits_and_triggers(pattern_hits, triggers)
        scan.pattern_hits = _json_dump(merged_hits)
        db.commit()

    # -------------------------------------------------------------------------
    # Stage 7: AI analysis (Person B — stub)
    # -------------------------------------------------------------------------
    _set_status(scan_id, "ai_analysis", db)
    ai_analysis_result = None
    ai_status = "unavailable"

    try:
        # Person B owns this — import guard prevents crash if not yet implemented
        from app.services import ai_analyst  # type: ignore
        ai_analysis_result, ai_status = ai_analyst.analyze(
            scan_id          = scan_id,
            app_metadata     = static_result.get("app_metadata", {}),
            permissions      = static_result.get("permissions", []),
            pattern_hits     = pattern_hits,
            iocs             = iocs,
            triggers         = triggers,
            decompiled_ok    = decompiled_ok,
        )
        # AI may return score adjustment
        if isinstance(ai_analysis_result, dict):
            fraud_category = ai_analysis_result.get("fraud_category")
            # AI score adjustment ±5 from rule_score
            ai_score_adj = ai_analysis_result.get("score_adjustment", 0)
            final_score = max(0, min(100, rule_score + ai_score_adj))
        else:
            fraud_category = None
            final_score = rule_score

    except ImportError:
        # Person B hasn't implemented ai_analyst yet — graceful degradation
        logger.info("[%s] ai_analyst not available — using rules-only verdict", scan_id)
        fraud_category = None
        final_score = rule_score
        ai_status = "unavailable"

    except Exception as exc:
        logger.error("[%s] Stage 7 (ai_analyst) failed: %s", scan_id, exc, exc_info=True)
        fraud_category = None
        final_score = rule_score
        ai_status = "unavailable"

    # -------------------------------------------------------------------------
    # Stage 8: Report generation (Person B — stub)
    # -------------------------------------------------------------------------
    _set_status(scan_id, "building_report", db)
    report_markdown = None

    try:
        from app.services import report_generator  # type: ignore
        report_markdown = report_generator.build(
            scan_id       = scan_id,
            app_metadata  = static_result.get("app_metadata", {}),
            permissions   = static_result.get("permissions", []),
            triggers      = triggers,
            iocs          = iocs,
            ai_analysis   = ai_analysis_result,
            rule_score    = rule_score,
            final_score   = final_score,
            severity      = severity,
        )
    except ImportError:
        logger.info("[%s] report_generator not available — skipping report", scan_id)
    except Exception as exc:
        logger.error("[%s] Stage 8 (report_generator) failed: %s", scan_id, exc, exc_info=True)

    # -------------------------------------------------------------------------
    # Finalize
    # -------------------------------------------------------------------------
    duration_ms = int((time.monotonic() - start_time) * 1000)

    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if scan:
        scan.final_score     = final_score
        scan.fraud_category  = fraud_category
        scan.ai_status       = ai_status
        scan.ai_analysis     = _json_dump(ai_analysis_result)
        scan.report_markdown = report_markdown
        scan.duration_ms     = duration_ms
        scan.status          = "completed"
        scan.progress_hint   = _PROGRESS_HINTS["completed"]
        db.commit()

    logger.info(
        "[%s] Pipeline complete: score=%d severity=%s duration=%dms",
        scan_id, final_score, severity, duration_ms
    )


def _merge_hits_and_triggers(pattern_hits: list, triggers: list) -> list:
    """
    Merge code-rule pattern hits with all triggers into one unified list
    for the ScoreBreakdown UI. Deduplicates by rule_id.
    """
    seen_ids = set()
    merged = []

    # Add triggers first (complete picture)
    for t in triggers:
        rule_id = t.get("rule_id", "")
        if rule_id not in seen_ids:
            merged.append(t)
            seen_ids.add(rule_id)

    # Add pattern hits not already in triggers
    for h in pattern_hits:
        rule_id = h.get("rule_id", "")
        if rule_id not in seen_ids:
            merged.append(h)
            seen_ids.add(rule_id)

    return merged


# ---------------------------------------------------------------------------
# CLI entry point for Block 2 verification
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import uuid

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    if "--sample" not in sys.argv:
        print("Usage: python -m app.services.pipeline --sample <path/to/file.apk>")
        sys.exit(1)

    sample_path = sys.argv[sys.argv.index("--sample") + 1]
    if not os.path.exists(sample_path):
        print(f"File not found: {sample_path}")
        sys.exit(1)

    # Bootstrap DB
    from app.database import create_tables
    create_tables()

    test_scan_id = uuid.uuid4().hex
    db = SessionLocal()

    # Create a minimal Scan row
    test_scan = Scan(
        id=test_scan_id,
        status="queued",
        sha256="test",
        original_filename=os.path.basename(sample_path),
    )
    db.add(test_scan)
    db.commit()
    db.close()

    print(f"\n=== APK Sentinel Pipeline CLI ===")
    print(f"Scan ID : {test_scan_id}")
    print(f"Sample  : {sample_path}\n")

    run_pipeline(test_scan_id, sample_path, os.path.basename(sample_path))

    # Print results
    db = SessionLocal()
    result = db.query(Scan).filter(Scan.id == test_scan_id).first()
    db.close()

    if result:
        print(f"\n--- Results ---")
        print(f"Status        : {result.status}")
        print(f"Rule Score    : {result.rule_score}")
        print(f"Final Score   : {result.final_score}")
        print(f"Severity      : {result.severity}")
        print(f"Fraud Category: {result.fraud_category}")
        print(f"AI Status     : {result.ai_status}")
        print(f"Duration      : {result.duration_ms} ms")
        if result.pattern_hits:
            triggers = json.loads(result.pattern_hits)
            print(f"\nTriggered Rules ({len(triggers)}):")
            for t in triggers:
                print(f"  [{t.get('weight', 0):3d}] {t.get('rule_id', '')} — {t.get('evidence', '')[:80]}")
        if result.error_message:
            print(f"\nError: {result.error_message}")
