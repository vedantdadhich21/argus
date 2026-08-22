#!/usr/bin/env bash
# clear_cache.sh — Wipe all scan history, stored APKs, and decompiled output.
# Run from the server/ directory: ./scripts/clear_cache.sh
# Optional: pass a SHA256 to delete only one APK's scans:
#   ./scripts/clear_cache.sh 0b368d90f6016743...

set -e
cd "$(dirname "$0")/.."

source .venv/bin/activate 2>/dev/null || true

if [ -n "$1" ]; then
  # Delete a single APK's scans by SHA256
  python3 - <<EOF
import hashlib, sys
from app.database import SessionLocal
from app.models import Scan
sha256 = "$1"
db = SessionLocal()
n = db.query(Scan).filter(Scan.sha256 == sha256).delete()
db.commit()
db.close()
print(f"Deleted {n} scan(s) for SHA256: {sha256}")
EOF
else
  # Full wipe
  python3 - <<EOF
from app.database import SessionLocal
from app.models import Scan
db = SessionLocal()
n = db.query(Scan).delete()
db.commit()
db.close()
print(f"Deleted all {n} scan(s) from database.")
EOF

  # Also wipe stored APKs and decompiled output
  rm -rf storage/apks/* storage/decompiled/* storage/reports/* 2>/dev/null || true
  echo "Cleared storage/apks/, storage/decompiled/, storage/reports/"
fi

echo "Cache cleared. Upload fresh files in the dashboard."
