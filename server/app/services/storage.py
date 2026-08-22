"""
storage.py — APK file saving, hash computation, size/type validation, and hash-cache lookup.
Owns Stage 1 of the analysis pipeline.
"""

import hashlib
import logging
import os
import uuid
from typing import Tuple

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Scan

logger = logging.getLogger(__name__)
settings = get_settings()

# APK is a ZIP — magic bytes: PK (0x50 0x4B)
_ZIP_MAGIC = b"\x50\x4b"


class FileTooLargeError(Exception):
    pass


class NotAnApkError(Exception):
    pass


def _compute_hashes(path: str) -> Tuple[str, str]:
    """Return (sha256_hex, md5_hex) for the file at path."""
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
            md5.update(chunk)
    return sha256.hexdigest(), md5.hexdigest()


def _check_magic(path: str) -> bool:
    """Return True if file starts with PK magic bytes (ZIP/APK)."""
    with open(path, "rb") as f:
        header = f.read(2)
    return header == _ZIP_MAGIC


async def save(upload: UploadFile, scan_id: str) -> dict:
    """
    Save the uploaded APK to disk, validate it, and compute hashes.

    Returns a dict with keys: path, sha256, md5, file_size_bytes, original_filename

    Raises:
        FileTooLargeError: if file exceeds MAX_UPLOAD_MB
        NotAnApkError: if file doesn't have ZIP magic bytes
    """
    apk_dir = os.path.join(settings.storage_dir, "apks")
    dest_path = os.path.join(apk_dir, f"{scan_id}.apk")

    # Stream to disk while counting bytes (avoid loading entire file into RAM)
    file_size = 0
    max_bytes = settings.max_upload_bytes

    with open(dest_path, "wb") as out:
        while True:
            chunk = await upload.read(65536)
            if not chunk:
                break
            file_size += len(chunk)
            if file_size > max_bytes:
                out.close()
                os.remove(dest_path)
                raise FileTooLargeError(
                    f"File exceeds {settings.max_upload_mb} MB limit "
                    f"(received >{file_size // (1024*1024)} MB)"
                )
            out.write(chunk)

    # Validate APK magic bytes
    if not _check_magic(dest_path):
        os.remove(dest_path)
        raise NotAnApkError("File is not a valid APK (missing ZIP/PK magic bytes)")

    sha256, md5 = _compute_hashes(dest_path)
    logger.info("Saved APK scan_id=%s sha256=%s size=%d bytes", scan_id, sha256, file_size)

    return {
        "path": dest_path,
        "sha256": sha256,
        "md5": md5,
        "file_size_bytes": file_size,
        "original_filename": upload.filename or "unknown.apk",
    }


def check_hash_cache(sha256: str, db: Session) -> Scan | None:
    """
    Look up sha256 in completed scans.
    Returns the completed Scan row if found, else None.
    """
    return (
        db.query(Scan)
        .filter(Scan.sha256 == sha256, Scan.status == "completed")
        .order_by(Scan.created_at.desc())
        .first()
    )


def clone_scan(existing: Scan, new_scan_id: str, original_filename: str, db: Session) -> Scan:
    """
    Clone a completed scan result for a duplicate file.
    Returns a new Scan row with status=completed instantly.

    NOTE: We re-score using the current rules_engine so that any scoring
    calibration changes take effect immediately on hash-cached files.
    """
    import json as _json
    # Re-score with current rules engine to pick up any weight/logic changes
    try:
        from app.services import rules_engine as _re
        permissions      = _json.loads(existing.permissions or "[]")
        pattern_hits_raw = _json.loads(existing.pattern_hits or "[]")
        iocs             = _json.loads(existing.iocs or "{}")
        manifest_flags   = _json.loads(existing.manifest_flags or "{}")
        certificate      = _json.loads(existing.certificate or "{}")
        embedded_payloads= _json.loads(existing.embedded_payloads or "{}")
        app_metadata     = _json.loads(existing.app_metadata or "{}")

        # Filter pattern_hits to only raw code hits (no perm/meta triggers)
        # so rules_engine can re-evaluate them fresh
        _re._ensure_loaded()
        code_hit_ids = {r["id"] for r in _re._RULES.get("code_rules", [])}
        raw_code_hits = [h for h in pattern_hits_raw if h.get("rule_id", "") in code_hit_ids]
        has_decompiled = bool(raw_code_hits)

        rescored = _re.score(
            permissions=permissions, pattern_hits=raw_code_hits, iocs=iocs,
            manifest_flags=manifest_flags, certificate=certificate,
            embedded_payloads=embedded_payloads, app_metadata=app_metadata,
            decompiled_available=has_decompiled,
        )
        new_rule_score = rescored["rule_score"]
        new_severity   = rescored["severity"]

        # Rebuild merged hits with fresh triggers
        from app.services.pipeline import _merge_hits_and_triggers
        new_pattern_hits = _json.dumps(_merge_hits_and_triggers(raw_code_hits, rescored["triggers"]))
        logger.info("Hash cache rescore: %s → score %d (was %d)", new_scan_id, new_rule_score, existing.rule_score or 0)
    except Exception as exc:
        logger.warning("clone_scan rescore failed, using cached score: %s", exc)
        new_rule_score   = existing.rule_score
        new_severity     = existing.severity
        new_pattern_hits = existing.pattern_hits

    new_scan = Scan(
        id=new_scan_id,
        status="completed",
        sha256=existing.sha256,
        md5=existing.md5,
        file_size_bytes=existing.file_size_bytes,
        original_filename=original_filename,
        app_metadata=existing.app_metadata,
        certificate=existing.certificate,
        permissions=existing.permissions,
        components=existing.components,
        manifest_flags=existing.manifest_flags,
        pattern_hits=new_pattern_hits,
        iocs=existing.iocs,
        embedded_payloads=existing.embedded_payloads,
        rule_score=new_rule_score,
        final_score=new_rule_score,
        severity=new_severity,
        fraud_category=existing.fraud_category,
        ai_status=existing.ai_status,
        ai_analysis=existing.ai_analysis,
        report_markdown=existing.report_markdown,
        duration_ms=0,
        progress_hint="Instant result — previously scanned file",
    )
    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)
    logger.info("Hash cache hit: cloned scan %s → %s", existing.id, new_scan_id)
    return new_scan


def get_apk_path(scan_id: str) -> str:
    return os.path.join(settings.storage_dir, "apks", f"{scan_id}.apk")


def get_decompiled_dir(scan_id: str) -> str:
    return os.path.join(settings.storage_dir, "decompiled", scan_id)


def get_report_path(scan_id: str) -> str:
    return os.path.join(settings.storage_dir, "reports", f"{scan_id}.md")
