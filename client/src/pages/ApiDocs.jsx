import { Copy } from 'lucide-react'
import { useState } from 'react'

function CodeBlock({ code }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <div className="relative">
      <pre className="rounded-xl border border-white/5 bg-black/40 p-4 text-xs text-green-300 overflow-x-auto font-mono leading-relaxed">{code}</pre>
      <button onClick={copy}
        className="absolute top-3 right-3 flex items-center gap-1 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-400 hover:text-white transition-colors">
        <Copy className="h-3 w-3" />
        {copied ? 'Copied!' : 'Copy'}
      </button>
    </div>
  )
}

function Section({ title, desc, children }) {
  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-6">
      <h3 className="text-base font-bold text-white mb-1">{title}</h3>
      <p className="text-sm text-slate-400 mb-4">{desc}</p>
      {children}
    </div>
  )
}

const BASE = 'http://localhost:8000'

export default function ApiDocs() {
  return (
    <div className="min-h-screen bg-slate-950 pt-20">
      <div className="mx-auto max-w-4xl px-6 py-10">
        <div className="mb-10">
          <h1 className="text-2xl font-bold text-white">API Reference</h1>
          <p className="text-sm text-slate-400 mt-1">
            Bank-gateway integration ready. Base URL: <code className="text-red-400">{BASE}</code> · No auth required.
          </p>
        </div>

        <div className="flex flex-col gap-6">
          <Section title="POST /api/scan" desc="Upload an APK and start the analysis pipeline. Returns a scan_id immediately; poll GET /api/scan/{id} for results.">
            <CodeBlock code={`# Upload APK for analysis
curl -X POST ${BASE}/api/scan \\
  -F "file=@suspicious.apk"

# Response 202
{ "scan_id": "9f1c4e2a8b3d7f0c5e6a1b4d2c8f9e3a" }

# Errors: 413 (too large) · 415 (not an APK) · 429 (server busy)`} />
          </Section>

          <Section title="POST /api/lookup/hash" desc="Fast-path used by mobile clients. Hash the APK on-device, query before uploading. If known: instant verdict. If unknown: proceed to upload.">
            <CodeBlock code={`# Hash lookup (instant cached verdict)
curl -X POST ${BASE}/api/lookup/hash \\
  -H "Content-Type: application/json" \\
  -d '{"sha256": "a3f5c8e2...", "md5": "7a3f9c1e..."}'

# Known APK response
{ "known": true, "scan_id": "9f1c...", "severity": "CRITICAL", "final_score": 87, "fraud_category": "sms_otp_stealer" }

# Unknown APK response
{ "known": false }`} />
          </Section>

          <Section title="GET /api/scan/{id}" desc="Poll this endpoint every 2 seconds until status === 'completed'. Returns full report when done.">
            <CodeBlock code={`# Poll scan status
curl ${BASE}/api/scan/9f1c4e2a8b3d7f0c5e6a1b4d2c8f9e3a

# In-progress response
{ "scan_id": "9f1c...", "status": "decompiling", "progress_hint": "Decompiling bytecode (stage 3/8)" }

# Completed response (abridged)
{
  "status": "completed",
  "final_score": 87,
  "severity": "CRITICAL",
  "fraud_category": "banking_trojan",
  "ai_status": "ok",
  "permissions": [...],
  "triggers": [...],
  "ai_analysis": { "attack_chain": [...], "mitre_techniques": [...] },
  "report_markdown": "# Threat Report..."
}`} />
          </Section>

          <Section title="GET /api/scan/{id}/report?format=md" desc="Download the full investigation report as a Markdown file.">
            <CodeBlock code={`curl -o report.md "${BASE}/api/scan/9f1c4e2a8b3d7f0c5e6a1b4d2c8f9e3a/report?format=md"`} />
          </Section>

          <Section title="GET /api/scans" desc="Paginated history list for the analyst dashboard.">
            <CodeBlock code={`curl "${BASE}/api/scans?page=1&limit=20"

# Response
{ "scans": [{ "scan_id": "...", "original_filename": "...", "severity": "CRITICAL", ... }], "total": 142 }`} />
          </Section>

          <Section title="GET /api/stats" desc="Dashboard hero strip stats.">
            <CodeBlock code={`curl ${BASE}/api/stats

{ "total_scans": 142, "malicious_found": 38, "avg_duration_ms": 28400, "unique_hashes": 139 }`} />
          </Section>

          {/* Integration pitch */}
          <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-6">
            <h3 className="text-base font-bold text-white mb-2">🏦 Gateway Integration Pattern</h3>
            <p className="text-sm text-slate-400 mb-4">
              The pair <code className="text-red-400">POST /api/lookup/hash</code> + <code className="text-red-400">POST /api/scan</code> is the complete bank-gateway integration story.
              Hash check is instant (milliseconds). Full scan completes in under 40 seconds.
            </p>
            <CodeBlock code={`# Step 1: Hash the APK (on-device or server-side)
sha256=$(sha256sum suspicious.apk | awk '{print $1}')

# Step 2: Instant cache check
result=$(curl -s -X POST ${BASE}/api/lookup/hash -H "Content-Type: application/json" \\
  -d "{\\\"sha256\\\": \\\"$sha256\\\"}")

if echo $result | grep -q '"known": true'; then
  echo "Known threat: $(echo $result | jq .severity)"
else
  # Step 3: Full analysis
  scan_id=$(curl -s -X POST ${BASE}/api/scan -F "file=@suspicious.apk" | jq -r .scan_id)
  # Poll until completed...
  curl ${BASE}/api/scan/$scan_id
fi`} />
          </div>
        </div>
      </div>
    </div>
  )
}
