"""
pattern_scanner.py — Stage 4: Regex pattern matching over decompiled .java sources.
Runs every code_rule from rules.yaml against the decompiled tree.
Returns pattern_hits[]: list of {rule_id, description, evidence, file, matched_line, weight}.
"""

import logging
import os
import re
from typing import Any, Dict, List

from app.services.decompiler import get_java_files

logger = logging.getLogger(__name__)

# Max bytes per file to scan (skip huge generated files)
_MAX_FILE_BYTES = 2 * 1024 * 1024  # 2 MB
# Max hits per rule (avoid overwhelming output on highly-repeated patterns)
_MAX_HITS_PER_RULE = 5


_FRAMEWORK_EXCLUDES = (
    "androidx/", "android/support/", "kotlin/", "kotlinx/",
    "com/google/android/material/", "org/intellij/", "org/jetbrains/"
)

def scan(scan_id: str, code_rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Scan all decompiled .java files for code_rules patterns.

    Args:
        scan_id:    Scan identifier (to locate decompiled output)
        code_rules: List of rule dicts from rules.yaml (code_rules section)

    Returns:
        List of pattern_hit dicts: {rule_id, description, evidence, file, weight}
    """
    java_files = get_java_files(scan_id)
    if not java_files:
        logger.info("No .java files found for scan %s — skipping pattern scan", scan_id)
        return []

    # Pre-compile all regexes
    compiled_rules = []
    for rule in code_rules:
        try:
            pattern = re.compile(rule["pattern"], re.IGNORECASE | re.DOTALL)
            compiled_rules.append({
                "rule": rule,
                "regex": pattern,
                "hit_count": 0,
            })
        except re.error as exc:
            logger.warning("Invalid regex in rule %s: %s", rule.get("id"), exc)

    hits: List[Dict[str, Any]] = []
    # Track already-seen (rule_id, file) pairs to deduplicate
    seen: Dict[str, int] = {}  # rule_id -> count

    for java_path in java_files:
        norm_path = java_path.replace("\\", "/").lower()
        if any(f"/{ex}" in norm_path or f"\\{ex}" in norm_path or norm_path.startswith(ex) for ex in _FRAMEWORK_EXCLUDES):
            continue

        # Relative path for cleaner evidence strings
        rel_path = _relative_path(java_path).replace("\\", "/")

        # Skip oversized files
        try:
            if os.path.getsize(java_path) > _MAX_FILE_BYTES:
                continue
        except OSError:
            continue

        try:
            with open(java_path, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
        except Exception:
            continue

        # Relative path for cleaner evidence strings
        rel_path = _relative_path(java_path)

        for cr in compiled_rules:
            rule = cr["rule"]
            rule_id = rule["id"]

            if seen.get(rule_id, 0) >= _MAX_HITS_PER_RULE:
                continue

            matches = list(cr["regex"].finditer(source))
            if not matches:
                continue

            # Grab the first match's line for evidence
            first_match = matches[0]
            match_start = first_match.start()
            line_num, line_text = _extract_line(source, match_start)

            hits.append({
                "rule_id": rule_id,
                "description": rule.get("description", ""),
                "evidence": f"{rel_path}:{line_num} — {line_text.strip()[:120]}",
                "file": rel_path,
                "matched_line": line_text.strip()[:200],
                "weight": rule.get("weight", 0),
                "match_count_in_file": len(matches),
            })

            seen[rule_id] = seen.get(rule_id, 0) + 1

    logger.info(
        "Pattern scan for %s: checked %d files, found %d hits across %d rules",
        scan_id, len(java_files), len(hits), len({h["rule_id"] for h in hits})
    )
    return hits


def _extract_line(source: str, pos: int):
    """Return (line_number, line_text) for character position pos in source."""
    before = source[:pos]
    line_num = before.count("\n") + 1
    line_start = before.rfind("\n") + 1
    line_end = source.find("\n", pos)
    if line_end == -1:
        line_end = len(source)
    return line_num, source[line_start:line_end]


def _relative_path(path: str) -> str:
    """Strip long storage prefix for readable evidence strings."""
    parts = path.split(os.sep)
    # Return last 4 path components: sources/com/example/Class.java
    return os.sep.join(parts[-4:]) if len(parts) >= 4 else path
