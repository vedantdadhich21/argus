"""
rules_engine.py — Stage 6: Weighted scoring against all rule categories.
Loads rules.yaml, evaluates permission/code/ioc/metadata rules,
returns rule_score (0-100), severity band, and triggers[] list.
"""

import json
import logging
import os
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)

# Path to rules.yaml (relative to this file's package root)
_RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "rules.yaml")

# Legitimate banking app package names for typosquatting detection
_LEGIT_PACKAGES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "legit_banking_packages.json"
)

# Severity bands — must match client/src/lib/severity.js
_SEVERITY_BANDS = [
    (75, "CRITICAL"),
    (45, "HIGH"),
    (20, "MEDIUM"),
    (1,  "LOW"),
    (0,  "SAFE"),
]


def _load_rules() -> Dict[str, Any]:
    """Load and cache rules.yaml. Called once per process."""
    try:
        with open(_RULES_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as exc:
        logger.error("Failed to load rules.yaml: %s", exc)
        return {}


def _load_legit_packages() -> List[str]:
    try:
        if os.path.exists(_LEGIT_PACKAGES_PATH):
            with open(_LEGIT_PACKAGES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


# Module-level cache
_RULES: Dict[str, Any] = {}
_LEGIT_PACKAGES: List[str] = []


def _ensure_loaded():
    global _RULES, _LEGIT_PACKAGES
    if not _RULES:
        _RULES = _load_rules()
        _LEGIT_PACKAGES = _load_legit_packages()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Rules that are always self-sufficient (count at full weight even without
# any high-risk permission hit). These have no false-positive equivalent in
# a legitimate app.
# ---------------------------------------------------------------------------
_SELF_SUFFICIENT_CODE_RULES = {
    "CODE_SMS_ABORT",    # abortBroadcast() — no legitimate app silently deletes SMS
    "CODE_FORWARD_SMS",  # SmsManager.sendTextMessage in non-SMS app = OTP exfiltration
    "CODE_EXEC",         # Runtime.exec() — shell execution is almost always malicious
}

# High-risk permission rule IDs — if ANY of these fire, code+IOC rules count
# at full weight. If none fire, code+IOC rules are dampened (combo-gating).
_HIGH_RISK_PERM_RULE_IDS = {
    "PERM_SMS_INTERCEPTION_COMBO",
    "PERM_ACCESSIBILITY",
    "PERM_OVERLAY",
    "PERM_DROPPER",
    "PERM_DEVICE_ADMIN",
}

# Damping factor applied to code+IOC weights when no high-risk permission
# rule fires. This prevents large feature-rich apps (shopping, social)
# from scoring CRITICAL purely because they use many SDKs with reflection,
# clipboard access, or camera APIs.
_CODE_IOC_DAMPING_FACTOR = 0.30


def score(
    permissions: List[Dict[str, Any]],
    pattern_hits: List[Dict[str, Any]],
    iocs: Dict[str, Any],
    manifest_flags: Dict[str, Any],
    certificate: Dict[str, Any],
    embedded_payloads: Dict[str, Any],
    app_metadata: Dict[str, Any],
    decompiled_available: bool,
) -> Dict[str, Any]:
    """
    Evaluate all rules and compute the risk score.

    **Combo-gated scoring**: Code and IOC signals only count at full weight
    when at least one high-risk permission rule is also triggered. Without
    a dangerous permission anchor, code/IOC signals are dampened to
    _CODE_IOC_DAMPING_FACTOR (30%) — they still appear in the trigger list
    so analysts can see them, but don't inflate the score to CRITICAL for
    large feature-rich apps that use common SDKs.

    Self-sufficient rules (CODE_SMS_ABORT, CODE_FORWARD_SMS, CODE_EXEC)
    always count at full weight regardless — no legitimate app ever
    silently aborts SMS broadcasts or executes shell commands.

    Returns:
        {
            "rule_score": int (0–100),
            "severity": str,
            "triggers": [{rule_id, description, weight, evidence, dampened}],
        }
    """
    _ensure_loaded()

    triggers: List[Dict[str, Any]] = []
    perm_weight = 0
    code_ioc_weight = 0
    metadata_weight = 0

    # ---- Permission rules ------------------------------------------------
    perm_names = {p["name"] for p in (permissions or [])}
    triggered_perm_rule_ids: set = set()

    for rule in _RULES.get("permission_rules", []):
        triggered, evidence = _eval_permission_rule(rule, perm_names, manifest_flags)
        if triggered:
            triggers.append(_make_trigger(rule, evidence))
            perm_weight += rule["weight"]
            triggered_perm_rule_ids.add(rule["id"])

    # Determine whether any HIGH-RISK permission rule fired
    has_high_risk_perm = bool(triggered_perm_rule_ids & _HIGH_RISK_PERM_RULE_IDS)

    # ---- Code rules (from pattern_hits already computed) -----------------
    if decompiled_available:
        code_rule_ids = {r["id"]: r for r in _RULES.get("code_rules", [])}
        for hit in (pattern_hits or []):
            rule_id = hit.get("rule_id")
            if rule_id and rule_id in code_rule_ids:
                raw_weight = hit.get("weight", 0)
                is_self_sufficient = rule_id in _SELF_SUFFICIENT_CODE_RULES
                dampened = not has_high_risk_perm and not is_self_sufficient
                effective_weight = raw_weight if (has_high_risk_perm or is_self_sufficient) else int(raw_weight * _CODE_IOC_DAMPING_FACTOR)
                triggers.append({
                    "rule_id": rule_id,
                    "description": hit.get("description", code_rule_ids[rule_id].get("description", "")),
                    "weight": raw_weight,
                    "effective_weight": effective_weight,
                    "evidence": hit.get("evidence", ""),
                    "dampened": dampened,
                })
                code_ioc_weight += effective_weight
    else:
        logger.info("Decompilation unavailable — code rules skipped")

    # ---- IOC rules -------------------------------------------------------
    all_ioc_text = _flatten_iocs(iocs)
    for rule in _RULES.get("ioc_rules", []):
        triggered, evidence, count = _eval_ioc_rule(rule, all_ioc_text)
        if triggered:
            max_apply = rule.get("max_applications", 1)
            apply_times = min(count, max_apply)
            raw_weight = rule["weight"] * apply_times
            dampened = not has_high_risk_perm
            effective_weight = raw_weight if has_high_risk_perm else int(raw_weight * _CODE_IOC_DAMPING_FACTOR)
            t = _make_trigger(rule, evidence)
            t["effective_weight"] = effective_weight
            t["dampened"] = dampened
            triggers.append(t)
            code_ioc_weight += effective_weight

    # ---- Metadata rules --------------------------------------------------
    for rule in _RULES.get("metadata_rules", []):
        triggered, evidence = _eval_metadata_rule(
            rule, certificate, embedded_payloads, app_metadata
        )
        if triggered:
            t = _make_trigger(rule, evidence)
            t["dampened"] = False
            triggers.append(t)
            metadata_weight += rule["weight"]

    # ---- Final score: perm + code_ioc (combo-gated) + metadata -----------
    total_weight = perm_weight + code_ioc_weight + metadata_weight
    rule_score = min(total_weight, 100)
    severity = _score_to_severity(rule_score)

    logger.info(
        "Rules engine: score=%d severity=%s triggers=%d "
        "(perm=%d code_ioc=%d meta=%d high_risk_perm=%s)",
        rule_score, severity, len(triggers),
        perm_weight, code_ioc_weight, metadata_weight, has_high_risk_perm
    )

    return {
        "rule_score": rule_score,
        "severity": severity,
        "triggers": triggers,
    }


# ---------------------------------------------------------------------------
# Rule evaluators
# ---------------------------------------------------------------------------

def _eval_permission_rule(
    rule: Dict[str, Any],
    perm_names: set,
    manifest_flags: Dict[str, Any],
) -> Tuple[bool, str]:
    required = rule.get("required_permissions", [])
    if required:
        missing = [p for p in required if p not in perm_names]
        if missing:
            return False, ""
        evidence = f"Permissions present: {', '.join(required)}"
        return True, evidence

    if rule.get("required_device_admin") and manifest_flags.get("device_admin"):
        return True, "Device administrator declared in manifest"

    return False, ""


def _eval_ioc_rule(
    rule: Dict[str, Any],
    ioc_text: str,
) -> Tuple[bool, str, int]:
    """Returns (triggered, evidence, match_count)."""
    import re
    try:
        pattern = re.compile(rule["pattern"], re.IGNORECASE)
        matches = list(pattern.finditer(ioc_text))
        if matches:
            sample = matches[0].group(0)[:100]
            return True, f"Matched: {sample}", len(matches)
    except re.error as exc:
        logger.warning("Bad IOC rule regex %s: %s", rule.get("id"), exc)
    return False, "", 0


def _eval_metadata_rule(
    rule: Dict[str, Any],
    certificate: Dict[str, Any],
    embedded_payloads: Dict[str, Any],
    app_metadata: Dict[str, Any],
) -> Tuple[bool, str]:
    condition = rule.get("condition", "")
    rule_id = rule.get("id", "")

    if rule_id == "META_DEBUG_SIGNED":
        if certificate.get("debug_signed"):
            return True, "Certificate: debug-signed"

    elif rule_id == "META_SELF_SIGNED":
        if certificate.get("self_signed"):
            return True, f"Certificate: self-signed (subject: {certificate.get('subject', 'unknown')[:80]})"

    elif rule_id == "META_NESTED_APK":
        if embedded_payloads.get("nested_apk"):
            return True, "Embedded APK found in app assets"

    elif rule_id == "META_NESTED_DEX":
        if embedded_payloads.get("nested_dex"):
            return True, "Embedded DEX file found in app assets"

    elif rule_id == "META_TYPOSQUAT":
        pkg = (app_metadata or {}).get("package_name", "")
        hit = _check_typosquat(pkg)
        if hit:
            return True, f"Package '{pkg}' is within edit-distance 2 of '{hit}'"

    elif rule_id == "META_HEAVY_OBFUSCATION":
        # Heuristic: check if package name contains single-char components
        pkg = (app_metadata or {}).get("package_name", "")
        if _check_obfuscation(pkg):
            return True, f"Package name suggests heavy obfuscation: {pkg}"

    return False, ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_trigger(rule: Dict[str, Any], evidence: str) -> Dict[str, Any]:
    return {
        "rule_id": rule["id"],
        "description": rule.get("description", ""),
        "weight": rule["weight"],
        "evidence": evidence,
    }


def _score_to_severity(score: int) -> str:
    for threshold, label in _SEVERITY_BANDS:
        if score >= threshold:
            return label
    return "SAFE"


def _flatten_iocs(iocs: Optional[Dict[str, Any]]) -> str:
    """Flatten all IOC lists into a single text blob for regex matching."""
    if not iocs:
        return ""
    parts = []
    for key in ("domains", "ips", "urls", "phones", "base64_blobs"):
        parts.extend(iocs.get(key, []))
    return " ".join(str(v) for v in parts)


def _edit_distance(a: str, b: str) -> int:
    """Simple edit distance using difflib ratio as proxy."""
    if a == b:
        return 0
    # Use SequenceMatcher for edit-distance approximation
    ratio = SequenceMatcher(None, a, b).ratio()
    max_len = max(len(a), len(b))
    return round(max_len * (1 - ratio))


def _check_typosquat(package_name: str) -> Optional[str]:
    """Return matching legit package if within edit distance 2, else None."""
    if not package_name or not _LEGIT_PACKAGES:
        return None
    for legit in _LEGIT_PACKAGES:
        if legit == package_name:
            return None  # exact match = not typosquatting
        if _edit_distance(package_name, legit) <= 2:
            return legit
    return None


def _check_obfuscation(package_name: str) -> bool:
    """Heuristic: package with many single-character segments."""
    if not package_name:
        return False
    parts = package_name.split(".")
    if len(parts) < 2:
        return False
    single_char = sum(1 for p in parts if len(p) == 1)
    return (single_char / len(parts)) > 0.5
