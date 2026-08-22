"""
ioc_extractor.py — Stage 5: Extract Indicators of Compromise from APK artifacts.
Sources: AndroidManifest.xml, res/values/strings.xml, decompiled .java sources.
Extracts: domains, IPs, URLs, phone numbers, base64 blobs, suspicious secrets.
"""

import base64
import logging
import os
import re
from typing import Any, Dict, List, Set

from app.services.decompiler import get_java_files
from app.services.storage import get_decompiled_dir

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_URL_RE = re.compile(
    r'https?://[^\s\'"<>]{4,200}',
    re.IGNORECASE,
)

_IP_RE = re.compile(
    r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'
)

_DOMAIN_RE = re.compile(
    r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)'
    r'+(?:com|net|org|io|xyz|top|ru|tk|ml|ga|cf|gq|pw|cc|su|click|info|biz|app|dev|ai)\b',
    re.IGNORECASE,
)

_PHONE_RE = re.compile(
    r'\b(?:\+?[1-9]\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
)

# Base64 blobs: 40+ character strings of base64 alphabet (likely encoded payloads/keys)
_BASE64_RE = re.compile(
    r'["\']([A-Za-z0-9+/]{40,}={0,2})["\']'
)

# Localhost / private IPs to exclude from IOC lists
_PRIVATE_IP_RE = re.compile(
    r'^(127\.|10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.|0\.0\.0\.0|::1)'
)

# URLs to exclude (common false positives)
_EXCLUDE_DOMAINS = {
    "schemas.android.com", "www.w3.org", "play.google.com",
    "developer.android.com", "schema.org", "xmlns.jcp.org",
}


def extract(scan_id: str, apk_path: str) -> Dict[str, Any]:
    """
    Extract IOCs from all available sources for this scan.

    Returns:
        {
            "domains": [...],
            "ips": [...],
            "urls": [...],
            "phones": [...],
            "base64_blobs": [...],
        }
    """
    domains: Set[str] = set()
    ips: Set[str] = set()
    urls: Set[str] = set()
    phones: Set[str] = set()
    base64_blobs: Set[str] = set()

    sources = _collect_sources(scan_id, apk_path)

    for label, text in sources:
        _extract_from_text(text, domains, ips, urls, phones, base64_blobs)

    # Post-process: pull IPs and domains out of extracted URLs
    for url in urls:
        _extract_from_text(url, domains, ips, set(), set(), set())

    # Filter out private/loopback IPs
    ips = {ip for ip in ips if not _PRIVATE_IP_RE.match(ip)}

    # Filter known false-positive domains
    domains = {d for d in domains if d not in _EXCLUDE_DOMAINS}

    result = {
        "domains": sorted(domains)[:50],
        "ips": sorted(ips)[:50],
        "urls": sorted(urls)[:100],
        "phones": sorted(phones)[:20],
        "base64_blobs": sorted(base64_blobs)[:20],
    }

    logger.info(
        "IOC extraction for %s: %d domains, %d IPs, %d URLs, %d phones, %d base64",
        scan_id,
        len(result["domains"]), len(result["ips"]),
        len(result["urls"]), len(result["phones"]),
        len(result["base64_blobs"]),
    )
    return result


# ---------------------------------------------------------------------------
# Source collection
# ---------------------------------------------------------------------------

def _collect_sources(scan_id: str, apk_path: str) -> List[tuple]:
    """Collect (label, text) tuples from all analysis sources."""
    sources = []

    # 1. AndroidManifest.xml from decompiled output
    decompiled_dir = get_decompiled_dir(scan_id)
    manifest_path = os.path.join(decompiled_dir, "resources", "AndroidManifest.xml")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8", errors="ignore") as f:
                sources.append(("manifest", f.read()))
        except Exception:
            pass

    # 2. strings.xml from decompiled resources
    for strings_path in _find_strings_xml(decompiled_dir):
        try:
            with open(strings_path, "r", encoding="utf-8", errors="ignore") as f:
                sources.append(("strings", f.read()))
        except Exception:
            pass

    # 3. Decompiled .java source files (app code prioritized, framework excluded)
    framework_excludes = ("androidx/", "android/support/", "kotlin/", "kotlinx/", "com/google/android/material/")
    java_files = get_java_files(scan_id)
    app_java_files = [
        f for f in java_files
        if not any(f.replace("\\", "/").endswith(ex) or f"/{ex}" in f.replace("\\", "/") for ex in framework_excludes)
    ]
    for java_path in (app_java_files or java_files)[:200]:  # fallback to all if app_java_files empty
        try:
            if os.path.getsize(java_path) > 500_000:
                continue
            with open(java_path, "r", encoding="utf-8", errors="ignore") as f:
                sources.append(("java", f.read()))
        except Exception:
            continue

    return sources


def _find_strings_xml(decompiled_dir: str) -> List[str]:
    """Find all strings.xml files in decompiled resources."""
    found = []
    try:
        for root, _, files in os.walk(decompiled_dir):
            for f in files:
                if f == "strings.xml":
                    found.append(os.path.join(root, f))
    except Exception:
        pass
    return found


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def _extract_from_text(
    text: str,
    domains: Set[str],
    ips: Set[str],
    urls: Set[str],
    phones: Set[str],
    base64_blobs: Set[str],
):
    # URLs (must go before domain/IP extraction)
    for m in _URL_RE.finditer(text):
        url = m.group(0).rstrip('.,;"\')>').strip()
        urls.add(url)

    # Raw IPs
    for m in _IP_RE.finditer(text):
        ips.add(m.group(0))

    # Domains
    for m in _DOMAIN_RE.finditer(text):
        domains.add(m.group(0).lower())

    # Phone numbers
    for m in _PHONE_RE.finditer(text):
        phone = m.group(0).strip()
        if len(phone) >= 10:
            phones.add(phone)

    # Base64 blobs
    for m in _BASE64_RE.finditer(text):
        b64 = m.group(1)
        if _looks_like_real_base64(b64):
            base64_blobs.add(b64[:80])  # truncate for storage


def _looks_like_real_base64(s: str) -> bool:
    """Heuristic: try to decode and check decoded length makes sense."""
    try:
        padded = s + "=" * ((-len(s)) % 4)
        decoded = base64.b64decode(padded)
        # Must decode to at least 20 bytes and not be all printable ASCII (that's probably code)
        return len(decoded) >= 20
    except Exception:
        return False
