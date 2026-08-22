"""
routers/scans.py — All /api/* endpoints.
API shapes frozen per APK-SENTINEL-REFERENCE.md §11.
"""

import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Scan
from app.schemas import (
    HashLookupRequest,
    HashLookupResponse,
    ScanCompletedResponse,
    ScanCreateResponse,
    ScanInProgressResponse,
    ScanSummary,
    ScansListResponse,
    StatsResponse,
)
from app.services import pipeline
from app.services.storage import (
    FileTooLargeError,
    NotAnApkError,
    clone_scan,
    check_hash_cache,
    save,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Working statuses (client should keep polling)
_WORKING_STATUSES = {"queued", "static_analysis", "decompiling", "pattern_scanning",
                     "ioc_extraction", "scoring", "ai_analysis", "building_report"}


# ---------------------------------------------------------------------------
# POST /api/scan — Upload and start pipeline
# ---------------------------------------------------------------------------

@router.post("/scan", response_model=ScanCreateResponse, status_code=202, tags=["scan"])
async def create_scan(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload an APK and start the analysis pipeline.
    Returns scan_id immediately; poll GET /api/scan/{id} for results.

    Errors: 413 file too large, 415 not an APK, 429 concurrent scan limit exceeded.
    """
    # Concurrency cap
    if pipeline.get_running_count() >= 2:
        raise HTTPException(
            status_code=429,
            detail="Too many scans in progress. Maximum 2 concurrent scans. Try again shortly.",
        )

    # Validate filename extension (quick pre-check)
    filename = file.filename or ""
    if not filename.lower().endswith(".apk"):
        raise HTTPException(
            status_code=415,
            detail="Only .apk files are accepted.",
        )

    scan_id = uuid.uuid4().hex

    # Save to disk and compute hashes
    try:
        file_info = await save(file, scan_id)
    except FileTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc))
    except NotAnApkError as exc:
        raise HTTPException(status_code=415, detail=str(exc))
    except Exception as exc:
        logger.error("Unexpected error saving upload: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.")

    # Hash-cache check — instant result for known files
    cached = check_hash_cache(file_info["sha256"], db)
    if cached:
        cloned = clone_scan(cached, scan_id, file_info["original_filename"], db)
        logger.info("Hash cache hit for scan %s", scan_id)
        return ScanCreateResponse(scan_id=cloned.id)

    # Create Scan row
    scan = Scan(
        id=scan_id,
        status="queued",
        sha256=file_info["sha256"],
        md5=file_info["md5"],
        file_size_bytes=file_info["file_size_bytes"],
        original_filename=file_info["original_filename"],
        progress_hint="Queued — waiting to start",
    )
    db.add(scan)
    db.commit()

    # Launch pipeline in background
    background_tasks.add_task(
        pipeline.run_pipeline,
        scan_id=scan_id,
        apk_path=file_info["path"],
        original_filename=file_info["original_filename"],
    )

    logger.info("Scan %s queued for %s", scan_id, file_info["original_filename"])
    return ScanCreateResponse(scan_id=scan_id)


# ---------------------------------------------------------------------------
# GET /api/scan/{scan_id} — Poll status or get full result
# ---------------------------------------------------------------------------

@router.get("/scan/{scan_id}", tags=["scan"])
async def get_scan(scan_id: str, db: Session = Depends(get_db)):
    """
    Poll scan status. Returns in-progress shape while running,
    full result shape when completed or failed.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found.")

    if scan.status in _WORKING_STATUSES:
        return ScanInProgressResponse(
            scan_id=scan.id,
            status=scan.status,
            progress_hint=scan.progress_hint,
        )

    # Deserialize JSON blobs for completed/failed scans
    return _build_completed_response(scan)


def _rescore_scan(scan: Scan) -> tuple:
    """
    Re-evaluate the scan using the CURRENT rules_engine.
    Returns (rule_score, severity, triggers, all_hits) computed live.
    This ensures any scoring calibration changes take effect immediately
    on all existing DB rows without needing manual patches or cache clears.
    """
    import json as _j
    from app.services import rules_engine as _re

    def _load(f):
        try: return _j.loads(f) if f else ([] if isinstance(f, str) else {})
        except: return []

    all_hits_raw = _load(scan.pattern_hits) or []

    try:
        _re._ensure_loaded()
        code_ids  = {r["id"] for r in _re._RULES.get("code_rules", [])}
        code_hits = [h for h in all_hits_raw if h.get("rule_id", "") in code_ids]

        result = _re.score(
            permissions       = _load(scan.permissions) or [],
            pattern_hits      = code_hits,
            iocs              = _load(scan.iocs) or {},
            manifest_flags    = _load(scan.manifest_flags) or {},
            certificate       = _load(scan.certificate) or {},
            embedded_payloads = _load(scan.embedded_payloads) or {},
            app_metadata      = _load(scan.app_metadata) or {},
            decompiled_available = bool(code_hits),
        )
        from app.services.pipeline import _merge_hits_and_triggers
        fresh_hits = _merge_hits_and_triggers(code_hits, result["triggers"])
        return result["rule_score"], result["severity"], result["triggers"], fresh_hits

    except Exception as exc:
        logger.warning("Live rescore failed for scan %s: %s", scan.id, exc)
        triggers = [h for h in all_hits_raw if "rule_id" in h]
        return scan.rule_score, scan.severity, triggers, all_hits_raw


def _build_completed_response(scan: Scan) -> ScanCompletedResponse:
    """
    Deserialize all JSON text columns into the full response schema.
    Always re-scores with the current rules_engine so calibration changes
    take effect immediately on all cached results.
    """

    def _load(field) -> Optional[dict | list]:
        if field is None:
            return None
        try:
            return json.loads(field)
        except Exception:
            return None

    # Always re-score live with current rules — no stale DB scores shown
    live_score, live_severity, live_triggers, all_hits = _rescore_scan(scan)

    return ScanCompletedResponse(
        scan_id          = scan.id,
        status           = scan.status,
        progress_hint    = scan.progress_hint,
        sha256           = scan.sha256,
        md5              = scan.md5,
        file_size_bytes  = scan.file_size_bytes,
        original_filename= scan.original_filename,
        app_metadata     = _load(scan.app_metadata),
        certificate      = _load(scan.certificate),
        permissions      = _load(scan.permissions),
        components       = _load(scan.components),
        manifest_flags   = _load(scan.manifest_flags),
        pattern_hits     = all_hits,
        iocs             = _load(scan.iocs),
        embedded_payloads= _load(scan.embedded_payloads),
        rule_score       = live_score,
        final_score      = live_score,
        severity         = live_severity,
        fraud_category   = scan.fraud_category,
        ai_status        = scan.ai_status,
        ai_analysis      = _load(scan.ai_analysis),
        triggers         = live_triggers,
        report_markdown  = scan.report_markdown,
        error_message    = scan.error_message,
        duration_ms      = scan.duration_ms,
        created_at       = scan.created_at,
    )


# ---------------------------------------------------------------------------
# GET /api/scan/{scan_id}/report — Download report file
# ---------------------------------------------------------------------------

@router.get("/scan/{scan_id}/report", tags=["scan"])
async def download_report(
    scan_id: str,
    format: str = Query("md", pattern="^(md|pdf)$"),
    db: Session = Depends(get_db),
):
    """Download the markdown or PDF threat report for a completed scan."""
    from fastapi.responses import Response

    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found.")
    if scan.status != "completed":
        raise HTTPException(status_code=400, detail="Scan is not yet completed.")
    if not scan.report_markdown:
        raise HTTPException(status_code=404, detail="Report not available for this scan.")

    if format == "pdf":
        from app.services.report_generator import ReportGenerator
        generator = ReportGenerator()
        pdf_bytes = generator.generate_pdf(scan.report_markdown)
        filename = f"apk-sentinel-report-{scan_id[:8]}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    filename = f"apk-sentinel-report-{scan_id[:8]}.md"
    return Response(
        content=scan.report_markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# POST /api/lookup/hash — Fast path for Android app
# ---------------------------------------------------------------------------

@router.post("/lookup/hash", response_model=HashLookupResponse, tags=["lookup"])
async def lookup_hash(request: HashLookupRequest, db: Session = Depends(get_db)):
    """
    Fast hash lookup — used by Android app before uploading.
    Returns instant verdict if SHA-256 was previously scanned.
    """
    scan = check_hash_cache(request.sha256, db)
    if not scan:
        return HashLookupResponse(known=False)

    return HashLookupResponse(
        known         = True,
        scan_id       = scan.id,
        severity      = scan.severity,
        final_score   = scan.final_score,
        fraud_category= scan.fraud_category,
    )


# ---------------------------------------------------------------------------
# GET /api/scans — History list with pagination
# ---------------------------------------------------------------------------

@router.get("/scans", response_model=ScansListResponse, tags=["history"])
async def list_scans(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Paginated list of past scans, optionally filtered by severity."""
    query = db.query(Scan).order_by(Scan.created_at.desc())

    if severity:
        query = query.filter(Scan.severity == severity.upper())

    total = query.count()
    scans = query.offset((page - 1) * limit).limit(limit).all()

    return ScansListResponse(
        scans=[
            ScanSummary(
                scan_id          = s.id,
                original_filename= s.original_filename,
                final_score      = s.final_score,
                severity         = s.severity,
                fraud_category   = s.fraud_category,
                status           = s.status,
                created_at       = s.created_at,
            )
            for s in scans
        ],
        total=total,
    )


# ---------------------------------------------------------------------------
# GET /api/stats — Dashboard hero strip
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=StatsResponse, tags=["stats"])
async def get_stats(db: Session = Depends(get_db)):
    """Aggregate stats for the dashboard hero strip."""
    total_scans = db.query(Scan).count()

    malicious_found = db.query(Scan).filter(
        Scan.severity.in_(["CRITICAL", "HIGH"])
    ).count()

    avg_row = db.query(func.avg(Scan.duration_ms)).filter(
        Scan.duration_ms.isnot(None)
    ).scalar()

    unique_hashes = db.query(func.count(func.distinct(Scan.sha256))).scalar() or 0

    return StatsResponse(
        total_scans     = total_scans,
        malicious_found = malicious_found,
        avg_duration_ms = float(avg_row) if avg_row else None,
        unique_hashes   = unique_hashes,
    )
