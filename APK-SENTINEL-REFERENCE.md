# APK Sentinel — Full Project Reference (SW-07)

> Use this document to understand, build, or extend APK Sentinel. It covers the full architecture, feature set, folder structure, data models, API contracts, detection rules, LLM integration contracts, and implementation instructions. Feed this to any AI agent or new teammate to get accurate, context-aware help without re-scanning the codebase.

**Problem statement:** SW-07 — Generative AI-Based Automated Analysis and Risk Scoring of Fraudulent APKs (for bank fraud prevention).

---

## 1. Project Overview

APK Sentinel is an **automated fraud-APK analysis platform** with two surfaces powered by one analysis engine:

1. **Analyst Dashboard (Web)** — Bank SOC analysts upload a suspicious APK and get a full AI-generated investigation report: risk score, attack chain, IOCs, MITRE mapping, recommendations.
2. **Phone Shield (Android)** — End users who tap a malicious APK (from WhatsApp/SMS/email) get intercepted before install: our scanner app hashes the file, queries the engine, and shows a RED/YELLOW/GREEN verdict in seconds. Safe apps are handed off to the normal installer.

**One-line pitch:** *"Intelligence at the core, protection at the edge — one engine protecting both the bank analyst and the end customer."*

### Core Features (final scope)

- APK upload via web dashboard (drag-drop) or intercepted on-phone
- SHA-256 hash cache → instant verdict for previously seen files
- Static analysis engine: manifest, permissions, components, certificates, strings, embedded payloads
- Decompiled-code scanning: suspicious API call detection via pattern matching on jadx output
- **AI code behavioral analysis**: top suspicious decompiled methods are sent to an LLM which reconstructs the fraud attack chain in plain English and returns structured JSON
- Explainable weighted risk scoring (0–100, CRITICAL/HIGH/MEDIUM/LOW/SAFE) — every point traceable to a triggered rule
- IOC extraction (domains, IPs, URLs, phone numbers, package names)
- MITRE ATT&CK Mobile technique mapping
- Auto-generated investigation report (markdown + PDF export)
- Analyst dashboard: risk gauge, findings tables, AI annotations, scan history, PDF export
- Android scanner app: intercept APK-open intents → hash/upload → verdict screen → safe handoff to installer
- One public REST endpoint = "bank gateway integration ready"

---

## 2. Tech Stack

### Backend (`/server`) — Python

| Purpose | Library/Tool |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI + Uvicorn |
| Static APK parsing | Androguard |
| Decompilation | jadx (called via subprocess; binary must be on PATH or set in env) |
| Regex/pattern scanning | Python `re` over decompiled `.java` sources |
| Database | SQLite (via SQLAlchemy 2.0) — zero-setup, fine for hackathon scale |
| Validation | Pydantic v2 (comes with FastAPI) |
| LLM | Any OpenAI-compatible API (OpenAI / Groq / OpenRouter / Ollama) — base URL + key from env |
| PDF report | `markdown2` + `pdfkit` fallback: render markdown, export `.md`; PDF is stretch |
| File uploads | FastAPI `UploadFile`, saved to local `storage/apks/` |
| Async jobs | FastAPI `BackgroundTasks` (NOT Celery — overkill for 24h) |
| Isolation | Docker container for the whole backend (never analyze samples on host OS) |

### Dashboard Frontend (`/client`) — React

| Purpose | Library/Tool |
|---|---|
| Build tool | Vite |
| UI Framework | React 18 |
| Routing | React Router v6 |
| Server State | TanStack Query v5 (with polling while scan runs) |
| Styling | Tailwind CSS + shadcn/ui |
| Charts | Recharts (risk gauge can be a custom SVG too) |
| HTTP Client | Axios |
| Deployment | Vercel |

### Android App (`/android`) — Kotlin

| Purpose | Tool |
|---|---|
| Language | Kotlin, single-Activity (Jetpack Compose optional — plain XML Views is faster for 24h) |
| Min SDK | 26 |
| Key APIs | `ContentResolver` (read APK from intent Uri), `MessageDigest` (SHA-256), Retrofit or OkHttp (backend calls), `PackageInstaller` handoff |
| Distribution | Sideloaded APK during demo (not Play Store) |

---

## 3. Architecture Overview

