"""
decompiler.py — Stage 3: jadx subprocess wrapper.
Decompiles APK bytecode to .java source files under storage/decompiled/<scan_id>/.
On failure or timeout: logs and returns False — pipeline continues without code rules.
"""

import logging
import os
import shutil
import subprocess
from typing import List

from app.config import get_settings
from app.services.storage import get_decompiled_dir

logger = logging.getLogger(__name__)
settings = get_settings()

_JADX_TIMEOUT = 60  # seconds


def run(scan_id: str, apk_path: str) -> bool:
    """
    Decompile apk_path using jadx into storage/decompiled/<scan_id>/.

    Returns:
        True  — decompilation succeeded, .java files present
        False — jadx missing, timed out, or failed (caller continues gracefully)
    """
    output_dir = get_decompiled_dir(scan_id)

    # Clean any previous run
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    jadx_bin = settings.jadx_path

    # Verify jadx is available
    if not _jadx_available(jadx_bin):
        logger.warning("jadx not found at '%s' — skipping decompilation for scan %s", jadx_bin, scan_id)
        return False

    cmd = [
        jadx_bin,
        "--output-dir", output_dir,
        "--no-res",          # skip resources, only sources — much faster
        "--threads-count", "4",
        apk_path,
    ]

    logger.info("Starting jadx decompilation for scan %s (timeout=%ds)", scan_id, _JADX_TIMEOUT)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=_JADX_TIMEOUT,
        )

        if result.returncode != 0:
            logger.warning(
                "jadx returned non-zero exit code %d for scan %s: %s",
                result.returncode, scan_id, result.stderr[:500]
            )

        java_count = _count_java_files(output_dir)
        if java_count == 0:
            logger.warning("jadx produced 0 .java files for scan %s", scan_id)
            return False

        logger.info("jadx produced %d .java files for scan %s", java_count, scan_id)
        return True

    except subprocess.TimeoutExpired:
        logger.error("jadx timed out after %ds for scan %s — killing process", _JADX_TIMEOUT, scan_id)
        java_count = _count_java_files(output_dir)
        return java_count > 0

    except FileNotFoundError:
        logger.error("jadx binary not found: '%s' for scan %s", jadx_bin, scan_id)
        return False

    except Exception as exc:
        logger.error("Unexpected jadx error for scan %s: %s", scan_id, exc, exc_info=True)
        return False


def _jadx_available(jadx_bin: str) -> bool:
    """Check if jadx binary is executable."""
    try:
        result = subprocess.run(
            [jadx_bin, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def _count_java_files(directory: str) -> int:
    """Count .java files in directory tree."""
    count = 0
    try:
        for _, _, files in os.walk(directory):
            count += sum(1 for f in files if f.endswith(".java"))
    except Exception:
        pass
    return count


def get_java_files(scan_id: str) -> List[str]:
    """Return list of absolute paths to all .java files in decompiled output."""
    output_dir = get_decompiled_dir(scan_id)
    java_files = []
    try:
        for root, _, files in os.walk(output_dir):
            for f in files:
                if f.endswith(".java"):
                    java_files.append(os.path.join(root, f))
    except Exception:
        pass
    return java_files


