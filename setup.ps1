<#
APK Sentinel — one-shot dev environment bootstrap (Windows).
Idempotent: safe to re-run; anything already present is skipped.

Usage:
  powershell -ExecutionPolicy Bypass -File .\setup.ps1
  powershell -ExecutionPolicy Bypass -File .\setup.ps1 -WithAndroid    # + Android Studio
  powershell -ExecutionPolicy Bypass -File .\setup.ps1 -WithDocker     # + Docker Desktop

Notes:
  - Uses winget (preinstalled on Win11 / updated Win10). If missing: install "App Installer" from the Microsoft Store.
  - jadx has no official winget package — script prints manual install steps (Reference §15).
#>
param(
  [switch]$WithAndroid,
  [switch]$WithDocker
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

function Say($m)  { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "  ok $m" -ForegroundColor Green }
function Warn($m) { Write-Host "  !! $m" -ForegroundColor Yellow }

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
  Write-Host "winget not found. Install 'App Installer' from the Microsoft Store, then re-run." -ForegroundColor Red
  exit 1
}

function Install-Winget([string]$Id) {
  # winget itself is idempotent: reports "already installed" and exits cleanly
  Say "Ensuring $Id (winget)"
  winget install --id $Id --exact --silent --accept-source-agreements --accept-package-agreements | Out-Null
  if ($LASTEXITCODE -ne 0) { Warn "$id winget install returned $LASTEXITCODE — check manually" } else { Ok $Id }
}

# --- Core toolchain -----------------------------------------------------------
Say "Core toolchain"

if (Get-Command git -ErrorAction SilentlyContinue) { Ok "git" } else { Install-Winget "Git.Git" }

if (Get-Command node -ErrorAction SilentlyContinue) { Ok "node ($(node -v))" } else { Install-Winget "OpenJS.NodeJS.LTS" }

$pyOk = $false
if (Get-Command python -ErrorAction SilentlyContinue) {
  $v = (& python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null)
  if ($v -match '^(\d+)\.(\d+)$' -and ([int]$Matches[1]) -ge 3 -and ([int]$Matches[2]) -ge 11) { $pyOk = $true; Ok "python ($v)" }
}
if (-not $pyOk) { Install-Winget "Python.Python.3.12"; Warn "If 'python' isn't found in THIS shell, open a new terminal (PATH refresh)" }

if (Get-Command jadx -ErrorAction SilentlyContinue) {
  Ok "jadx available"
} else {
  Warn "jadx not found — no official winget package. Manual install (one time):"
  Write-Host "     1. Download jadx zip: https://github.com/skylot/jadx/releases"
  Write-Host "     2. Extract to e.g. C:\tools\jadx"
  Write-Host "     3. Add C:\tools\jadx\bin to your PATH (Environment Variables), reopen terminal"
  Write-Host "     Until then the decompiler stage degrades gracefully (Reference §15)."
}

# --- Backend ------------------------------------------------------------------
Say "Backend: venv + pip deps (server/)"
Push-Location "$Root\server"
try {
  if (-not (Test-Path ".venv")) { python -m venv .venv }
  & ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
  & ".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
  Ok "Backend deps installed"
  if (Test-Path ".env") { Ok "server/.env exists" }
  else { Copy-Item .env.example .env; Warn "Created server/.env — fill LLM_API_KEY before scanning" }
} finally { Pop-Location }

# --- Client ---------------------------------------------------------------------
Say "Dashboard client (client/)"
if (Test-Path "$Root\client\package.json") {
  Push-Location "$Root\client"
  try {
    if (-not (Test-Path ".env")) { Copy-Item .env.example .env; Ok "Created client/.env" }
    npm install
    Ok "npm deps installed"
  } finally { Pop-Location }
} else {
  Warn "client/package.json doesn't exist yet (Person C scaffolds Vite in Block 1) — skipping npm install"
}

# --- Optional apps ---------------------------------------------------------------
if ($WithAndroid) {
  Say "Android Studio"
  Install-Winget "Google.AndroidStudio"
  Warn "First launch of Android Studio still requires the GUI setup wizard (SDK + license acceptance)"
}

if ($WithDocker) {
  Say "Docker Desktop"
  if (Get-Command docker -ErrorAction SilentlyContinue) { Ok "already installed" } else { Install-Winget "Docker.DockerDesktop" }
  Warn "Launch Docker Desktop once after install to finish setup (WSL2 backend)"
}

# --- Summary ----------------------------------------------------------------------
Write-Host ""
Write-Host "Setup complete. Next steps:" -ForegroundColor Green
Write-Host "  backend : cd server ; .venv\Scripts\Activate.ps1 ; uvicorn app.main:app --reload --port 8000"
Write-Host "  client  : cd client ; npm run dev            (after C scaffolds Vite)"
Write-Host "  android : open android\ in Android Studio    $(if ($WithAndroid) {'(installed)'} else {'(run with -WithAndroid if needed)'})"