```
┌──────────────────────────┐        ┌─────────────────────────────┐
│   React Dashboard        │        │   Android Scanner App       │
│   (analysts)             │        │   (end users)               │
│                          │        │                             │
│  Upload APK (multipart)  │        │  Intercept APK-open intent  │
│  Poll scan status        │        │  SHA-256 → hash lookup      │
│  View report/export PDF  │        │  Upload unknown APKs        │
└────────────┬─────────────┘        │  Show R/Y/G verdict screen  │
             │                      └──────────────┬──────────────┘
             │            REST (JSON)               │
             └──────────────┬───────────────────────┘
                            ▼
              ┌──────────────────────────────┐
              │      FastAPI Backend          │
              │      (runs in Docker)         │
              │                              │
              │  POST /api/scan              │
              │  GET  /api/scan/{id}         │
              │  POST /api/lookup/hash       │
              │  ...                         │
              │                              │
              │  BackgroundTask = pipeline:  │
              │   1. dedupe/hash             │
              │   2. static_analysis.py      │
              │   3. decompiler.py (jadx)    │
              │   4. ioc_extractor.py        │
              │   5. rules_engine.py         │
              │   6. ai_analyst.py (LLM)     │
              │   7. merge scores            │
              │   8. report_generator.py     │
              └───────┬──────────────┬───────┘
                      ▼              ▼
              ┌────────────┐   ┌──────────────────┐
              │  SQLite DB  │   │  LLM API         │
              │  (scans)    │   │  (OpenAI-compat) │
              └────────────┘   └──────────────────┘
```

### Key Design Decisions

- **All analysis happens server-side.** The Android app contains ZERO analysis logic — it is only: intercept → hash → upload → render. This keeps the phone app tiny (~1 person-day of work).
- **Pipeline stages update a `status` field in the DB.** Clients poll `GET /api/scan/{id}` every 2s until `status === "completed"` (or `"failed"`). Live stage display in the UI is a cheap, impressive demo touch.
- **Rules engine runs BEFORE the LLM.** If the rule score already says CRITICAL, we still run the LLM (for narrative/reporting) but a crash/timeout in the LLM must never produce "no verdict" — the rule-based score always exists as floor.
- **LLM failure tolerance:** if no API key or the call fails, the scan completes with `ai_analysis: null` and a flag `ai_status: "unavailable"`. Verdict still ships from rules alone.
- **Terminology warning:** do NOT call the LLM layer "dynamic analysis" (that means running the app in an emulator). Brand it **"AI-powered code behavioral analysis."**

---

## 4. Folder Structure

```
apk-sentinel/
├── server/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app factory, CORS, routes mount
│   │   ├── config.py                # Reads .env via pydantic-settings
│   │   ├── database.py              # SQLAlchemy engine + session (SQLite)
│   │   ├── models.py                # ORM model: Scan
│   │   ├── schemas.py               # Pydantic response/request schemas
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── scans.py             # All /api/* endpoints
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── storage.py           # Save uploaded APK, path mgmt, size limit
│   │   │   ├── static_analysis.py   # Androguard: manifest, perms, components, cert
│   │   │   ├── decompiler.py        # jadx subprocess wrapper + timeout
│   │   │   ├── pattern_scanner.py   # Suspicious-API regex patterns over .java files
│   │   │   ├── ioc_extractor.py     # Regex: URLs, IPs, phones, base64 blobs, secrets
│   │   │   ├── method_selector.py   # Rank decompiled methods by suspicion → top N
│   │   │   ├── ai_analyst.py        # THE GenAI layer: LLM prompt + JSON parsing
│   │   │   ├── rules_engine.py      # Weighted scoring, loads rules.yaml
│   │   │   ├── report_generator.py  # Markdown report builder (+PDF stretch)
│   │   │   └── pipeline.py          # Orchestrates 1→8, updates Scan.status
│   │   └── data/
│   │       ├── rules.yaml           # ALL rule weights live here (edit freely)
│   │       └── legit_banking_packages.json   # For typosquat detection
│   ├── storage/
│   │   ├── apks/                    # Uploaded samples (gitignored)
│   │   ├── decompiled/              # jadx output (gitignored)
│   │   └── reports/                 # Generated reports (gitignored)
│   ├── tests/
│   │   └── test_pipeline.py         # Runs full pipeline against samples/samples_info.json
│   ├── samples/                     # Demo APKs (see §16 — NEVER install these)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env
├── client/
│   ├── src/
│   │   ├── api/
│   │   │   └── axios.js             # baseURL = VITE_API_BASE
│   │   ├── components/
│   │   │   ├── ui/                  # shadcn/ui generated (button, card, badge, tabs, dialog...)
│   │   │   ├── upload/
│   │   │   │   └── Dropzone.jsx     # Drag-drop upload, calls POST /api/scan
│   │   │   ├── scan/
│   │   │   │   ├── RiskGauge.jsx        # SVG semicircle gauge 0-100 + severity color
│   │   │   │   ├── PipelineStatus.jsx   # Shows live stage ticks during scan
│   │   │   │   ├── VerdictCard.jsx      # Big verdict banner (CRITICAL etc.)
│   │   │   │   ├── ScoreBreakdown.jsx   # "Why this score" — rule contributions table
│   │   │   │   ├── PermissionTable.jsx  # Permissions + risk flags
│   │   │   │   ├── AttackChain.jsx      # Numbered steps from LLM output
│   │   │   │   ├── IocTable.jsx         # Domains/IPs/URLs/phones, click-to-copy
│   │   │   │   ├── AiFindings.jsx       # Behavior summary + inline code annotations
│   │   │   │   └── MitreList.jsx        # MITRE technique chips
│   │   │   └── shared/
│   │   │       ├── Navbar.jsx
│   │   │       └── SeverityBadge.jsx
│   │   ├── pages/
│   │   │   ├── Home.jsx             # Hero + dropzone + stats strip
│   │   │   ├── ScanDetail.jsx       # The big report view (tabs)
│   │   │   ├── History.jsx          # Past scans table
│   │   │   └── ApiDocs.jsx          # Static page showing the integration endpoint
│   │   ├── hooks/
│   │   │   ├── useScan.js           # TanStack Query + refetchInterval while pending
│   │   │   └── useScans.js          # History list
│   │   ├── lib/
│   │   │   └── severity.js          # score → color/label mapping (shared w/ backend bands)
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── .env
│   └── package.json
├── android/
│   ├── app/src/main/
│   │   ├── java/com/sentinel/shield/
│   │   │   ├── MainActivity.kt          # Routes intents: APK open → ScanActivity
│   │   │   ├── ScanActivity.kt          # Hash → lookup/upload → poll → verdict
│   │   │   ├── VerdictScreen.kt         # R/Y/G full-screen result + reasons list
│   │   │   ├── InstallHandoff.kt        # Green verdict → PackageInstaller intent
│   │   │   └── api/
│   │   │       ├── ApiService.kt        # Retrofit interface (matches backend contract)
│   │   │       └── Models.kt            # Mirrors backend schemas.py
│   │   ├── AndroidManifest.xml          # Intent-filters (see §14)
│   │   └── res/layout/...
│   └── build.gradle
├── docker-compose.yml                   # Builds server image (isolated analysis)
├── docs/
│   └── demo-script.md                   # The 90-second pitch script
└── README.md
```

