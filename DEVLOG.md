# DEVLOG — Shared Handoff Journal

Append-only journal. **Newest entries go at the TOP** of the Entries section.

Rule: before starting any work, read the last 2–3 entries. After finishing a work block (or a checkpoint merge), your AI appends one entry. This is how three people running three different AIs stay synchronized without meetings.

## Entry format

```
### [H+X.Xh · Block N] Owner — branch-name
- Did: what was built/changed (file paths)
- How: key decisions, architecture notes, anything non-obvious
- Gotchas: traps discovered that the next person/AI must know
- Next: what remains / handoff point
```

Keep entries ≤ 15 lines. Link to commits where useful. Checkpoint merges (CP1/CP2) get an entry from every owner.

---

## Entries

### [Checkpoint 4 · All] Unified Rebrand to Argus: Mobile Threat Defense & Cybersecurity Intelligence — main
- Did: Rebranded entire repository, Web Dashboard, Android App, and Threat Reports to **Argus** (Next-Gen Mobile Threat Intelligence & Malware Defense).
- How: Removed bank-only niche terminology and broadened scope across LLM system prompts, UI cards, API references, Android strings (`res/values/strings.xml` → "Argus"), and PDF/Markdown report headers.
- Verification: `npm run build` completed cleanly in 1.7s. `./gradlew assembleDebug` passed in 8s. All backend endpoints verified.

### [Checkpoint 3 · A] Combo-gated scoring: fixes false positives on legit large apps — main
- Did: Rewrote `rules_engine.py` scoring to gate code+IOC rule weights on high-risk permission presence. `static_analysis.py` allowlists known SDK dex files (Facebook Audience Network etc) in assets/. `rules.yaml` META_SELF_SIGNED weight 6→3.
- How: If NO high-risk perm rule fires (SMS combo, Accessibility, Overlay, Install, Device Admin), all code+IOC signals are dampened to 30%. "Self-sufficient" code rules (abortBroadcast, Runtime.exec, SmsForward) always count at full weight — no legit app uses these.
- Gotchas: Meesho APKPure v1.2 scored 100 because (a) re-signed by APKPure with random cert, (b) Facebook Audience Network ships `assets/audience_network.dex` which falsely triggered META_NESTED_DEX. After fix: Meesho=8 LOW, fake_banker=100 CRITICAL, benign_notes=13 LOW.
- Next: Scanner is well-calibrated for hackathon demo. No further tuning needed unless judges bring their own APKs.

### [Checkpoint 2 · All] Merged c/frontend into main: Native Android Scanner App + Live Groq AI + PDF Reports — main
- Did: Merged Person C's Android Sentinel Shield client (`Models.kt`, `SentinelClient.kt`, `InstallHandoff.kt`, `Screens.kt`, Compose RYG verdict UI, and `usesCleartextTraffic`) into `main`. Unified dashboard with live PDF report export and offline degradation banners.
- Verification: `./gradlew assembleDebug` builds clean APK in ~18s. `npm run build` succeeds with 0 errors. All 9 automated backend tests in `smoke.sh` pass with live Groq LLM inference.
- Next: Block 4 Deployment & demo rehearsal.

### [H+8.0h · Block 2/3] Person C — c/frontend
- Did: Complete Android Sentinel Shield app built in `android/` (`Models.kt`, `SentinelClient.kt`, `InstallHandoff.kt`, `Screens.kt`, updated `MainActivity.kt`, enabled `usesCleartextTraffic`). Enhanced Web Dashboard in `client/` (`ScanDetail.jsx` AI degradation banner, IOC copy cells, history filters).
- How: Native HTTP client streams APK multipart and calculates SHA-256/MD5 for fast-path hash check (`POST /api/lookup/hash`). Full Jetpack Compose RYG VerdictScreen with install handoff for safe APKs and block actions for critical/banking malware.
- Gotchas: Added `android:usesCleartextTraffic="true"` for LAN/IP testing; `local.properties` configured for Windows Android SDK. Verified `./gradlew assembleDebug` (21s) and `npm run build` both build clean.
- Next: Checkpoint 2 (CP2) full end-to-end integration testing with backend on LAN/WiFi.

