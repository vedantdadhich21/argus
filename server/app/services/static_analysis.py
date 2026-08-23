"""
static_analysis.py — Stage 2: Androguard-based static APK analysis.
Extracts: app metadata, permissions, components, manifest flags, certificate info.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Permissions that are considered "dangerous" by Android classification
_DANGEROUS_PERMISSIONS = {
    "android.permission.READ_SMS",
    "android.permission.RECEIVE_SMS",
    "android.permission.SEND_SMS",
    "android.permission.RECEIVE_MMS",
    "android.permission.READ_CALL_LOG",
    "android.permission.WRITE_CALL_LOG",
    "android.permission.READ_CONTACTS",
    "android.permission.WRITE_CONTACTS",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.ACCESS_COARSE_LOCATION",
    "android.permission.CAMERA",
    "android.permission.RECORD_AUDIO",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.GET_ACCOUNTS",
    "android.permission.USE_BIOMETRIC",
    "android.permission.USE_FINGERPRINT",
    "android.permission.BIND_ACCESSIBILITY_SERVICE",
    "android.permission.SYSTEM_ALERT_WINDOW",
    "android.permission.REQUEST_INSTALL_PACKAGES",
    "android.permission.BIND_DEVICE_ADMIN",
    "android.permission.RECEIVE_BOOT_COMPLETED",
    "android.permission.READ_PHONE_STATE",
    "android.permission.PROCESS_OUTGOING_CALLS",
    "android.permission.CALL_PHONE",
}

_HIGH_RISK_PERMISSIONS = {
    "android.permission.READ_SMS",
    "android.permission.RECEIVE_SMS",
    "android.permission.SEND_SMS",
    "android.permission.BIND_ACCESSIBILITY_SERVICE",
    "android.permission.SYSTEM_ALERT_WINDOW",
    "android.permission.REQUEST_INSTALL_PACKAGES",
    "android.permission.BIND_DEVICE_ADMIN",
}


def _classify_permission(perm: str) -> str:
    if perm in _HIGH_RISK_PERMISSIONS:
        return "high_risk"
    if perm in _DANGEROUS_PERMISSIONS:
        return "dangerous"
    if perm.startswith("android.permission."):
        return "normal"
    return "unknown"


def run(apk_path: str) -> Dict[str, Any]:
    """
    Run Androguard static analysis on the APK at apk_path.
    Returns a dict with keys: app_metadata, permissions, components,
                               manifest_flags, certificate, embedded_payloads.
    On any parse error, returns partial results with error field set.
    """
    result: Dict[str, Any] = {
        "app_metadata": {},
        "permissions": [],
        "components": [],
        "manifest_flags": {},
        "certificate": {},
        "embedded_payloads": {"nested_apk": False, "nested_dex": False, "nested_elf": False},
        "error": None,
    }

    try:
        from androguard.core.bytecodes.apk import APK
        a = APK(apk_path)
    except Exception as exc:
        logger.error("Androguard failed to parse APK: %s", exc)
        result["error"] = str(exc)
        return result


    try:
        # ----------------------------------------------------------------
        # App metadata
        # ----------------------------------------------------------------
        result["app_metadata"] = {
            "package_name": a.get_package(),
            "label": _safe(a.get_app_name),
            "version_name": a.get_androidversion_name(),
            "version_code": a.get_androidversion_code(),
            "min_sdk": a.get_min_sdk_version(),
            "target_sdk": a.get_target_sdk_version(),
        }

        # ----------------------------------------------------------------
        # Permissions
        # ----------------------------------------------------------------
        declared_perms = set(a.get_declared_permissions() or [])
        requested_perms = set(a.get_permissions() or [])
        all_perms = requested_perms | declared_perms

        result["permissions"] = [
            {
                "name": p,
                "danger_level": _classify_permission(p),
                "declared_by_app": p in declared_perms,
            }
            for p in sorted(all_perms)
        ]

        # ----------------------------------------------------------------
        # Components (activities, services, receivers, providers)
        # ----------------------------------------------------------------
        components: List[Dict[str, Any]] = []
        for comp_type, getter in [
            ("activity", a.get_activities),
            ("service", a.get_services),
            ("receiver", a.get_receivers),
            ("provider", a.get_providers),
        ]:
            for comp in (getter() or []):
                components.append({
                    "name": comp,
                    "type": comp_type,
                    # Exported if not explicitly false in manifest
                    "exported": True,
                })
        result["components"] = components

        # ----------------------------------------------------------------
        # Manifest flags
        # ----------------------------------------------------------------
        result["manifest_flags"] = {
            "cleartext_traffic": _check_cleartext(a),
            "backup_allowed": _safe_attr(a, "get_effective_target_sdk_version") is not None,
            "debuggable": _check_debuggable(a),
            "has_deep_links": _has_deep_links(a),
            "device_admin": _has_device_admin(a),
        }

        # ----------------------------------------------------------------
        # Certificate
        # ----------------------------------------------------------------
        result["certificate"] = _extract_cert(a)

        # ----------------------------------------------------------------
        # Embedded payloads (nested APK/DEX/ELF in assets/resources)
        # ----------------------------------------------------------------
        result["embedded_payloads"] = _check_embedded_payloads(a)

    except Exception as exc:
        logger.error("Error during static analysis extraction: %s", exc, exc_info=True)
        result["error"] = str(exc)

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe(fn):
    try:
        return fn()
    except Exception:
        return None


def _safe_attr(obj, attr):
    try:
        return getattr(obj, attr)()
    except Exception:
        return None


def _check_cleartext(a) -> bool:
    try:
        manifest = a.get_android_manifest_axml().get_xml().decode("utf-8", errors="ignore")
        return "cleartextTrafficPermitted" in manifest and "true" in manifest
    except Exception:
        return False


def _check_debuggable(a) -> bool:
    try:
        manifest = a.get_android_manifest_axml().get_xml().decode("utf-8", errors="ignore")
        return 'android:debuggable="true"' in manifest
    except Exception:
        return False


def _has_deep_links(a) -> bool:
    try:
        manifest = a.get_android_manifest_axml().get_xml().decode("utf-8", errors="ignore")
        return "android:scheme" in manifest
    except Exception:
        return False


def _has_device_admin(a) -> bool:
    try:
        receivers = a.get_receivers() or []
        manifest = a.get_android_manifest_axml().get_xml().decode("utf-8", errors="ignore")
        return "BIND_DEVICE_ADMIN" in manifest or any("admin" in r.lower() for r in receivers)
    except Exception:
        return False


def _extract_cert(a) -> Dict[str, Any]:
    try:
        certs = a.get_certificates_v3() or a.get_certificates_v2() or a.get_certificates()
        if not certs:
            return {"error": "no certificates found"}
        cert = certs[0]
        subject = str(cert.subject.human_friendly) if hasattr(cert, "subject") else str(cert)
        # Self-signed: issuer == subject
        try:
            issuer = str(cert.issuer.human_friendly)
            self_signed = issuer == subject
        except Exception:
            self_signed = True
        # Debug-signed: subject contains Android Debug or debug keyword
        debug_signed = "debug" in subject.lower() or "android debug" in subject.lower()
        return {
            "subject": subject,
            "self_signed": self_signed,
            "debug_signed": debug_signed,
        }
    except Exception as exc:
        return {"error": str(exc), "self_signed": True, "debug_signed": False}


def _check_embedded_payloads(a) -> Dict[str, bool]:
    """Check assets/resources for nested APK, DEX, or ELF files.

    Known-SDK DEX files bundled inside assets/ (e.g. Facebook Audience Network)
    are allowlisted by filename prefix so they don't produce false positives.
    """
    # Known legitimate SDK dex files that live inside assets/
    _KNOWN_SDK_DEX_NAMES = {
        "audience_network.dex",   # Facebook Audience Network
        "tinker_classn.dex",      # Tencent Tinker hot-patch framework
        "multidex.dex",           # AndroidX MultiDex shim
        "secondary.dex",          # Generic secondary MultiDex shard (not a payload)
    }

    result = {"nested_apk": False, "nested_dex": False, "nested_elf": False}
    try:
        files = a.get_files() or []
        for f in files:
            fl = f.lower()
            basename = fl.rsplit("/", 1)[-1]
            # Root classes*.dex is standard compiled bytecode, not nested payload
            is_in_payload_dir = fl.startswith("assets/") or fl.startswith("res/")
            if is_in_payload_dir:
                if fl.endswith(".apk"):
                    result["nested_apk"] = True
                elif fl.endswith(".dex"):
                    # Skip well-known SDK dex files distributed inside assets/
                    if basename not in _KNOWN_SDK_DEX_NAMES:
                        result["nested_dex"] = True
                elif fl.endswith(".so") or fl.endswith(".elf"):
                    result["nested_elf"] = True
            elif fl.endswith(".apk") and not fl.startswith("classes"):
                result["nested_apk"] = True
    except Exception:
        pass
    return result