---

## 5. Environment Variables

### Backend (`server/.env`)

```env
PORT=8000
DATABASE_URL=sqlite:///./sentinel.db
STORAGE_DIR=./storage
MAX_UPLOAD_MB=100
SCAN_TIMEOUT_SECONDS=120          # hard kill switch for runaway pipelines
JADX_PATH=jadx                    # absolute path if not on PATH
CORS_ORIGINS=http://localhost:5173

# LLM (any OpenAI-compatible provider; swap base_url for Groq/OpenRouter/Ollama)
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=
LLM_MODEL=gpt-4o-mini
LLM_TIMEOUT_SECONDS=45
LLM_MAX_METHODS=10                # max decompiled methods sent per scan
LLM_MAX_CHARS_PER_METHOD=3000     # truncate long methods
```

### Frontend (`client/.env`)

```env
VITE_API_BASE=http://localhost:8000
```

### Android (`local.properties` or `BuildConfig`)

```properties
# During demo on venue WiFi, point at laptop LAN IP or ngrok tunnel
API_BASE_URL=http://192.168.x.x:8000
```

> **Demo networking note:** the phone must reach the backend. Options: same WiFi + LAN IP (bind uvicorn to `0.0.0.0`), or `ngrok http 8000`. Test this BEFORE demo day.

---

## 6. Data Model

### Scan Table (`server/app/models.py`)

