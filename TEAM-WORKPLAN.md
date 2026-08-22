# APK Sentinel — Parallel Team Workplan (10–12 Hours)

> Companion document to `APK-SENTINEL-REFERENCE.md` (the full technical spec). That document says WHAT we're building; this one says WHO builds WHAT, WHEN, and HOW TO VERIFY each piece — designed so 3 people (each working with their own AI assistant) can build in one repo simultaneously without stepping on each other.
>
> **Assumptions:** 3 people, same room, ~10–12 productive hours, each person uses a different AI coding assistant. All architecture/API decisions come from the Reference doc — do NOT redesign here.

---

## 0. Read This First: How We Parallelize One Repo

Working simultaneously in one repo is safe **only if file ownership is disjoint**. Our folder layout makes this almost automatic:

### File Ownership Map (STRICT)

| Folder/files | Owner | Nobody else touches |
|---|---|---|
| `server/app/services/storage.py`, `static_analysis.py`, `decompiler.py`, `pattern_scanner.py`, `ioc_extractor.py`, `rules_engine.py`, `pipeline.py`, `app/data/rules.yaml`, `Dockerfile`, `requirements.txt` | **Person A** | — |
| `server/app/services/method_selector.py`, `ai_analyst.py`, `report_generator.py`, `server/fixtures/`, `server/samples/` | **Person B** | — |
| `client/**` (everything) | **Person C** | — |
| `android/**` | **Person C (Phase 2)** — see Block 3 | — |
| `server/app/schemas.py`, `models.py`, `routers/scans.py` | **Person A**, but see Contract Freeze below | — |

### Contract Freeze (Hour 1, non-negotiable)

The API request/response shapes and the LLM output schema in `APK-SENTINEL-REFERENCE.md` §6, §9, §11 are **FROZEN at Hour 1**. Everyone codes against those shapes immediately using committed fixture files:

- **B never waits for A**: B develops `ai_analyst.py` against `server/fixtures/decompiled_sample/` (pre-decompiled java files committed to the repo in Hour 1).
- **C never waits for A**: C develops the entire dashboard against `client/src/mocks/scanResponse.json` (a completed-scan JSON matching §11, committed in Hour 1). Mock toggle: `VITE_USE_MOCKS=true`.

If anyone MUST change a frozen shape: announce out loud, update the Reference doc first, then code. Never silently drift.

### Git Discipline

```
main          ← always runnable; merged ONLY at checkpoints
├── a/backend     ← Person A
├── b/genai       ← Person B
├── c/frontend    ← Person C (later: c/android second branch)
```

- Commit to your personal branch every ~45–60 min. Commit messages: `a: static analysis permissions parsing` style.
- Merge to `main` only at the 3 scheduled checkpoints (§5). Between checkpoints, `main` is sacred — nobody pushes "quick fixes."
- Merge order at checkpoints: A first (backend is the dependency root), then B, then C. Resolve conflicts in YOUR OWN folder only.
- Pull before you start each block. Push before each checkpoint.

### Working With Your AI (all three of us use different AIs)

Add an `AGENTS.md` (and/or `CLAUDE.md`) to the repo root containing exactly this:

```markdown
# Repo instructions
1. Before ANY work, read APK-SENTINEL-REFERENCE.md (full spec) and TEAM-WORKPLAN.md (who owns what).
2. You are assisting ONE person. Only modify files listed under their ownership in TEAM-WORKPLAN.md §File Ownership Map. If a needed change falls outside, STOP and tell the human to coordinate.
3. API shapes and the LLM JSON schema are frozen per Reference doc §6, §9, §11. Do not invent new fields.
4. Do not add auth, databases other than SQLite, or features listed in Reference doc §17 (out of scope).
5. After changes, run the verification command for that block from TEAM-WORKPLAN.md and paste results.
```

Each block below ends with **"Kickoff prompt"** text — paste it into your AI at block start.

---

## 1. Personas & Tracks

| | Person A — Pipeline Core | Person B — GenAI & Reports | Person C — Surfaces (Web + Phone) |
|---|---|---|---|
| Language | Python | Python | JavaScript/React + Java |
| Owns | Stages 1–6 of pipeline | Stages 7–8 of pipeline | Dashboard + Android app |
| Deliverable | Upload→score works rules-only | AI attack chain + investigation report | Both demo surfaces |
| Needs from others | Nothing (works from spec) | Fixture decompiled code (H1), A's `pattern_hits` JSON shape | A's API live at H6, mock JSON before that |

