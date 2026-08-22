"""
models.py — SQLAlchemy ORM model for the Scan table.
Schema exactly matches APK-SENTINEL-REFERENCE.md §6.
JSON blobs stored as text columns — intentional for hackathon speed.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Scan(Base):
    __tablename__ = "scans"

    # Primary key — uuid4 hex string
    id: Mapped[str] = mapped_column(String, primary_key=True)

    # Status machine: queued | static_analysis | decompiling | pattern_scanning |
    #                 ioc_extraction | scoring | ai_analysis | completed | failed
    status: Mapped[str] = mapped_column(String, default="queued")

    # File fingerprint
    sha256: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    md5: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    original_filename: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Static results (JSON-encoded strings)
    app_metadata: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    certificate: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    permissions: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    components: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    manifest_flags: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    pattern_hits: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    iocs: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    embedded_payloads: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Scores
    rule_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    final_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    fraud_category: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # AI layer
    ai_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ai_analysis: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    report_markdown: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Meta
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Progress hint shown to polling clients
    progress_hint: Mapped[Optional[str]] = mapped_column(String, nullable=True)
