# ARGUS — Project Pitch Brief

> **For:** Teammate preparing the PPT.
> **What this is:** Everything you need to present Argus confidently — the problem, the solution, how it works, what makes it special, the exact words to use (buzzwords), the demo story, and likely judge questions with ready answers.
> **Rule of thumb:** speak in SIMPLE sentences, drop BOLD terms naturally. Don't memorize — understand the flow once and you can present any slide.

---

## 1. One-Liners (pick per audience)

- **Elevator (10 sec):** *"Argus is an AI-powered fraud shield that analyzes suspicious Android apps before they hurt anyone — giving bank investigators a full report in seconds, and blocking threats on the customer's phone before install."*
- **One word version:** *"Argus is the hundred-eyed watchman for Android apps."*
- **Formal version:** *"A Generative-AI-driven malware analysis platform that automates static and behavioral analysis of fraudulent APKs, produces explainable risk scores, and generates investigation-ready reports — deployed both as an analyst dashboard and as an on-device pre-install scanner."*

---

## 2. The Problem (Slide 2 material)

### The threat
- Fraudsters distribute **malicious APKs** (fake banking apps, loan apps, "gift" apps) through **WhatsApp, SMS phishing (smishing), email, and malicious links** — this is **social engineering** at scale.
- These apps are **banking trojans**: they steal credentials, **intercept OTPs** (one-time passwords) via SMS permissions, draw fake login screens over real apps (**overlay attacks**), and execute unauthorized transactions.
- Victims: bank customers. Cost: direct financial fraud + reputational damage to banks.

### Why current approaches fail
| Current approach | Why it's not enough |
|---|---|
| **Manual analysis** by security experts | Slow (hours–days), doesn't scale, requires rare skilled analysts |
| **Signature-based antivirus** | Only catches *known* malware; new variants evade via **obfuscation** and repackaging (**polymorphism**) |
| **Generic scanners (e.g., multi-engine upload sites)** | Give a "malicious/benign" label with **no explanation** — banks need evidence, attack chain, and IOCs to act |
| **Nothing at install time** | The customer's phone happily installs the trojan |

**The gap we fill:** fast, automated, *explainable* analysis — powered by **Generative AI** — that works at two points: the bank analyst's desk AND the moment of installation on the phone.

---

## 3. The Solution (Slide 3 material)

**Argus = one analysis engine, two shields.**

```
                    ┌────────────────────────┐
   Suspicious APK → │   ARGUS ANALYSIS ENGINE │ → Risk score + AI investigation report
                    └───────────┬────────────┘
              used by           │           used by
        ┌───────────────────────┴────────────────────────┐
        ▼                                                ▼
  BANK ANALYSTS (web dashboard)                 CUSTOMERS (Android scanner app)
  Deep reports, IOCs, recommendations           Instant RED/YELLOW/GREEN verdict
  Block hashes at gateways                      BEFORE the app gets installed
```

- **Analyst side:** drag-drop an APK → get a full investigation report: severity, attack chain in plain English, indicators of compromise, recommended actions.
- **Customer side:** taps a shady APK from WhatsApp → Argus intercepts it *before* installation → scans it against our engine → shows RED alert ("OTP stealer, do not install") in seconds. Safe apps pass through normally.

**Tagline options:** *"Intelligence at the core, protection at the edge."* · *"Every APK gets vetted."*

---

## 4. How It Works — The Flow (Slides 4–5 material)

### Step by step (say it like a story)

1. **Intake & fingerprinting** — APK uploaded (or intercepted on phone). We compute its **SHA-256 hash**. If we've seen it before → instant cached verdict. This is **hash-based deduplication**.
2. **Static analysis** — Without ever running the app, we dissect its package: requested **permissions**, exported components, receivers, certificates (**self-signed / debug-signed flags**), embedded payloads like nested APKs (**multi-stage droppers**). Think: reading the ingredients label and the recipe, without tasting the dish.
3. **Decompilation** — We convert the compiled bytecode (DEX) back into readable Java source using **reverse engineering** tooling (jadx).
4. **AI code-behavioral analysis (our GenAI layer)** — We rank the most suspicious code sections and feed them to a **Large Language Model (LLM)**, which reads the code like a human malware analyst would: *"This receiver silently deletes incoming SMS and forwards your OTP to a server at X.X.X.X."* It reconstructs the **attack chain**, extracts **Indicators of Compromise (IOCs)**, and maps findings to **MITRE ATT&CK Mobile** techniques (industry-standard threat taxonomy).
5. **Explainable risk scoring** — A weighted rules engine converts every finding into points. Every point in the final score traces back to a specific triggered rule — **no black box**. Score bands: SAFE → MEDIUM → HIGH → CRITICAL.
6. **Report generation** — GenAI writes the full investigation report: executive summary, score breakdown, permission table, IOC list, MITRE mapping, actionable recommendations (*"block this hash at the SMS gateway"*).
7. **Delivery** — Analyst sees it on the dashboard (PDF/markdown export). Phone user sees instant verdict. Banks can integrate the same engine via our **REST API** (gateway integration).

