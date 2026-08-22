"""
schemas.py — Pydantic v2 request/response schemas.
API shapes frozen per APK-SENTINEL-REFERENCE.md §6, §9, §11.
DO NOT add fields not present in the Reference doc.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Scan upload / initiation
# ---------------------------------------------------------------------------

class ScanCreateResponse(BaseModel):
    """Response from POST /api/scan (Reference §11)."""
    scan_id: str


# ---------------------------------------------------------------------------
# Scan poll responses
# ---------------------------------------------------------------------------

class ScanInProgressResponse(BaseModel):
    """Returned while status is a working state."""
    scan_id: str
    status: str
    progress_hint: Optional[str] = None


class TriggerDetail(BaseModel):
    rule_id: str
    description: Optional[str] = None
    weight: int
    evidence: Optional[str] = None


class PermissionDetail(BaseModel):
    name: str
    danger_level: str  # dangerous | normal | signature | unknown


class ComponentDetail(BaseModel):
    name: str
    type: str           # activity | service | receiver | provider
    exported: bool


class AttackChainStep(BaseModel):
    step: int
    title: str
    detail: str
    evidence: List[str] = []


class MitreTechnique(BaseModel):
    id: str
    name: str
    reason: str


class AiAnalysisSchema(BaseModel):
    """Mirrors the frozen LLM output schema from Reference §9."""
    fraud_category: Optional[str] = None
    confidence: Optional[str] = None
    behavior_summary: Optional[str] = None
    attack_chain: List[AttackChainStep] = []
    iocs: Optional[Dict[str, List[str]]] = None
    mitre_techniques: List[MitreTechnique] = []
    recommendations: List[str] = []


class ScanCompletedResponse(BaseModel):
    """Full result returned when status == 'completed' or 'failed'."""
    scan_id: str
    status: str
    progress_hint: Optional[str] = None

    # File fingerprint
    sha256: Optional[str] = None
    md5: Optional[str] = None
    file_size_bytes: Optional[int] = None
    original_filename: Optional[str] = None

    # Static results (deserialized)
    app_metadata: Optional[Dict[str, Any]] = None
    certificate: Optional[Dict[str, Any]] = None
    permissions: Optional[List[PermissionDetail]] = None
    components: Optional[List[ComponentDetail]] = None
    manifest_flags: Optional[Dict[str, Any]] = None
    pattern_hits: Optional[List[Dict[str, Any]]] = None
    iocs: Optional[Dict[str, List[str]]] = None
    embedded_payloads: Optional[Dict[str, Any]] = None

    # Scores
    rule_score: Optional[int] = None
    final_score: Optional[int] = None
    severity: Optional[str] = None
    fraud_category: Optional[str] = None

    # AI layer
    ai_status: Optional[str] = None
    ai_analysis: Optional[AiAnalysisSchema] = None
    triggers: Optional[List[TriggerDetail]] = None
    report_markdown: Optional[str] = None

    # Meta
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Hash lookup (fast path — Android app)
# ---------------------------------------------------------------------------

class HashLookupRequest(BaseModel):
    sha256: str
    md5: Optional[str] = None


class HashLookupResponse(BaseModel):
    known: bool
    scan_id: Optional[str] = None
    severity: Optional[str] = None
    final_score: Optional[int] = None
    fraud_category: Optional[str] = None


# ---------------------------------------------------------------------------
# History list
# ---------------------------------------------------------------------------

class ScanSummary(BaseModel):
    scan_id: str
    original_filename: Optional[str] = None
    final_score: Optional[int] = None
    severity: Optional[str] = None
    fraud_category: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None


class ScansListResponse(BaseModel):
    scans: List[ScanSummary]
    total: int


# ---------------------------------------------------------------------------
# Stats strip (dashboard hero)
# ---------------------------------------------------------------------------

class StatsResponse(BaseModel):
    total_scans: int
    malicious_found: int
    avg_duration_ms: Optional[float] = None
    unique_hashes: int
