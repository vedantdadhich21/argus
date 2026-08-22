"""
Report Generator Service (Person B)
Builds comprehensive Markdown threat investigation reports per Reference §10.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class ReportGenerator:
    """Generates structured, presentation-ready Markdown reports for bank SOC analysts."""

    def __init__(self):
        pass

    def get_verdict_badge(self, severity: str) -> str:
        """Returns visual emoji badge for the given severity."""
        sev = (severity or "UNKNOWN").upper()
        if "CRITICAL" in sev:
            return "🔴 CRITICAL"
        elif "HIGH" in sev:
            return "🟠 HIGH"
        elif "MEDIUM" in sev or "LOW" in sev:
            return "🟡 MEDIUM/LOW"
        elif "SAFE" in sev:
            return "🟢 SAFE"
        return "⚪ UNKNOWN"

    def build_markdown_report(
        self,
        app_label: str,
        package_name: str,
        sha256: str,
        md5: Optional[str],
        file_size_bytes: Optional[int],
        final_score: int,
        severity: str,
        fraud_category: str,
        analysis_timestamp: Optional[datetime],
        behavior_summary: Optional[str],
        attack_chain: Optional[List[Dict[str, Any]]],
        triggers: Optional[List[Dict[str, Any]]],
        permissions: Optional[List[Dict[str, Any]]],
        iocs: Optional[Dict[str, Any]],
        mitre_techniques: Optional[List[Dict[str, Any]]],
        recommendations: Optional[List[str]],
    ) -> str:
        """Assembles and formats the complete Markdown investigation report."""
        timestamp_str = (
            analysis_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
            if analysis_timestamp
            else datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        )
        verdict_badge = self.get_verdict_badge(severity)
        app_title = app_label or package_name or "Android Application"
        size_kb = f"{file_size_bytes / 1024:.1f} KB" if file_size_bytes else "Unknown"

        md_lines = []

        # Header
        md_lines.append(f"# Threat Investigation Report — {app_title}")
        md_lines.append(
            f"**Verdict:** {verdict_badge} ({final_score}/100) · `{fraud_category or 'unclassified'}` · **Analyzed:** {timestamp_str}\n"
        )
        md_lines.append(
            f"- **Package Name:** `{package_name or 'unknown'}`\n"
            f"- **SHA-256:** `{sha256 or 'N/A'}`\n"
            f"- **MD5:** `{md5 or 'N/A'}`\n"
            f"- **File Size:** {size_kb}\n"
        )
        md_lines.append("---")

        # Executive Summary
        md_lines.append("\n## Executive Summary\n")
        if behavior_summary and behavior_summary.strip():
            md_lines.append(behavior_summary.strip())
        else:
            md_lines.append(
                f"Automated static and behavioral rule analysis identified risk indicators in `{package_name}`. "
                f"The application has been assessed with a threat score of **{final_score}/100** ({severity})."
            )

        # Attack Chain
        md_lines.append("\n## Attack Chain Reconstruction\n")
        if attack_chain and len(attack_chain) > 0:
            for item in attack_chain:
                step_idx = item.get("step", 1)
                title = item.get("title", "Attack Step")
                detail = item.get("detail", "")
                evidence = item.get("evidence", [])
                evidence_str = (
                    f" *(Evidence: `{', '.join(evidence)}`)*" if evidence else ""
                )
                md_lines.append(f"{step_idx}. **{title}** — {detail}{evidence_str}")
        else:
            md_lines.append(
                "> *No sequential attack chain generated. Refer to the static trigger breakdown below.*"
            )

        # Risk Score Breakdown
        md_lines.append("\n## Risk Score Breakdown\n")
        md_lines.append("| Triggered Rule | Description / Evidence | Points |")
        md_lines.append("|---|---|---|")
        if triggers and len(triggers) > 0:
            for t in triggers:
                rule_id = t.get("rule_id") or t.get("id", "RULE")
                desc = t.get("description") or t.get("evidence") or "Static rule match"
                pts = t.get("weight") or t.get("points", 0)
                md_lines.append(f"| `{rule_id}` | {desc} | +{pts} |")
        else:
            md_lines.append("| `BASELINE_SAFE` | No hostile static signatures or permissions triggered | 0 |")

        # Permissions Requested
        md_lines.append("\n## Permissions Requested\n")
        if permissions and len(permissions) > 0:
            md_lines.append("| Permission | Danger Level | Description |")
            md_lines.append("|---|---|---|")
            for p in permissions:
                if isinstance(p, dict):
                    name = p.get("name", "")
                    danger = p.get("danger_level", "NORMAL").upper()
                    desc = p.get("description", "Declared by manifest")
                else:
                    name = str(p)
                    danger = (
                        "HIGH"
                        if any(
                            k in name
                            for k in [
                                "SMS",
                                "ACCESSIBILITY",
                                "ALERT_WINDOW",
                                "INSTALL_PACKAGES",
                                "ADMIN",
                            ]
                        )
                        else "NORMAL"
                    )
                    desc = "Android Manifest permission"
                flag = "⚠️ HIGH" if danger in ["HIGH", "DANGEROUS"] else "ℹ️ NORMAL"
                md_lines.append(f"| `{name}` | {flag} | {desc} |")
        else:
            md_lines.append("*No special permissions requested.*")

        # Indicators of Compromise (IOCs)
        md_lines.append("\n## Indicators of Compromise (IOCs)\n")
        has_iocs = False
        if iocs:
            if isinstance(iocs, dict):
                domains = iocs.get("domains", [])
                ips = iocs.get("ips", [])
                urls = iocs.get("urls", [])
                phones = iocs.get("phone_numbers", [])
            else:
                domains = getattr(iocs, "domains", [])
                ips = getattr(iocs, "ips", [])
                urls = getattr(iocs, "urls", [])
                phones = getattr(iocs, "phone_numbers", [])

            if domains or ips or urls or phones:
                has_iocs = True
                if domains:
                    md_lines.append("### C2 Domains\n" + "\n".join(f"- `{d}`" for d in domains))
                if ips:
                    md_lines.append("### C2 IP Addresses\n" + "\n".join(f"- `{ip}`" for ip in ips))
                if urls:
                    md_lines.append("### Network Endpoints / URLs\n" + "\n".join(f"- `{u}`" for u in urls))
                if phones:
                    md_lines.append("### Destination Phone Numbers\n" + "\n".join(f"- `{ph}`" for ph in phones))

        if not has_iocs:
            md_lines.append("*No external network IOCs identified.*")

        # MITRE ATT&CK Mobile Mapping
        md_lines.append("\n## MITRE ATT&CK Mobile Techniques\n")
        if mitre_techniques and len(mitre_techniques) > 0:
            md_lines.append("| ID | Technique Name | Evidence / Reason |")
            md_lines.append("|---|---|---|")
            for m in mitre_techniques:
                if isinstance(m, dict):
                    m_id = m.get("id", "T-UNK")
                    m_name = m.get("name", "Unknown Technique")
                    m_reason = m.get("reason", "")
                else:
                    m_id = getattr(m, "id", "T-UNK")
                    m_name = getattr(m, "name", "Unknown Technique")
                    m_reason = getattr(m, "reason", "")
                md_lines.append(f"| **{m_id}** | {m_name} | {m_reason} |")
        else:
            md_lines.append("*No MITRE ATT&CK Mobile techniques correlated.*")

        # Recommended Actions
        md_lines.append("\n## Recommended Incident Response & Mitigation Actions\n")
        if recommendations and len(recommendations) > 0:
            for rec in recommendations:
                md_lines.append(f"- [ ] {rec}")
        else:
            md_lines.append("- [ ] Block the SHA-256 hash at enterprise perimeter email and SMS gateways.")
            md_lines.append("- [ ] Correlate inbound authentication attempts from devices matching these IOCs.")

        md_lines.append("\n---\n*Report generated automatically by Argus Threat Intelligence Engine.*")
        return "\n".join(md_lines)

    def save_report(self, scan_id: str, markdown_content: str, output_dir: str = "storage/reports") -> str:
        """Saves the generated markdown report to disk and returns the filepath."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        report_file = out_path / f"{scan_id}_report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        return str(report_file)

    def generate_pdf(self, markdown_content: str) -> bytes:
        """Converts generated Markdown report into a clean, presentation-ready PDF document."""
        import io
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=8,
        )
        h2_style = ParagraphStyle(
            'ReportH2',
            parent=styles['Heading2'],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=12,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['BodyText'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155'),
            spaceAfter=4,
        )
        bullet_style = ParagraphStyle(
            'ReportBullet',
            parent=styles['BodyText'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155'),
            leftIndent=15,
            spaceAfter=3,
        )

        story = []
        lines = markdown_content.split('\n')
        in_table = False
        table_rows = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if in_table and table_rows:
                    # Render table
                    t = Table(table_rows, hAlign='LEFT')
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 8))
                    table_rows = []
                    in_table = False
                continue

            if stripped.startswith('|') and stripped.endswith('|'):
                in_table = True
                cols = [c.strip() for c in stripped.strip('|').split('|')]
                if not all(set(c).issubset({'-', ':', ' '}) for c in cols):
                    table_rows.append([Paragraph(c, body_style) for c in cols])
                continue
            elif in_table:
                if table_rows:
                    t = Table(table_rows, hAlign='LEFT')
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 8))
                table_rows = []
                in_table = False

            if stripped.startswith('# '):
                story.append(Paragraph(stripped[2:], title_style))
                story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#dc2626'), spaceAfter=10))
            elif stripped.startswith('## '):
                story.append(Paragraph(stripped[3:], h2_style))
            elif stripped.startswith('### '):
                story.append(Paragraph(stripped[4:], h2_style))
            elif stripped.startswith('- ') or stripped.startswith('* '):
                story.append(Paragraph("• " + stripped[2:], bullet_style))
            elif stripped.startswith('---'):
                story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceAfter=8))
            else:
                story.append(Paragraph(stripped, body_style))

        if in_table and table_rows:
            t = Table(table_rows, hAlign='LEFT')
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ]))
            story.append(t)

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Report Generator.")
    parser.add_argument("--input", default=None, help="Optional JSON file with scan findings")
    args = parser.parse_args()

    generator = ReportGenerator()

    # Sample demo data matching fake_banker
    report_md = generator.build_markdown_report(
        app_label="PhotoVault (Fake Banker)",
        package_name="com.bank.security.update",
        sha256="8f4b1e5c2d9a3b7e6f1a8c4d2e9b3a7f5e1c8d4b2a9e3f7c1d5a8b4e2f9c3a7",
        md5="d41d8cd98f00b204e9800998ecf8427e",
        file_size_bytes=3428900,
        final_score=87,
        severity="CRITICAL",
        fraud_category="sms_otp_stealer",
        analysis_timestamp=datetime.now(timezone.utc),
        behavior_summary="The application disguises itself as a photo gallery utility while executing aggressive banking trojan behaviors. It registers high-priority broadcast listeners to intercept transactional SMS OTPs, deletes inbound banking alerts to keep the victim unaware, and dynamic-loads an encrypted secondary DEX payload from assets.",
        attack_chain=[
            {
                "step": 1,
                "title": "Delivery & Persistence",
                "detail": "App requests boot receiver and overlay permissions to persist across restarts.",
                "evidence": ["AndroidManifest.xml", "RECEIVE_BOOT_COMPLETED"],
            },
            {
                "step": 2,
                "title": "Dynamic Payload Decryption",
                "detail": "PayloadLoader loads and executes secondary classes.dex from assets using DexClassLoader.",
                "evidence": ["PayloadLoader.loadAndExecute", "DexClassLoader"],
            },
            {
                "step": 3,
                "title": "SMS OTP Interception & Suppression",
                "detail": "Intercepts incoming SMS messages, executes abortBroadcast() to hide banking OTPs, and exfiltrates stolen codes to C2 server.",
                "evidence": ["SmsReceiver.onReceive", "abortBroadcast()", "http://185.220.101.5/collect/sms"],
            },
        ],
        triggers=[
            {"rule_id": "PERM_SMS_INTERCEPTION_COMBO", "description": "READ_SMS + RECEIVE_SMS + SEND_SMS combo", "weight": 30},
            {"rule_id": "CODE_SMS_ABORT", "description": "abortBroadcast() suppresses SMS notification", "weight": 22},
            {"rule_id": "CODE_DYNAMIC_LOADING", "description": "DexClassLoader dynamically loads dex file", "weight": 18},
            {"rule_id": "IOC_RAW_IP_URL", "description": "Communicates with bare IP C2 http://185.220.101.5", "weight": 10},
            {"rule_id": "PERM_OVERLAY", "description": "SYSTEM_ALERT_WINDOW draw-over-apps permission", "weight": 12},
        ],
        permissions=[
            {"name": "android.permission.RECEIVE_SMS", "danger_level": "DANGEROUS", "description": "Allows receiving SMS"},
            {"name": "android.permission.READ_SMS", "danger_level": "DANGEROUS", "description": "Allows reading SMS"},
            {"name": "android.permission.SEND_SMS", "danger_level": "DANGEROUS", "description": "Allows sending SMS"},
            {"name": "android.permission.SYSTEM_ALERT_WINDOW", "danger_level": "HIGH", "description": "Draw over other apps"},
            {"name": "android.permission.INTERNET", "danger_level": "NORMAL", "description": "Full network access"},
        ],
        iocs={
            "domains": ["test-c2bank.info"],
            "ips": ["185.220.101.5"],
            "urls": ["http://185.220.101.5/collect/sms"],
            "phone_numbers": [],
        },
        mitre_techniques=[
            {"id": "T1412", "name": "SMS Interception / Theft", "reason": "Silently drops and forwards OTP SMS to C2."},
            {"id": "T1407", "name": "Dynamic Code Loading", "reason": "Uses DexClassLoader to load secondary payload."},
            {"id": "T1437", "name": "Application Layer Protocol", "reason": "Exfiltrates stolen credentials to C2 IP."},
            {"id": "T1444", "name": "Masquerading / Phishing Overlay", "reason": "Draws overlays to harvest bank credentials."},
        ],
        recommendations=[
            "Block SHA-256 hash at enterprise mobile security gateway.",
            "Blacklist C2 IP 185.220.101.5 at corporate and ISP threat intel feeds.",
            "Notify affected customers with active sessions on compromised devices.",
            "Enforce hardware security keys or in-app push approvals over SMS OTPs.",
        ],
    )

    out_file = generator.save_report("sample_demo_scan", report_md)
    print(f"\n[+] Generated sample investigation report at: {out_file}")
    print("\n--- Report Preview ---")
    safe_preview = report_md[:800].encode("ascii", "replace").decode("ascii")
    print(safe_preview + "\n\n... [remaining sections truncated for preview] ...")