### Key architectural phrase to use
*"We combine deterministic static analysis with probabilistic AI reasoning — rules give us auditability, GenAI gives us comprehension."*

---

## 5. Feature List (Slide 6 material)

**Analysis Engine**
- Static analysis: permissions, manifest, components, certificates, embedded payloads
- Decompiled-code scanning: suspicious API call patterns (SMS interception, runtime code loading, reflection, crypto abuse)
- IOC extraction: C2 domains, IPs, URLs, phone numbers
- **AI-powered code behavioral analysis** — LLM reads decompiled code, explains behavior, builds attack chain *(note: deliberately NOT called "dynamic analysis" — that means running the app in an emulator)*
- Explainable weighted risk scoring (0–100, five severity bands)
- MITRE ATT&CK Mobile mapping
- Auto-generated investigation reports (markdown/PDF)

**Surfaces**
- Analyst web dashboard: drag-drop upload, live pipeline view, risk gauge, score breakdown ("why this score"), IOC tables, report export
- Android pre-install scanner: intercepts APK-open events, scans before install, RED/YELLOW/GREEN verdict, safe handoff to installer
- Hash cache for instant repeat verdicts + REST API for bank gateway integration

---

## 6. What Makes Us Different (Slide 7 — THE most important slide)

| Competing approach | Their weakness | Our edge |
|---|---|---|
| Manual security experts | Hours/days per sample, doesn't scale | **Seconds per scan**, expert-level first-pass report |
| Signature AV engines | Blind to new/unknown variants | Behavioral + AI reasoning catches **zero-day-style patterns**, not just known signatures |
| Existing open-source scanners (e.g., MobSF) | Raw technical findings, no narrative, no fraud context | **GenAI turns findings into a story**: who is targeted, how the fraud unfolds, what to do |
| Consumer antivirus on phones | Scans AFTER install, opaque verdicts | Argus acts **BEFORE install** with explainable reasons shown to the user |
| Generic risk scores | Black-box numbers | **Fully explainable scoring** — every point traceable to a rule (crucial for bank audits & compliance) |

**Three differentiators to hammer:**
1. **Explainability** — auditable scores, not black boxes (banks love compliance language).
2. **Dual-surface deployment** — same engine protects the institution AND the end customer at install-time.
3. **GenAI comprehension layer** — first tools tell you *what* was found; Argus tells you *what it means for fraud* and *what to do next*.

---

## 7. Buzzword Sheet (use these, know these)