> Why B can start instantly: the LLM layer only needs (a) some decompiled methods as input and (b) the frozen output schema. We commit a decompiled fixture in Hour 1 so B is never blocked by A's jadx work.

---

## 2. Timeline At a Glance

| Block | Hours | Theme | Ends with |
|---|---|---|---|
| 0 | H0–H1 | Setup + risk spikes + fixtures committed | Every AI can run its env; riskiest unknowns proven |
| 1 | H1–H3.5 | Independent cores (mocks/fixtures) | A: static scan runs. B: LLM returns valid JSON on fixture. C: full dashboard UI on mocks |
| 2 | H3.5–H6 | Depth + demo assets | A: rules engine scores real APK. B: fake-malicious APK built + tuned prompts. C: screens complete on mocks |
| ✅ CP1 | H6 (~30 min) | **Integration #1** | Real upload → rules-only verdict visible on real dashboard |
| 3 | H6.5–H9 | Wiring everything live | Full pipeline incl. AI; Android app talks to backend |
| ✅ CP2 | H9 (~30 min) | **Integration #2 (full E2E)** | Phone RED alert + dashboard report, both live |
| 4 | H9.5–H11.5 | Deploy + demo prep | Deployed URLs, backup videos recorded, pitch rehearsed ×2 |
| Buffer | H11.5–H12 | Sleep on it / fix reds | — |

---

## 3. Block-by-Block Detail

### BLOCK 0 — Setup & Risk Spikes (H0–H1)

**ALL (first 15 min, together):**
- [ ] Create fresh repo; copy `APK-SENTINEL-REFERENCE.md` + this file in
- [ ] Create branch structure (`a/backend`, `b/genai`, `c/frontend`)
- [ ] Add `AGENTS.md` (text in §0 above)
- [ ] Create `.gitignore`: `.env`, `node_modules`, `server/storage/`, `server/samples/*.apk`, `*.db`
- [ ] **Contract freeze announcement** — confirm everyone has read §6, §9, §11

**Person A — environment proof:**
- [ ] `python -m venv`, install `fastapi uvicorn python-multipart sqlalchemy pydantic-settings httpx`
- [ ] Install jadx (`brew install jadx` / release zip), verify `jadx --version`
- [ ] Scaffold `server/app/` exactly per Reference §4 tree; `uvicorn app.main:app --reload` serves `GET /health`
- [ ] Commit empty `requirements.txt` updated

