"""
Method Selector Service (Person B)
Selects and ranks top suspicious decompiled Java methods for LLM behavioral analysis.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Suspicious code and IOC patterns based on Reference §7 rules.yaml
DEFAULT_SUSPICIOUS_PATTERNS: List[Dict[str, any]] = [
    {
        "id": "CODE_SMS_ABORT",
        "pattern": r"abortBroadcast\s*\(",
        "weight": 25,
        "description": "Silently drops incoming SMS/OTP notifications",
    },
    {
        "id": "CODE_DYNAMIC_LOADING",
        "pattern": r"(DexClassLoader|PathClassLoader)\s*\(",
        "weight": 20,
        "description": "Loads external executable code dynamically at runtime",
    },
    {
        "id": "CODE_STRING_DECRYPTION",
        "pattern": r"(Cipher\.getInstance|javax\.crypto).{0,200}(Base64|decrypt|SecretKeySpec|IvParameterSpec)",
        "weight": 15,
        "description": "Cryptographic routine / runtime payload decryption",
    },
    {
        "id": "CODE_OVERLAY",
        "pattern": r"(TYPE_APPLICATION_OVERLAY|TYPE_SYSTEM_ALERT|WindowManager\.LayoutParams)",
        "weight": 15,
        "description": "Draw-over-apps phishing overlay manipulation",
    },
    {
        "id": "CODE_ACCESSIBILITY_SCRAPING",
        "pattern": r"(AccessibilityService|AccessibilityNodeInfo|getRootInActiveWindow|TYPE_VIEW_TEXT_CHANGED)",
        "weight": 18,
        "description": "Accessibility service credential / screen text scraping",
    },
    {
        "id": "CODE_CONTACT_ENUM",
        "pattern": r"content://com\.android\.contacts",
        "weight": 10,
        "description": "Harvets user contacts from device content provider",
    },
    {
        "id": "CODE_REFLECTION",
        "pattern": r"(Class\.forName|Method\.invoke|getDeclaredMethod)",
        "weight": 10,
        "description": "Reflection to invoke hidden or restricted APIs",
    },
    {
        "id": "CODE_EXEC",
        "pattern": r"Runtime\.getRuntime\(\)\.exec|ProcessBuilder",
        "weight": 12,
        "description": "Executes shell commands or binaries",
    },
    {
        "id": "CODE_DEVICE_ID_HARVEST",
        "pattern": r"(getDeviceId|getImei|getSubscriberId|getSimSerialNumber)\s*\(",
        "weight": 8,
        "description": "Harvests hardware identifiers",
    },
    {
        "id": "IOC_RAW_IP",
        "pattern": r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?",
        "weight": 12,
        "description": "Communicates with bare IP (C2 infrastructure)",
    },
]


@dataclass
class Method:
    file_path: str
    class_name: str
    name: str
    signature: str
    code: str
    score: int = 0
    matched_rules: List[str] = field(default_factory=list)

    def to_formatted_block(self, max_chars: int = 3000) -> str:
        """Formats the method block for LLM prompt context."""
        code_body = self.code
        if len(code_body) > max_chars:
            code_body = code_body[:max_chars] + "\n        // ... [truncated for length]"

        header = f"// File: {self.file_path}\n// Class: {self.class_name} | Method: {self.signature}\n// Matched suspicious rules: {', '.join(self.matched_rules) if self.matched_rules else 'None'}"
        return f"{header}\n{code_body}\n"


class MethodSelector:
    """Parses Java files, extracts methods, and ranks them by suspicion score."""

    def __init__(
        self,
        patterns: Optional[List[Dict[str, any]]] = None,
        max_methods: int = 10,
        max_chars_per_method: int = 3000,
    ):
        self.patterns = patterns or DEFAULT_SUSPICIOUS_PATTERNS
        self.max_methods = max_methods
        self.max_chars_per_method = max_chars_per_method
        # Compile regexes
        self._compiled_patterns = [
            (p["id"], p["weight"], p["description"], re.compile(p["pattern"], re.IGNORECASE | re.DOTALL))
            for p in self.patterns
        ]

    def extract_methods_from_java(self, file_path: str, content: str) -> List[Method]:
        """Extracts individual method declarations and bodies from a Java source string."""
        methods: List[Method] = []

        # Find package and class name
        pkg_match = re.search(r"package\s+([\w\.]+);", content)
        pkg = pkg_match.group(1) if pkg_match else ""

        class_match = re.search(r"(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:final\s+)?class\s+(\w+)", content)
        class_name = class_match.group(1) if class_match else Path(file_path).stem
        if pkg:
            class_name = f"{pkg}.{class_name}"

        # Method signature matcher: matches typical Java method signatures
        method_sig_pattern = re.compile(
            r"((?:public|private|protected|static|final|synchronized|abstract|native|default)\s+)+"
            r"([\w<>\[\],\s]+?)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[\w\s,]+)?\s*\{",
            re.MULTILINE,
        )

        for match in method_sig_pattern.finditer(content):
            method_name = match.group(3)
            return_type = match.group(2).strip()
            params = match.group(4).strip()
            signature = f"{return_type} {method_name}({params})"

            start_brace_idx = match.end() - 1
            # Extract method body matching balanced curly braces
            brace_count = 1
            idx = start_brace_idx + 1
            n = len(content)

            while idx < n and brace_count > 0:
                char = content[idx]
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                elif char in ('"', "'"):
                    # Skip string and char literals
                    quote = char
                    idx += 1
                    while idx < n and content[idx] != quote:
                        if content[idx] == "\\" and idx + 1 < n:
                            idx += 2
                        else:
                            idx += 1
                elif char == "/" and idx + 1 < n:
                    if content[idx + 1] == "/":
                        # Skip line comment
                        idx = content.find("\n", idx)
                        if idx == -1:
                            break
                    elif content[idx + 1] == "*":
                        # Skip block comment
                        end_comment = content.find("*/", idx + 2)
                        if end_comment == -1:
                            break
                        idx = end_comment + 1
                idx += 1

            if brace_count == 0:
                full_method_code = content[match.start() : idx].strip()
            else:
                full_method_code = content[match.start() : min(match.start() + self.max_chars_per_method, n)].strip()

            methods.append(
                Method(
                    file_path=file_path,
                    class_name=class_name,
                    name=method_name,
                    signature=signature,
                    code=full_method_code,
                )
            )

        # Fallback: if no structured methods were parsed (e.g. static block or script), treat whole file as a block
        if not methods and content.strip():
            methods.append(
                Method(
                    file_path=file_path,
                    class_name=class_name,
                    name="main_or_file_body",
                    signature="void whole_file()",
                    code=content[: self.max_chars_per_method * 2],
                )
            )

        return methods

    def score_method(self, method: Method) -> int:
        """Calculates a suspicion score for a method based on matched rules."""
        total_score = 0
        matched = []

        for rule_id, weight, desc, regex in self._compiled_patterns:
            if regex.search(method.code):
                total_score += weight
                matched.append(rule_id)

        method.score = total_score
        method.matched_rules = matched
        return total_score

    def select_top_methods_from_directory(self, base_dir: str) -> List[Method]:
        """Scans a decompiled directory, extracts all methods, and returns the top suspicious ones."""
        all_methods: List[Method] = []
        base_path = Path(base_dir)

        if not base_path.exists():
            return []

        framework_excludes = ("androidx/", "android/support/", "kotlin/", "kotlinx/", "com/google/android/material/")
        for root, _, files in os.walk(base_path):
            for file in files:
                if file.endswith(".java") or file.endswith(".smali") or file.endswith(".kt"):
                    abs_file = os.path.join(root, file)
                    rel_file = os.path.relpath(abs_file, base_dir).replace("\\", "/")
                    if any(rel_file.startswith(ex) or f"/{ex}" in rel_file for ex in framework_excludes):
                        continue
                    try:
                        with open(abs_file, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        file_methods = self.extract_methods_from_java(rel_file, content)
                        for m in file_methods:
                            self.score_method(m)
                            all_methods.append(m)
                    except Exception:
                        continue

        # Sort methods by score descending
        all_methods.sort(key=lambda m: m.score, reverse=True)

        # Return top N methods
        top_methods = all_methods[: self.max_methods]
        return top_methods


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Extract and score suspicious decompiled methods.")
    parser.add_argument("--dir", default="fixtures/decompiled_sample", help="Directory with decompiled code")
    args = parser.parse_args()

    selector = MethodSelector()
    methods = selector.select_top_methods_from_directory(args.dir)

    print(f"\n[MethodSelector] Found {len(methods)} top suspicious methods in {args.dir}:")
    for i, m in enumerate(methods, 1):
        print(f"\n--- Method #{i} (Score: {m.score}) ---")
        print(f"File: {m.file_path} | Class: {m.class_name} | Method: {m.name}")
        print(f"Rules: {', '.join(m.matched_rules)}")
        print(m.to_formatted_block(max_chars=300))