```python
class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # uuid4 hex
    status: Mapped[str] = mapped_column(String, default="queued")
    # queued | static_analysis | decompiling | ai_analysis | completed | failed

    # File fingerprint
    sha256: Mapped[Optional[str]]
    md5: Mapped[Optional[str]]
    file_size_bytes: Mapped[Optional[int]]
    original_filename: Mapped[Optional[str]]

    # Static results (JSON blobs — SQLite-friendly, no migrations needed)
    app_metadata: Mapped[Optional[str]]    # JSON: package, label, versionName, minSdk...
    certificate: Mapped[Optional[str]]     # JSON: signer subject, self_signed, debug_signed
    permissions: Mapped[Optional[str]]     # JSON: [{name, danger_level}]
    components: Mapped[Optional[str]]      # JSON: exported activities/services/receivers
    manifest_flags: Mapped[Optional[str]]  # JSON: cleartext traffic, device admin, deep links
    pattern_hits: Mapped[Optional[str]]    # JSON: [{rule_id, evidence, file, weight}]
    iocs: Mapped[Optional[str]]            # JSON: {domains, ips, urls, phones, base64_blobs}
    embedded_payloads: Mapped[Optional[str]]  # JSON: nested apk/dex/elf found in assets

    # Scores
    rule_score: Mapped[Optional[int]]      # 0-100 from rules engine
    final_score: Mapped[Optional[int]]     # after LLM adjustment (usually == rule_score ± 5)
    severity: Mapped[Optional[str]]        # SAFE | LOW | MEDIUM | HIGH | CRITICAL
    fraud_category: Mapped[Optional[str]]  # banking_trojan | sms_fraud | spyware | ...

    # AI layer
    ai_status: Mapped[Optional[str]]       # ok | unavailable | skipped
    ai_analysis: Mapped[Optional[str]]     # JSON: full LLM output (schema in §9)
    report_markdown: Mapped[Optional[str]]

    error_message: Mapped[Optional[str]]
    duration_ms: Mapped[Optional[int]]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

> JSON-in-text-columns is intentional for hackathon speed. Do not "normalize" this into 8 tables mid-hackathon.

### Severity Bands (must match `client/src/lib/severity.js`)

| Score | Severity | Color |
|---|---|---|
| 0–19 | SAFE | green |
| 20–44 | LOW / MEDIUM | yellow |
| 45–74 | HIGH | orange |
| 75–100 | CRITICAL | red |

---

## 7. Detection Rules (`server/app/data/rules.yaml`)

This is the heart of the explainable score. Each rule: id, description, weight, category. Adding a rule = add entry here + pattern in `pattern_scanner.py`. **No other code changes.**

```yaml
permission_rules:
  - id: PERM_SMS_INTERCEPTION_COMBO
    description: "READ_SMS + RECEIVE_SMS + SEND_SMS together = OTP interception capability"
    required_permissions: [android.permission.READ_SMS, android.permission.RECEIVE_SMS, android.permission.SEND_SMS]
    weight: 30
  - id: PERM_ACCESSIBILITY
    description: "Accessibility service abuse — can read screen content & capture credentials"
    required_permissions: [android.permission.BIND_ACCESSIBILITY_SERVICE]
    weight: 20
  - id: PERM_OVERLAY
    description: "Draw-over-apps — overlay phishing attacks on login screens"
    required_permissions: [android.permission.SYSTEM_ALERT_WINDOW]
    weight: 12
  - id: PERM_DROPPER
    description: "Can install other packages — dropper/stager behavior"
    required_permissions: [android.permission.REQUEST_INSTALL_PACKAGES]
    weight: 18
  - id: PERM_CONTACTS
    required_permissions: [android.permission.READ_CONTACTS]
    weight: 8
  - id: PERM_DEVICE_ADMIN
    required_device_admin: true
    description: "Requests device admin — resists uninstall"
    weight: 18
  - id: PERM_BOOT_PERSISTENCE
    required_permissions: [android.permission.RECEIVE_BOOT_COMPLETED]
    weight: 5

code_rules:   # matched by pattern_scanner regex over decompiled sources
  - id: CODE_DYNAMIC_LOADING
    pattern: "DexClassLoader|PathClassLoader\\("
    description: "Loads executable code at runtime — hides real payload from scanners"
    weight: 18
  - id: CODE_SMS_ABORT
    pattern: "abortBroadcast\\(\\)"
    description: "Silently deletes incoming SMS — classic OTP-stealing behavior"
    weight: 22
  - id: CODE_REFLECTION
    pattern: "Class\\.forName\\(|Method\\.invoke\\("
    weight: 8
  - id: CODE_STRING_DECRYPTION
    pattern: "(Cipher\\.getInstance|javax\\.crypto).{0,200}(Base64|decrypt)"
    description: "Runtime string decryption — obfuscating C2 config"
    weight: 10
  - id: CODE_EXEC
    pattern: "Runtime\\.getRuntime\\(\\)\\.exec"
    weight: 6
  - id: CODE_CONTACT_ENUM
    pattern: "content://com.android.contacts"
    weight: 8
  - id: CODE_DEVICE_ID_HARVEST
    pattern: "getDeviceId\\(|getImei\\(|getSubscriberId\\("
    weight: 6

ioc_rules:
  - id: IOC_RAW_IP_URL
    pattern: "https?://[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}"
    description: "Communicates with bare IP — typical C2 infrastructure"
    weight: 10
  - id: IOC_HTTP_NO_TLS
    pattern: "http://"
    description: "Cleartext HTTP endpoints"
    weight: 4
    max_applications: 3          # cap stacking: apply at most 3 times

metadata_rules:
  - id: META_DEBUG_SIGNED
    condition: cert.debug_signed == true
    weight: 10
  - id: META_SELF_SIGNED
    condition: cert.self_signed == true
    weight: 6
  - id: META_NESTED_APK
    condition: payloads.nested_apk == true
    description: "Contains another APK inside assets — multi-stage dropper"
    weight: 20
  - id: META_TYPOSQUAT
    condition: package_name within edit_distance<=2 of legit_banking_packages.json
    description: "Package name impersonates a legitimate banking app"
    weight: 25
  - id: META_HEAVY_OBFUSCATION
    condition: fraction_of_single_letter_class_names > 0.6
    weight: 8
