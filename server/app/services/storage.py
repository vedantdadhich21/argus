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
    """
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
        pattern_hits=existing.pattern_hits,
        iocs=existing.iocs,
        embedded_payloads=existing.embedded_payloads,
        rule_score=existing.rule_score,
        final_score=existing.final_score,
        severity=existing.severity,
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