### [Block 2/3 · A+B] Created demo APKs (fake_banker & benign_notes), PDF export, framework false positive filter — main
- Did: Built two dedicated demo APK modules in `android/samples/`: `fake_banker.apk` (SMS intercept, abortBroadcast, DexClassLoader, Accessibility, Overlay, nested payload) and `benign_notes.apk` (clean single-permission note app). Added ReportLab-based PDF report generation in `report_generator.py` and `GET /api/scan/{id}/report?format=pdf`. Added PDF export button in UI.
- How: Fixed nested DEX check in `static_analysis.py` (only flags DEX inside `assets/` or `res/`, not root `classes.dex`). Fixed `pattern_scanner.py` and `method_selector.py` to filter AndroidX/framework library classes so innocent apps aren't false-positived by AndroidX internal code.
- Verification: `fake_banker.apk` scores **100 (CRITICAL)** in ~17s; `benign_notes.apk` scores **16 (LOW/SAFE)** in ~18s. All 9 automated tests in `smoke.sh` pass including PDF export validation.
- Next: Checkpoint 2 testing with Android client. Set `LLM_API_KEY` in `server/.env` whenever live LLM inference is needed.

### [H+3.5h · Block 1] Person C — c/frontend
- Did: Full dashboard scaffolded in `client/` (Vite, React 18, Tailwind CSS, TanStack Query v5, Axios, React Router v6). Built all pages (Home, ScanDetail, History, ApiDocs) & components (Dropzone, RiskGauge, VerdictCard, PipelineStatus, ScoreBreakdown, PermissionTable, AttackChain, IocTable, MitreList, AiFindings).
- How: Mapped against frozen fixture `client/src/mocks/scanResponse.json` (§11). `VITE_USE_MOCKS=true` simulates artificial pipeline delays without needing backend.
- Gotchas: Node.js PATH issue on Windows resolved by user-level PATH setx; production build verified clean via `npm run build`.
- Next: Block 2 (History + stats mock polish) → Checkpoint 1 integration.

