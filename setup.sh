#!/usr/bin/env bash
#
# APK Sentinel — one-shot dev environment bootstrap (macOS).
# Idempotent: safe to run repeatedly; anything already present is skipped.
#
# Usage:
#   ./setup.sh                  # core: brew, python, node, jadx, backend venv, client env
#   ./setup.sh --with-android   # also install Android Studio (large download)
#   ./setup.sh --with-docker    # also install Docker Desktop (recommended: analysis isolation)

set -euo pipefail

WITH_ANDROID=false
WITH_DOCKER=false
for arg in "$@"; do
  case "$arg" in
    --with-android) WITH_ANDROID=true ;;
    --with-docker) WITH_DOCKER=true ;;
    *) echo "Unknown option: $arg"; exit 1 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

say()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m  ok %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m  !! %s\033[0m\n' "$*"; }

# --- Homebrew ---------------------------------------------------------------
if ! command -v brew >/dev/null 2>&1; then
  say "Homebrew missing — installing"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  ok "Homebrew"
fi

have_brew_pkg() { brew list --formula "$1" >/dev/null 2>&1; }
ensure_tool() { # $1=brew pkg  $2=bin to check
  if command -v "$2" >/dev/null 2>&1 || have_brew_pkg "$1"; then ok "$1"; else say "Installing $1"; brew install "$1"; fi
}

say "Core toolchain"
ensure_tool git git
ensure_tool node node
ensure_tool jadx jadx

if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
  ok "python3 ($(python3 -V))"
else
  say "Installing python 3.12 (need >= 3.11)"
  brew install python@3.12
fi

# --- Backend ------------------------------------------------------------------
say "Backend: venv + pip deps (server/)"
cd "$ROOT/server"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet -r requirements.txt
ok "Backend deps installed"
if [ ! -f .env ]; then cp .env.example .env; warn "Created server/.env — fill LLM_API_KEY before scanning"; else ok "server/.env exists"; fi

if command -v jadx >/dev/null 2>&1; then
  ok "jadx available ($(jadx --version 2>/dev/null | head -1))"
else
  warn "jadx still missing — decompiler stage will degrade gracefully (see Reference §15)"
fi

# --- Client ---------------------------------------------------------------------
say "Dashboard client (client/)"
if [ -f "$ROOT/client/package.json" ]; then
  cd "$ROOT/client"
  [ -f .env ] || { cp .env.example .env; ok "Created client/.env"; }
  npm install
  ok "npm deps installed"
else
  warn "client/package.json doesn't exist yet (Person C runs Vite scaffold in Block 1) — skipping npm install"
fi

# --- Optional apps ----------------------------------------------------------------
if [ "$WITH_ANDROID" = true ]; then
  say "Android Studio"
  if [ -d "/Applications/Android Studio.app" ]; then ok "already installed"
  else brew install --cask android-studio; warn "First launch of Android Studio still requires the GUI setup wizard (SDK + platform tools accept licenses)" ; fi
fi

if [ "$WITH_DOCKER" = true ]; then
  say "Docker Desktop"
  if command -v docker >/dev/null 2>&1; then ok "already installed"
  else brew install --cask docker; warn "Launch Docker Desktop once to finish setup"; fi
fi

# --- Summary ----------------------------------------------------------------------
printf '\n\033[1;32mSetup complete. Next steps:\033[0m\n'
printf '  backend : cd server && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000\n'
printf '  client  : cd client && npm run dev            (after C scaffolds Vite)\n'
printf '  android : open android/ in Android Studio     (%s)\n' \
  "$([ "$WITH_ANDROID" = true ] && echo 'installed' || echo 'run ./setup.sh --with-android if needed')"
