"""
main.py — FastAPI application factory.
Mounts CORS middleware, health endpoint, and API routers.
Creates DB tables on startup.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import create_tables
from app.routers import scans

settings = get_settings()

app = FastAPI(
    title="Argus",
    description="Automated Mobile Threat Intelligence & Malware Reverse-Engineering Platform",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=".*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    # Ensure storage directories exist
    for sub in ("apks", "decompiled", "reports"):
        os.makedirs(os.path.join(settings.storage_dir, sub), exist_ok=True)
    # Create DB tables (idempotent)
    create_tables()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "service": "apk-sentinel"}


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(scans.router, prefix="/api")