### [Block 1+2 · A] Backend pipeline stages 1–6 complete — a/backend
- Did: built all 14 Person A files from scratch: `config.py`, `database.py`, `models.py`, `schemas.py`, `main.py`, `routers/scans.py`, `services/storage.py`, `services/static_analysis.py`, `services/decompiler.py`, `services/pattern_scanner.py`, `services/ioc_extractor.py`, `services/rules_engine.py`, `services/pipeline.py`, `data/rules.yaml`, `data/legit_banking_packages.json`
- How: FastAPI app with CORS + startup (creates storage dirs + SQLite tables). Pipeline runs in BackgroundTasks with per-stage status updates to DB. Stages 7–8 use import guards (graceful degradation if Person B's files absent). CLI entry point at `python -m app.services.pipeline --sample <apk>` for standalone testing.
- Gotchas: (1) `androguard==3.3.5` `get_certificates_v3/v2` fallback chain needed — pin the version. (2) jadx outputs partial results on non-zero exit (still usable); check `.java` file count not return code. (3) `check_same_thread=False` mandatory for SQLite + FastAPI threading. (4) `pattern_hits` column doubles as trigger storage (merged after scoring) — Person C must deserialize the whole list for ScoreBreakdown.
- Next: Person B wires `ai_analyst.py` + `report_generator.py` (already import-guarded in pipeline.py). CP1: flip `VITE_USE_MOCKS=false` on C's dashboard, upload `samples/fake_banker.apk`, confirm CRITICAL verdict appears.

### [Pre-hackathon · Block 0] ✅ RISK SPIKE PASSED — main
- Did: tested on physical device (Nothing A015, wireless debugging). Tapped a real .apk in Files app → chooser offered "Sentinel Shield" → Logcat `tag:Sentinel` shows full chain: `intercepted URI: content://com.google.android.apps.nbu.files.provider/…` → `read 17534594 bytes` (= exactly 17.53 MB decimal, matches file listing) → `zip magic=[80, 75]`. Interception + ContentResolver streaming both confirmed.
- How: §14 manifest filter registered first try; no fallback needed — native phone flow is GO for Block 3. Byte count matching the visible file size doubles as a read-integrity check.
- Gotchas: vendor noise on Nothing OS logs lines tagged with package name (`sentinel.shield`) e.g. `legacy_receive_flag`, `perfmgr_sbe` — harmless, filter with `tag:Sentinel` to exclude. When real ScanActivity lands: handle re-entry via onNewIntent if activity already alive (spike only logs in onCreate).
- Next: Block 0 exit criteria green for C's track. Tomorrow: git init + branches + first commit, LLM key into server/.env, teammates clone + run setup scripts.

### [Pre-hackathon · Block 0] Risk spike wired — main
- Did: tested on physical device (wireless debugging). Tapped a random .apk in Files app → **chooser offered "Sentinel Shield"** → app opened via VIEW intent. Interception mechanism confirmed working end-to-end at the OS level.
- How: §14 manifest filter registered correctly; no fallback needed — native phone flow is GO for Block 3. Remaining micro-check (optional): Logcat tag `Sentinel` should show `intercepted URI: content://…` + byte count + zip magic `[80, 75]`.
- Gotchas: none hit — filter worked first try on modern Android. Note for C: when real ScanActivity lands, handle possible re-entry (onNewIntent) if activity already alive; current spike only logs in onCreate.
- Next: Block 0 exit criteria now green for C's track. Tomorrow: git init + branches, LLM key into server/.env, teammates run setup scripts.

### [Pre-hackathon · Block 0] Risk spike wired — main
- Did: added §14 intent-filter (`VIEW` + content/file schemes + `application/vnd.android.package-archive`) and `INTERNET`/`REQUEST_INSTALL_PACKAGES` permissions to `AndroidManifest.xml`. Added temporary spike logging in `MainActivity.logIncomingApk()` (tag `Sentinel`: logs intercepted URI, byte count, zip magic). Verified `./gradlew assembleDebug` builds clean.
- How: spike reads via `contentResolver.openInputStream(uri)` per §14 gotcha — never `File(path)`. Zip magic check `[80, 75]` = "PK". Test file = our own debug APK pushed to `/sdcard/Download/test.apk`.
- Gotchas: octet-stream mime intentionally NOT in the filter yet (would hijack every file open — §14 says sniff magic bytes later instead). Remove/replace the log code when real ScanActivity lands.
- Next: human must run on physical phone (USB debugging → Run ▶ → open test.apk from Files → check Logcat `Sentinel`). PASS = chooser shows Sentinel Shield + URI logged. FAIL after ~40 min = trigger browser fallback (§5).

### [H+0h · Block 0] Setup — main
- Did: generated SentinelShield project in Android Studio (`~/AndroidStudioProjects/SentinelShield`) and moved it into `android/` via rsync, excluding `local.properties`, `.gradle`, `.idea`, `build`.
- How: verified `minSdk = 26` ✓, namespace/applicationId `com.sentinel.shield` ✓ (matches Reference §4 tree). Template is **Compose** ("Empty Activity") — spec §2 prefers plain XML Views for speed but Compose is explicitly optional/allowed; Person C decides before writing real screens.
- Gotchas: manifest currently has ONLY the launcher intent-filter — the §14 APK-interception filter (`VIEW` + `application/vnd.android.package-archive`) and `INTERNET`/`REQUEST_INSTALL_PACKAGES` permissions are still missing = exactly Person C's Block 0 risk spike. `local.properties` deliberately not committed (machine-specific); AS regenerates it on first open. Old placeholder skeleton dirs were deleted during the move.
- Next: open repo `android/` folder in Android Studio → Gradle sync → add §14 intent-filter + permissions → test interception with a random .apk.

### [H+0h · Block 0] Setup — main
- Did: added Windows twin `setup.ps1` (winget-based); README quick start now covers both macOS and Windows.
- How: mirrors `setup.sh` logic. winget ids: `Git.Git`, `OpenJS.NodeJS.LTS`, `Python.Python.3.12`, `Google.AndroidStudio`, `Docker.DockerDesktop`. jadx has no official winget package → script prints manual install steps (matches Reference §15 non-mac path). venv differs: `.venv\Scripts\` not `.venv/bin/`.
- Gotchas: winget needs "App Installer" from MS Store; after installing python/node, PATH needs a **new terminal** before commands resolve; PowerShell may need `-ExecutionPolicy Bypass`. Backend can alternatively run identically on both OSes via `docker compose up --build` — best parity option if Windows setup fights back.
- Next: unchanged.

### [H+0h · Block 0] Setup — main
- Did: full folder skeleton per Reference §4; `.gitignore`; `AGENTS.md`; `DEVLOG.md` (this file); `README.md`; `server/.env.example` + `client/.env.example` (§5 values); `server/samples/README.md` safety warning; `__init__.py` files; `server/requirements.txt`; root `setup.sh` bootstrap.
- How: dirs mirror Reference §4 exactly so each owner drops code into place. `server/storage/` fully gitignored (runtime artifacts only). `android/` holds just the package path — the real Gradle skeleton must be generated by Android Studio into that folder.
- Gotchas: androguard pinned to 3.3.5 (4.x broke APIs, §15); PyYAML added to requirements for `rules.yaml`; client npm step is skipped by setup.sh until Person C scaffolds Vite (`client/package.json` gate). Android Studio cask install still needs its first-run GUI wizard for SDK/licenses.
- Next: `git init` + branches (`a/backend`, `b/genai`, `c/frontend`); Person C's intent-filter risk spike (Block 0).

<!-- newest first -->