| Term | One-line meaning |
|---|---|
| **APK** | Android application package — the installable file |
| **Static analysis** | Inspecting the app WITHOUT running it |
| **Dynamic analysis** | Running the app in a sandboxed emulator to watch behavior (we DON'T do this — say "code-behavioral analysis") |
| **Reverse engineering** | Converting compiled bytecode back into readable source |
| **IOC (Indicator of Compromise)** | Evidence artifacts: malicious domains, IPs, hashes, phone numbers |
| **C2 (Command & Control)** | The attacker's server that stolen data gets sent to |
| **Attack chain / kill chain** | Step-by-step story of how the fraud happens |
| **MITRE ATT&CK** | Industry-standard catalog of attacker techniques — mapping to it = credibility |
| **Banking trojan** | Malware disguised as legit app, steals banking credentials/OTPs |
| **Overlay attack** | Fake screen drawn over the real banking app to phish credentials |
| **Accessibility-service abuse** | Misusing Android's accessibility feature to read screens & steal input |
| **Dropper / multi-stage payload** | App whose job is only to download the REAL malware after install |
| **Typosquatting** | Package name imitating a legit app (`com.sbi.officia1`) |
| **Obfuscation** | Deliberately scrambling code/names to evade analysis |
| **Zero-day** | Threat with no existing signature/defense yet |
| **LLM / GenAI** | Large Language Model — reads code and writes human-grade analysis |
| **Structured output** | Forcing AI responses into strict JSON schemas — prevents hallucinated formats |
| **RAG (Retrieval-Augmented Generation)** | Grounding AI answers in a curated knowledge base (on our roadmap) |
| **Explainable AI (XAI)** | AI decisions you can audit — our rule-level score breakdown embodies this |
| **Risk scoring** | Weighted, transparent point system → severity band (SAFE→CRITICAL) |
| **Hash-based detection** | Fingerprinting files by cryptographic hash for instant re-identification |
| **Defense-in-depth** | Multiple protection layers (analyst + device + gateway) |
| **SOC (Security Operations Center)** | Bank team that would use the analyst dashboard |
| **False positive** | Benign app flagged as malicious — our benign control sample proves we minimize these |

---

## 8. Who Uses It & Why They Care (impact slide)

- **Bank SOC / fraud teams:** triage suspicious apps in seconds instead of hours; evidence-backed reports for takedowns and customer advisories; API hooks into their fraud gateways.
- **End customers:** invisible bodyguard at install time — the fraud is stopped before credentials are ever entered.
- **Regulators/compliance folks:** explainable, auditable decisions (every score decomposes into named rules).
- **Society angle (good closing note):** digital-fraud awareness is rising nationally; a deployable pre-install shield directly supports safer digital-banking adoption.

---

## 9. Demo Script (~90 seconds)

1. **(0:00)** Show a WhatsApp message with an APK from an unknown number. Tap it.
2. **(0:10)** Argus opens instead of the installer → scanning animation → **RED ALERT: "OTP-stealing banking trojan detected — do not install"** with plain-language reasons. *(crowd moment #1)*
3. **(0:30)** Cut to analyst dashboard: upload the same APK. Watch live pipeline stages tick.
4. **(0:45)** Verdict lands: CRITICAL 87/100. Open AI Analysis tab: attack chain narrated step-by-step, IOCs listed, MITRE techniques mapped. *(crowd moment #2)*
5. **(1:10)** Open Score Breakdown: "+30 OTP interception combo, +22 silent SMS deletion…" — *"every point is explained. Auditable, not a black box."*
6. **(1:25)** Close: *"One engine, two shields — the bank's SOC and the customer's pocket. And it's one REST API away from a bank's fraud gateway."*

**Backup plans (mention if asked / if demo gods are angry):** recorded video of the same flow · pre-generated report artifact · benign control sample proving GREEN verdicts work (no crying wolf).

---

## 10. Roadmap (future-work slide)

Phased honestly — what's shipped vs. what scales it:
- **Next:** Dynamic/emulated execution analysis (run app in sandboxed Android emulator, monitor network traffic & runtime APIs) · VirusTotal/threat-intel enrichment stage
- **Then:** Custom ML classifier trained on public malware datasets (Drebin, CICMalDroid) · **RAG** over curated fraud-pattern knowledge base for even more grounded AI verdicts
- **Platform:** bank gateway SDK, hash-blocklist sharing network between banks, JWT-signed verdicts for tamper-proof phone responses, multi-tenant dashboard with auth/RBAC

*(Frame current scope as deliberate MVP focus: "we built the highest-value layer first — automated expert-level comprehension.")*

---

## 11. Judge Questions — Ready Answers

**Q: "Isn't this just VirusTotal?"**
> VirusTotal aggregates labels from AV engines — opaque and binary. Argus explains: attack chain, IOCs, MITRE mapping, and a decomposable risk score. Plus we act at install-time on-device, which VT doesn't.

**Q: "How do you stop the LLM from hallucinating?"**
> Three guards: the model only receives actual extracted evidence (decompiled methods + static findings); its output is forced into a strict JSON schema validated programmatically; and confidence is reported — inconclusive evidence yields low confidence, not invention. Rules-based scoring runs independently, so the verdict floor never depends on the LLM.

**Q: "Why no dynamic analysis? Real sandboxes run the app."**
> Correct — that's phase 2. Our AI code-behavioral analysis approximates runtime insight statically: reading code paths to infer behavior. It's faster, needs no emulator farm, and avoids anti-emulation evasion. We're explicit about the tradeoff.

**Q: "What about false positives?"**
> We ship a benign control sample that must score SAFE — calibrated thresholds, and every flag is user-visible so a human always has final say. The system assists analysts; it doesn't replace judgment.

**Q: "Is uploading APKs to your server a privacy problem?"**
> Deployment-wise the engine is containerized and bank-hostable on-prem; the phone client sends file content only for scanning over TLS, and hash lookups avoid uploads entirely for previously seen files.

**Q: "Where did you get malware samples?"**
> Public research repositories (MalwareBazaar) for testing, plus we built our own controlled proof-of-concept sample in-house — reproducible, legal, offline-safe.

**Q: "Why 'Argus'?"**
> Argus Panoptes — the giant with a hundred eyes, the mythical watchman. A fitting name for something that watches every app from every angle.

---

## 12. Suggested Deck Outline (10 slides)

1. **Title** — ARGUS + tagline + team
2. **Problem** — fraud-APK landscape; manual analysis can't scale (§2 table condensed to 2 rows)
3. **Solution** — one engine, two shields diagram (§3)
4. **How it works** — the 7-step flow, heavily simplified icons (§4 steps 1–4)
5. **How it works contd.** — scoring + report generation (§4 steps 5–7), show mini score-breakdown visual
6. **Features** — engine column + surfaces column (§5)
7. **Differentiation** — §6 table, top 3 edges bolded
8. **Live demo** — one screenshot + "watch this"
9. **Impact & architecture fit** — who uses it; "REST-API ready for bank gateways"; explainability/compliance note (§8)
10. **Roadmap + close** — phased future (§10), tagline repeat, QR/link to repo

Design tips: dark theme, red/green verdict colors carry the story, minimal text per slide (you talk, slides don't), reuse the score-breakdown screenshot everywhere — it IS the explainability story.

---

*Companion docs in repo: `APK-SENTINEL-REFERENCE.md` (full technical spec) · `TEAM-WORKPLAN.md` (build plan). If a judge asks something deeper than this brief — the answer lives in the Reference doc.*