```

**Score computation (`rules_engine.py`):**
1. Sum all triggered rule weights, capped at 100.
2. Store every trigger as `{rule_id, description, weight, evidence}` — this powers the ScoreBreakdown UI ("why this score").
3. Final score = rule_score (LLM may adjust ±5 via its own confidence field; default = unchanged).

---

## 8. Static Analysis Pipeline (`pipeline.py` orchestration)

Exact stage order and what each writes back to the Scan row:

```
Stage 1  storage.save()            → sha256/md5/size; hash-cache check:
                                     if sha256 seen before with completed scan,
                                     clone that result instantly (status=completed)
Stage 2  static_analysis.run()     → app_metadata, permissions[], components[],
                                     manifest_flags, certificate info (androguard)
Stage 3  decompiler.run()          → jadx → storage/decompiled/<scan_id>/ ; 60s timeout;
                                     on failure: continue WITHOUT code rules (log it)
Stage 4  pattern_scanner.scan()    → pattern_hits[] (regex over decompiled .java)
Stage 5  ioc_extractor.extract()   → domains/ips/urls/phones/base64 blobs
                                     (from manifest + strings.xml + decompiled sources)
Stage 6  rules_engine.score()      → rule_score, severity, triggers[]
Stage 7  ai_analyst.analyze()      → method_selector picks top-N suspicious methods
                                     → LLM → ai_analysis JSON (§9); sets ai_status