**Person B — LLM proof (the #1 external dependency):**
- [ ] Get API key working (OpenAI gpt-4o-mini, or Groq free tier `llama-3.3-70b-versatile` — decide NOW based on key availability)
- [ ] Write a throwaway script: send a fake "suspicious method" + demand the §9 JSON schema back → parse it with Pydantic
- [ ] Verify JSON-mode/robust parsing works with YOUR provider (strip ``` fences, retry once)
- [ ] Commit the script as `server/scripts/test_llm.py`

**Person C — THE RISK SPIKE (most important task of the whole day):**
- [ ] Empty Android Studio project, one Activity, add the intent-filter from Reference §14
- [ ] Build, install on the physical phone, open any random APK from Files/WhatsApp → confirm OUR app appears in the chooser and receives the URI
- [ ] Log the URI; read bytes via ContentResolver; print length
- [ ] **If this fails after ~40 min of trying: STOP, announce.** Fallback decision gets made at once (see §6 Fallbacks) — do not burn Block 1 time on it

**Block 0 exit criteria:** A's server boots · B parses a real LLM JSON · C's phone opens-the-right-app. Any ❌ = escalate immediately, adjust fallbacks (§6).

---

### BLOCK 1 — Independent Cores (H1–H3.5)

> Theme: nobody waits for anybody. A/B/C all produce working units against fixtures/mocks.

**Person A:**
- [ ] `storage.py`: save upload to `storage/apks/<scan_id>.apk`, compute sha256/md5, size limit check (100 MB), hash-cache lookup
- [ ] `static_analysis.py` with Androguard: package name, label, versionName, permissions[], exported components, receivers/services, device-admin flag, cleartext flag, cert info (self-signed/debug detection)
- [ ] `models.py` Scan table + `database.py` (SQLite) exactly per Reference §6
- [ ] `POST /api/scan` + `GET /api/scan/{id}` returning status machine (`queued → static_analysis → …`)
- [ ] Pipeline orchestrator skeleton: stage functions stubbed, status transitions real

**Person A verification (alone):**
```bash
curl -s -X POST localhost:8000/api/scan -F "file=@any.apk"      # → {"scan_id": "..."}
sleep 3 && curl -s localhost:8000/api/scan/<id> | python -m json.tool
# PASS = permissions[] populated, status advanced through stages without crash
```

**Person B:**
- [ ] Commit `server/fixtures/decompiled_sample/`: 6–10 suspicious-looking java methods (write realistic ones by hand or ask AI — SMS receiver calling abortBroadcast(), DexClassLoader loader, AES string decryptor, contact enumerator). This is B's permanent test rig.
- [ ] `method_selector.py`: split a `.java` file into methods, score by pattern hits (regex list shared with A via `rules.yaml` code_rules section — READ it, don't edit), truncate long methods
- [ ] `ai_analyst.py`: full prompt (Reference §9), provider call, Pydantic validation, retry-on-parse-failure, raw-response logging to `storage/reports/`
- [ ] `ai_status` handling: timeout/no-key → `"unavailable"`, never crashes caller

**Person B verification (alone):**
```bash
python -m app.services.ai_analyst --fixture fixtures/decompiled_sample/
# PASS = prints valid attack_chain ≥2 steps, iocs extracted from the fixture strings,
# completes <45s, and still exits cleanly with LLM_API_KEY unset (degraded path)
```

**Person C:**
- [ ] Vite + Tailwind + shadcn init; router with 4 pages (Home/ScanDetail/History/ApiDocs)
- [ ] Commit `src/mocks/scanResponse.json` matching §11 completed-shape (ask AI to generate from the Reference doc — good AI task)
- [ ] Build ALL major components against mocks: Dropzone, PipelineStatus (fake stage ticker), RiskGauge (SVG), VerdictCard, ScoreBreakdown, PermissionTable, AttackChain, IocTable, MitreList
- [ ] `VITE_USE_MOCKS=true` api layer that returns mocks with artificial delays

**Person C verification (alone):**
```bash
npm run dev   # click through every page with mock data; no console errors
# PASS = full report experience viewable WITHOUT any backend running
```

**Block 1 exit criteria:** three green units, zero cross-dependency. No collective testing yet — nothing integrated, nothing to gain.

---

### BLOCK 2 — Depth + Demo Assets (H3.5–H6)

**Person A:**
- [ ] `decompiler.py`: jadx subprocess wrapper (timeout 60s, unique output dir per scan_id, failure → continue without code rules)
- [ ] `pattern_scanner.py`: run every `code_rules` regex over decompiled tree → pattern_hits[] with evidence (file + matched line)
- [ ] `ioc_extractor.py`: URL/IP/phone/base64 regexes over manifest + strings.xml + sources
- [ ] `rules_engine.py`: load `rules.yaml`, evaluate permission/code/ioc/metadata rules, capped sum → rule_score + triggers[] (Reference §7)
- [ ] Wire stages 2–6 into pipeline with real status updates

**Person A verification (alone):**
```bash
python -m app.services.pipeline --sample <some.apk>
# PASS = prints stage progress, rule_score, triggers[] listing e.g. PERM_SMS_INTERCEPTION_COMBO,
# total runtime <60s, and completes even with jadx binary path broken (graceful skip)
```

**Person B — build the demo malware (yes, really):**
- [ ] New Android Studio project "PhotoVault" (innocuous name/icon): permissions per Reference §16, SMS receiver calling `abortBroadcast()` + forwarding to `http://185.x.x.x/collect` (RFC5737 IP), one DexClassLoader line, Base64+Cipher blob
- [ ] Build BOTH samples: `samples/fake_banker.apk` (must trip ≥5 rules) and `samples/benign_notes.apk` (must stay SAFE)
- [ ] Tune `ai_analyst` prompt against fake_banker fixture output until attack_chain tells the OTP-theft story correctly and benign comes back benign
- [ ] `report_generator.py`: markdown template per Reference §10

**Person B verification (alone):**
```bash
python -m app.services.report_generator --input <B's manual merge of A's trigger JSON + own ai_analysis>
# PASS = readable report.md renders correctly in VS Code preview; benign sample produces SAFE verdict
```

**Person C:**
- [ ] History page + stats strip wired to mocks
- [ ] Report tab: render markdown (react-markdown), download button (blob)
- [ ] ApiDocs page (static, shows integration curls — sells "bank-ready")
- [ ] Empty/error/loading states everywhere (Skeletons)
- [ ] Visual pass: severity colors consistent with bands (§6 of Reference), responsive-enough for projector

**Person C verification (alone):**
```bash
# Click-through: Home→upload(mock)→live stage ticker→CRITICAL report→download .md→History
# PASS = zero dead buttons, all states handled
```

**Block 2 exit criteria:** A scores real APKs standalone · two demo APKs exist · dashboard pixel-complete on mocks.

---

### ✅ CHECKPOINT 1 (H6, timebox 30 min) — First Collective Test

**Merge order: A → B(except ai wiring) → C. Then run together:**

1. Start A's server. C flips `VITE_USE_MOCKS=false`, sets `VITE_API_BASE=http://localhost:8000`
2. Drag `samples/fake_banker.apk` onto the REAL dashboard
3. Watch stages advance → rules-only verdict appears (AI tab may show placeholder)
4. `curl localhost:8000/api/lookup/hash` with the known sha256 → `"known": true`

**Rules for this checkpoint (important):**
- Timeboxed 30 min. Bug found? Owner fixes solo on their branch; group does NOT crowd around one laptop
- If >2 blocking bugs: abort, revert to branches, fix, re-convene in 20 min. Don't death-spiral
- Success = rules-only E2E green. AI layer intentionally NOT in this checkpoint (that's CP2)

---

### BLOCK 3 — Live Wiring + Phone App (H6.5–H9)

**Person A:**
- [ ] Hardening pass: explicit timeouts on EVERY stage, concurrency cap (max 2 running scans → 429), malformed-file rejection (zip magic check), error_message population, duration_ms
- [ ] `GET /api/scans` history + `GET /api/stats`
- [ ] CORS config from env; bind note: `uvicorn ... --host 0.0.0.0` for LAN access
- [ ] Merge B's services into pipeline: stage 7 call with try/except → ai_status handling verified end-to-end
- [ ] `scripts/smoke.sh`: upload fake_banker → poll till done → assert severity CRITICAL + ai_status ok → download report. Prints PASS/FAIL per step

**Person B:**
- [ ] Score-merge logic with A (final_score = rule_score default; document ± adjustment rule)
- [ ] Prompt-quality pass on REAL pipeline outputs (garbage in A's pattern_hits formatting → fix serialization, not the prompt)
- [ ] MITRE mapping grounded: include a mini technique list in the prompt so IDs aren't hallucinated
- [ ] Recommendations quality: bank-actionable phrasing ("block hash at SMS gateway", not "be careful")
- [ ] Markdown report polish + (stretch) PDF attempt — drop PDF instantly if it eats >45 min

**Person C — Part 1 (web, ~1.5h):**
- [ ] Kill all mocks: real Dropzone → POST /api/scan → route to /scan/:id → real polling hook (Reference §12 refetchInterval pattern)
- [ ] Handle 413/415/429 errors visibly; handle ai_status=unavailable banner

**Person C — Part 2 (Android, ~2.5h, this is the owner's Java hour):**
- [ ] Single Activity, 3 views: Scanning(spinner) / Verdict(RYG) / History(list)
- [ ] Hash stream → `POST /api/lookup/hash` → known? instant verdict : upload multipart → poll GET
- [ ] VerdictScreen thresholds: ≥75 RED / 40–74 YELLOW / <40 GREEN + reasons list from triggers
- [ ] GREEN handoff: fire ACTION_VIEW install intent (REQUEST_INSTALL_PACKAGES perm already in manifest)
- [ ] `usesCleartextTraffic=true`; Retrofit timeouts 15s/60s; API base in BuildConfig

**Person C verification (alone, in order — network BEFORE app logic):**
```bash
# 1. Phone browser → http://<laptop-LAN-IP>:8000/health   (network reachable?)
# 2. adb install scanner.apk; open fake_banker.apk from Files → our app intercepts?
# 3. Full flow on phone: RED verdict for fake_banker, GREEN for benign_notes
```

**Block 3 exit criteria:** `smoke.sh` green · dashboard fully live · phone RED/GREEN flow works on LAN.

---

### ✅ CHECKPOINT 2 (H9, timebox 30 min) — Full E2E, Both Surfaces

1. Web: fresh upload of fake_banker → CRITICAL + real AI attack chain + report download
2. Benign control: benign_notes.apk → SAFE/green everywhere (proves no crying wolf)
3. Phone: WhatsApp-style open of fake_banker → intercepted → RED alert with reasons
4. Hash re-scan of same file → instant cached verdict
5. Repeat demo twice back-to-back (timing matters for pitch: target <40s full scan)

Same checkpoint rules as CP1: timebox, owners fix solo, abort-and-branch if spiraling.

---

### BLOCK 4 — Deploy, Record, Rehearse (H9.5–H11.5)

- [ ] **C:** Deploy dashboard → Vercel (env: prod API URL). Deploy backend → Railway/Render with Dockerfile (jadx baked in). Verify deployed E2E once
- [ ] **A:** Docker compose polish + README quick-start section + `.env.example` files complete
- [ ] **B:** Backup videos (screen-record, phone on hotspot AND laptop-only variants): full phone RED flow + full dashboard report flow. These are plan C if venue WiFi dies — non-negotiable
- [ ] **ALL:** Pitch rehearsal ×2 against timer (script: Reference §16). Assign sections: opener+C, engine/A, AI story+B, close+C
- [ ] Freeze features at H11. From here: bug fixes only, no new anything

---

## 4. Testing Cheat Sheet

| Layer | Command/artifact | PASS condition |
|---|---|---|
| A: static scan | `python -m app.services.pipeline --sample X.apk` | Stage log + score + triggers printed, <60s |
| A: API | `scripts/smoke.sh` | All steps PASS |
| B: LLM | `python -m app.services.ai_analyst --fixture ...` | Valid schema JSON, <45s, degraded path exits clean |
| B: reports | generated `report.md` preview | Renders, correct verdict language |
| C: web (mocks) | `npm run dev` + click-through | Zero dead buttons/console errors |
| C: web (live) | CP1/CP2 flows | Verdict matches expected sample behavior |
| C: phone | 3-step sequence in Block 3 | Reach API → intercept → correct color |
| Samples | fake_banker vs benign_notes | CRITICAL vs SAFE respectively — run at EVERY checkpoint |

Golden rule: **continuous solo testing, scheduled group testing (CP1, CP2 only).** Group-debugging between checkpoints historically causes more errors than it finds — resist the urge.

---

## 5. Fallback Decision Tree (decide loudly, once, then move on)

| Failure | Trigger | Fallback |
|---|---|---|
| Android intent-filter spike fails | End of Block 0 | Plan B: demo phone flow via phone **browser** hitting a mobile-width page of the dashboard (still a great story). Native app becomes "roadmap" slide |
| LLM provider down/keyless | Block 0 | Groq/OpenRouter swap (env-only change). Worst case: ship rules-engine product + canned example AI report in slides |
| jadx fails on venue laptop | anytime | Graceful skip already built in — demo with permissions/IOC rules only; pre-generate one complete report as artifact beforehand |
| Venue WiFi hostile | demo time | Phone hotspot ↔ laptop LAN. Last resort: recorded videos (Block 4) |
| Behind schedule at H9 | — | Cut order (sacrifice first): PDF export → ApiDocs page → stats strip → History page. NEVER cut: web E2E verdict, phone RED moment, backup videos |

---

## 6. Kickoff Prompts (paste into your AI at each block start)

**A:** *"Read APK-SENTINEL-REFERENCE.md fully. You are helping build the backend pipeline (folders/files owned by Person A in TEAM-WORKPLAN.md §Ownership). Implement [BLOCK TASK LIST]. Follow frozen schemas §6/§11 exactly. Finish by running the block's verification command and show me output."*

**B:** *"Read APK-SENTINEL-REFERENCE.md §9, §10, §16. You own ai_analyst.py, method_selector.py, report_generator.py, fixtures/ and samples/. Current block: [TASKS]. Enforce the frozen LLM JSON schema. Degraded mode must never crash."*

**C:** *"Read APK-SENTINEL-REFERENCE.md §11, §12, §14. You own client/ (and android/ in Block 3). Current block: [TASKS]. While USE_MOCKS=true nothing may import from the network layer except api/client.js. Android work: follow §14 gotchas in order."*

---

*Sync this file's checkboxes during the event. When reality diverges from plan (it will), update THIS doc — it's the shared brain for three different AIs.*