Stage 8  report_generator.build()  → report_markdown (§10); status=completed
```

Target end-to-end time: **under 40 seconds** for a mid-size APK (jadx is usually the slowest step).

**Timeout discipline:** wrap jadx and the LLM call with explicit timeouts. A single hung stage must not hang the scan — mark failed stage, continue, complete with partial results. Partial verdict >> no verdict.

---

## 9. AI Layer Contract (`ai_analyst.py`) — MOST IMPORTANT FILE TO GET RIGHT

### Input assembly — the selection funnel (`method_selector.py`)

```
jadx output (500–3000 files, 10k+ methods)
  → SPLIT each file into methods (brace-depth parser)
  → SCORE: suspicion = Σ weights of rules.yaml code_rules matching inside the method
      · count DISTINCT rule matches per method (repeated same-pattern hits don't stack)
      · +8 entry-point boost if the class is a manifest-declared receiver/service/
        exported activity (attacker logic must hang off entry points)
  → RANK desc → keep top LLM_MAX_METHODS, truncate each to LLM_MAX_CHARS_PER_METHOD
  → assemble prompt: context header + annotated method blocks (~8k tokens total budget)
```

Edge cases:
- **Zero pattern hits anywhere** → skip the LLM call entirely (`ai_status="skipped"`), verdict comes from rules alone (instant GREEN path).
- **Fewer than N scored methods** → pad with largest methods from manifest-declared components so the model always has context.
- **Cross-method flows (A→B→C calls)** — only the top method is sent for MVP; cross-method taint analysis is a roadmap item. Admit this if asked.

#### Why regex survives obfuscation (judge-question armor)

We match **Android framework API calls and manifest declarations**, NOT developer-chosen names:

- Obfuscators (ProGuard/R8) rename only attacker-authored classes/methods (`StealOtp.send()` → `a.b.c()`). Framework contracts cannot be renamed: `abortBroadcast()`, `DexClassLoader`, `SmsManager.sendTextMessage`, `Cipher.getInstance`, `getDeviceId()` are resolved by canonical name against the OS at runtime — renaming them causes `NoSuchMethodError`.
- Manifest signals are even more rigid: `<uses-permission android:name="android.permission.RECEIVE_SMS">` must appear verbatim or the capability doesn't exist.
- Aggressive renaming itself trips `META_HEAVY_OBFUSCATION`; hiding API names behind strings requires reflection + crypto + Base64 — each independently scored (`CODE_REFLECTION`, `CODE_STRING_DECRYPTION`).

Known blind spots (be honest if pushed): native `.so` payloads invisible to jadx; payloads fetched from network post-install (we see the `DexClassLoader`, not its remote DEX); framework APIs we haven't written a rule for. These are why the LLM reads flagged code *semantically* and why emulator-based dynamic analysis sits on the roadmap.

### Prompt skeleton (system prompt)

```
You are a senior mobile malware analyst working for a bank's fraud prevention team.
You are given decompiled Java methods from an Android APK plus its permission list
and static analysis findings. Determine whether this application exhibits fraudulent
or malicious behavior (especially: banking trojans, OTP/SMS interception, credential
phishing overlays, spyware, premium SMS fraud).

Rules:
- Base conclusions ONLY on provided evidence. If evidence is inconclusive, say so
  and lower confidence — never fabricate IOCs or behaviors.
- Quote specific method names / lines as evidence.
- Output STRICT JSON conforming exactly to the provided schema. No prose outside JSON.
```

User message: context header + method blocks + instruction to return the JSON schema below.

### Required output schema (enforce with JSON mode / function calling if available; otherwise parse robustly)

```json
{
  "fraud_category": "banking_trojan | sms_otp_stealer | overlay_phishing | spyware | premium_sms_fraud | ransomware | adware | pupe | benign",
  "confidence": "high | medium | low",
  "behavior_summary": "2-4 sentence plain-English explanation of what this app actually does",
  "attack_chain": [
    { "step": 1, "title": "Delivery", "detail": "...", "evidence": ["MainActivity.onCreate"] },
    { "step": 2, "title": "...", "detail": "...", "evidence": ["..."] }
  ],
  "iocs": {
    "domains": [],
    "ips": [],
    "urls": [],
    "phone_numbers": [],
    "package_names": []
  },
  "mitre_techniques": [
    { "id": "T1409", "name": "Stored Application Data", "reason": "..." }
  ],
  "recommendations": [
    "Block hash at email/SMS gateway",
    "Notify customers who received distribution link"
  ]
}
```

### Robustness requirements (do not skip)

- Strip markdown fences before `json.loads`; retry once with "return valid JSON only" on parse failure.
- Validate with Pydantic; on validation failure keep partial fields that parsed.
- Log raw response to `storage/reports/<scan_id>_raw_llm.txt` for debugging.

---

## 10. Report Format (`report_generator.py`)

Markdown template, filled from merged results:

```markdown
# Threat Investigation Report — <app label>
**Verdict:** 🔴 CRITICAL (87/100) · banking_trojan · Confidence: high
**SHA-256:** `abc...` · **Analyzed:** 2026-08-21 14:02 UTC

## Executive Summary
<behavior_summary>

## Attack Chain
1. **Delivery** — ...
2. **OTP Interception** — ...

## Risk Score Breakdown
| Triggered Rule | Evidence | Points |
|---|---|---|
| SMS interception combo | ... | +30 |

## Permissions Requested
(table with danger flags)

## Indicators of Compromise
(domains / IPs / URLs / phones / hashes — copyable)

## MITRE ATT&CK Mobile Mapping
(chips)

## Recommended Actions
(from LLM + static playbook)
```

PDF export = stretch goal (`weasyprint` or print-CSS in the dashboard browser). Markdown download must ship regardless.

---

## 11. Backend API Reference

Base URL: `http://localhost:8000`. All responses JSON. **No auth** (intentionally out of scope — see §17).

#### `POST /api/scan`
Upload + start pipeline. Multipart form: `file=<apk>`.

**Response `202`:**
```json
{ "scan_id": "9f1c..." }
```

Errors: `413` file too large, `415` not an APK (check zip magic bytes + `.apk` extension), `429` concurrent scan limit (cap at 2 simultaneous pipelines).

#### `POST /api/lookup/hash`
Fast path used by the Android app BEFORE uploading anything.

**Request:**
```json
{ "sha256": "abc...", "md5": "def..." }
```

**Response `200` (known):**
```json
{ "known": true, "scan_id": "9f1c...", "severity": "CRITICAL", "final_score": 87, "fraud_category": "sms_otp_stealer" }
```

**Response `200` (unknown):**
```json
{ "known": false }
```

#### `GET /api/scan/{scan_id}`
Polled by both clients every ~2s while `status` is a working state.

**Response `200` (in progress):**
```json
{ "scan_id": "9f1c...", "status": "decompiling", "progress_hint": "Decompiling bytecode (stage 3/8)" }
```

**Response `200` (completed):** full result — all fields from §6 deserialized, including `ai_analysis` object, `triggers[]`, `report_markdown`.

#### `GET /api/scan/{scan_id}/report?format=md`
Downloads the report file.

#### `GET /api/scans?page=1&limit=20`
History list: `{ scans: [...], total }` — id, filename, score, severity, category, created_at.

#### `GET /api/stats`
Dashboard hero strip: `{ total_scans, malicious_found, avg_duration_ms, unique_hashes }`.

#### Integration pitch endpoint
The pair `POST /api/lookup/hash` + `POST /api/scan` IS the bank-gateway integration story — mention it explicitly in the pitch.

---

## 12. Dashboard Pages & Components

| Page | Route | Description | Key components |
|---|---|---|---|
| Home | `/` | Hero + drag-drop dropzone + stats strip + recent scans mini-list | Dropzone, RiskGauge (mini), Badge |
| ScanDetail | `/scan/:id` | Full report view. Tabs: Overview (verdict card + gauge + pipeline status), Findings (permissions + pattern hits + ScoreBreakdown), AI Analysis (behavior summary + AttackChain + MitreList), IOCs (IocTable), Report (rendered markdown + download btn) | all scan/* components, Tabs |
| History | `/history` | Table of past scans, filter by severity, click-through | Card, Badge, Skeleton |
| ApiDocs | `/docs` | Static page showing integration curl examples — sells "bank-ready" in pitch | Card |

**Polling hook pattern:**

```javascript
// hooks/useScan.js
export const useScan = (scanId) =>
  useQuery({
    queryKey: ['scan', scanId],
    queryFn: () => api.get(`/api/scan/${scanId}`).then(r => r.data),
    refetchInterval: (query) =>
      ['queued', 'static_analysis', 'decompiling', 'ai_analysis'].includes(query.state.data?.status)
        ? 2000 : false,
  })
```

**No auth, no global store.** Axios instance + TanStack Query covers everything. Don't add Zustand/Redux.

---

## 13. Scan Flow (end-to-end lifecycle)

### Web (analyst)
```
1. Analyst drags APK onto Dropzone (Home)
2. POST /api/scan → scan_id → navigate /scan/:id
3. PipelineStatus component ticks through stages as polls return
4. On status=completed: RiskGauge animates to score, tabs populate
5. Analyst opens AI Analysis tab → reads attack chain
6. Downloads report (.md) / screenshots IOC table
```

### Phone (end user)
```
1. User taps malicious APK received over WhatsApp
2. Android offers openers → user picks (or defaults to) Sentinel Shield
3. MainActivity receives VIEW intent with content:// URI
4. ScanActivity: read stream → SHA-256 → POST /api/lookup/hash
5a. known → show verdict immediately (instant — great demo moment)
5b. unknown → upload APK → poll GET /api/scan/{id} → show spinner (~30s)
6. VerdictScreen:
   RED    → "Do not install" + reasons list + category icon. Block button.
   YELLOW → warnings + "Install at your own risk"
   GREEN  → "Looks safe" + Continue → InstallHandoff fires system installer intent
7. Scan appended to in-app history list
```

**Verdict thresholds on phone:** score ≥75 RED, 40–74 YELLOW, <40 GREEN (same bands, coarser edges).

---

## 14. Android App Implementation Notes

### Manifest intent filters (the entire "interception" trick)

```xml
<!-- Registers as handler for APK files opened from anywhere -->
<intent-filter>
    <action android:name="android.intent.action.VIEW"/>
    <category android:name="android.intent.category.DEFAULT"/>
    <category android:name="android.intent.category.BROWSABLE"/>
    <data android:scheme="content"/>
    <data android:scheme="file"/>
    <data android:mimeType="application/vnd.android.package-archive"/>
</intent-filter>
<uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES"/>
<uses-permission android:name="android.permission.INTERNET"/>
```

### Gotchas (learned the hard way — read before coding)

- Content URIs: always read via `contentResolver.openInputStream(uri)` — never `File(path)`.
- Some apps send APKs with wildcard mime (`application/octet-stream`) — add a second intent-filter for that ONLY with user initiation via share-sheet, otherwise you'll hijack every file open. Safer: handle octet-stream in `onCreate` by sniffing zip magic bytes.
- `cleartextTrafficPermitted=true` in network security config if pointing at `http://` LAN backend.
- Retrofit timeouts: connect 15s / read 60s (uploads on venue WiFi are slow).
- Keep the whole app in ONE activity with view switching — less state plumbing.
- **Test the intent-filter flow with `adb install` of the scanner itself, then opening a random .apk from Files app — do this FIRST, it's the riskiest unknown.**

---

## 15. Third-Party Services Setup

### LLM provider
Any OpenAI-compatible endpoint works because only `base_url/key/model` are configured. Suggested: OpenAI `gpt-4o-mini` (cheap+fast) or Groq `llama-3.3-70b-versatile` (very fast, generous free tier — good for repeated demos). Verify JSON-mode support; if absent, rely on the robust parser (§9).

### jadx
```bash
# macOS
brew install jadx
# Linux: download release zip from github.com/skylot/jadx, unzip, add bin/ to PATH
# Docker image: bake into server image (ADD jadx zip + unzip in Dockerfile)
jadx --version
```

### Androguard
```bash
pip install androguard==3.3.5   # pin the version; 4.x changed APIs
```

### Real malware samples for testing (handle with care)
- **MalwareBazaar (abuse.ch)** — filter `tag:android`, `type:apk`. Download a few known banking-trojan families for testing only.
- Never install samples on real devices. Never run outside the Docker container. Keep them in `server/samples/` (gitignored) and delete after the event.
- Preferred demo path is your OWN built "fake fraudulent" APK (see §16) — offline-safe, legal, deterministic.

---

## 16. Demo Strategy (build these BEFORE hackathon day)

### Self-built fake malicious APK (primary demo sample)
Build in Android Studio (~1h): innocent-looking calculator/battery app that:
1. Requests `READ_SMS`, `RECEIVE_SMS`, `SEND_SMS`, `BIND_ACCESSIBILITY_SERVICE`, `SYSTEM_ALERT_WINDOW`
2. BroadcastReceiver on `SMS_RECEIVED` that calls `abortBroadcast()` and forwards body to hardcoded `http://185.x.x.x/collect` (RFC5737 IP — reserved for docs, safe to display publicly)
3. One `DexClassLoader` reference and a Base64+Cipher string blob (to trip those rules)

Result: guaranteed RED verdict, offline, zero legal issues, and the score breakdown lights up beautifully.

### Benign control sample
A clean notes app (normal permissions only) → must come back GREEN. Proves you don't cry wolf.

### Backup recordings
Record full demo flow (phone interception + dashboard report) as video BEFORE the event. Live demos die; recordings don't. Venue WiFi WILL be hostile — have phone-on-hotspot-to-laptop as plan B and pure-video as plan C.

### 90-second pitch arc
1. WhatsApp message with APK tap → Sentinel intercepts → spinning → **RED ALERT: OTP stealer** (crowd moment)
2. Cut to analyst dashboard: same APK, deep report — attack chain narrated by AI, IOCs, MITRE mapping
3. Show score breakdown: "every point explained — auditable, not a black box"
4. Close: *"Same engine, two shields: the customer's pocket and the bank's SOC. One API away from gateway integration."*

---

## 17. What's Intentionally Not Built

Valid "what would you improve next?" answers:

- **Dynamic/emulated runtime analysis** (Frida + headless emulator + mitmproxy) — biggest future upgrade; our LLM code-behavioral layer approximates it statically
- **Custom ML classifier** trained on Drebin/CICMalDroid2020 — rules+GenAI was chosen for explainability and 24h feasibility
- **RAG knowledge base** of malware TTPs — currently direct prompting
- **Auth / multi-tenancy / RBAC** on dashboard
- **Celery+Redis job queue** — BackgroundTasks suffices at demo concurrency
- **VirusTotal cross-enrichment** — easy add: one more pipeline stage
- **Report PDF generation** — markdown ships, PDF is polish
- **JWT-signed verdict responses** for the phone app (anti-tamper) — production concern

---

## 18. Team Split & Build Order (24h)

| Hours | Person A (Backend core) | Person B (GenAI + report) | Person C (Android) | Person D (Dashboard) |
|---|---|---|---|---|
| 0–2 | Scaffold FastAPI + models + upload endpoint + hash cache | LLM client + prompt + JSON schema + robust parser | Project setup + **verify intent-filter opens app** (§14 gotcha) | Vite + Tailwind + shadcn init + router + pages shell |
| 2–6 | static_analysis.py + storage + pipeline skeleton | method_selector + wire into pipeline behind flag | Hash + lookup + upload + poll services | Dropzone + useScan polling + PipelineStatus |
| 6–12 | decompiler.py + pattern_scanner + rules.yaml + rules_engine | ai_analyst tuning against fake-malicious APK; report_generator | VerdictScreen R/Y/G + InstallHandoff | RiskGauge + ScoreBreakdown + PermissionTable |
| 12–16 | Timeouts, error paths, concurrency cap, tests vs both samples | AttackChain/MitreList data shapes agreed w/ D; IOC polish | History screen + LAN/ngrok testing on real device | AttackChain + IocTable + ScanDetail tabs assembled |
| 16–20 | Docker compose + deploy (Railway/Render) | PDF/markdown export + report copy quality pass | Polish + record backup videos | Stats strip + History + ApiDocs page |
| 20–24 | Buffer/integration bugs | Pitch deck + demo-script.md rehearsal | Buffer | Visual polish + empty/error states |

**Definition of "done" for MVP (hour ~16 checkpoint):** upload fake-malicious APK on web → get CRITICAL verdict with AI attack chain + downloadable report. Everything else is enhancement.

---

## Quick Start

### Backend

```bash
cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
brew install jadx            # or see §15
cp .env.example .env         # fill LLM keys
uvicorn app.main:app --reload --port 8000
# Swagger at http://localhost:8000/docs
```

### Dashboard

```bash
cd client
npm install
npx shadcn@latest add button card badge tabs dialog skeleton input separator
npm run dev                  # http://localhost:5173
```

### Android

```bash
open android/ in Android Studio → Run on device
# Set API_BASE_URL to laptop LAN IP; ensure uvicorn bound to 0.0.0.0
```

### Run full pipeline against a sample (CLI sanity check)

```bash
cd server
python -m app.services.pipeline --sample samples/fake_banker.apk
# prints stage-by-stage progress + final score + report path
```

### Docker isolation (recommended even locally)

```bash
docker compose up --build    # builds server image with jadx baked in
```

---

*Keep this document in sync with actual implementation. When you change an API shape, a rule weight, or the LLM schema — update it here first, then code.*
