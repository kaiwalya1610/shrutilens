from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class AssessmentMode(StrEnum):
    clinical_locked = "clinical_locked"
    research_flexible = "research_flexible"


class SessionStatus(StrEnum):
    in_progress = "in_progress"
    awaiting_confirmation = "awaiting_confirmation"
    safety_interrupted = "safety_interrupted"
    completed = "completed"


class ResponseAnchor(BaseModel):
    id: str
    label: str
    score: int | float | None = None
    utterance_patterns: list[str] = Field(default_factory=list)


class SafetyHook(BaseModel):
    kind: Literal["score_threshold", "anchor_match", "keyword"]
    item_id: str | None = None
    anchor_ids: list[str] = Field(default_factory=list)
    threshold: int | float | None = None
    keywords: list[str] = Field(default_factory=list)
    severity: Literal["low", "moderate", "high", "crisis"] = "high"
    message: str


class AssessmentItem(BaseModel):
    id: str
    text: str
    response_type: str
    required: bool = True
    locked_wording: bool = True
    anchors: list[ResponseAnchor] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    max_followups: int = 0


class ScoringConfig(BaseModel):
    method: Literal["sum", "none", "custom"] = "none"
    severity_bands: list[dict[str, Any]] = Field(default_factory=list)


class PackPolicy(BaseModel):
    paraphrasing_allowed: bool = False
    adaptive_followup_allowed: bool = False
    confirmation_required: Literal["always", "low_confidence", "never"] = "low_confidence"
    confidence_threshold: float = 0.78


class AssessmentPack(BaseModel):
    id: str
    version: str
    title: str
    mode: AssessmentMode
    language: str = "en"
    licensing: str
    consent: str
    disclaimer: str
    items: list[AssessmentItem]
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    safety_hooks: list[SafetyHook] = Field(default_factory=list)
    policy: PackPolicy = Field(default_factory=PackPolicy)
    export_schema: dict[str, Any] = Field(default_factory=dict)


class NormalizedAnswer(BaseModel):
    item_id: str
    raw_text: str
    anchor_id: str | None = None
    value: str | int | float | bool | None = None
    confidence: float
    source: Literal["deterministic", "llm", "manual"] = "deterministic"
    needs_confirmation: bool = False


class TurnRecord(BaseModel):
    speaker: Literal["system", "assistant", "user"]
    text: str
    item_id: str | None = None
    event: str = "turn"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScoreResult(BaseModel):
    total: int | float | None = None
    severity: str | None = None
    detail: dict[str, int | float] = Field(default_factory=dict)


class SafetyEvent(BaseModel):
    hook_kind: str
    severity: str
    item_id: str | None
    message: str
    evidence: str


class SessionState(BaseModel):
    id: str
    pack_id: str
    status: SessionStatus = SessionStatus.in_progress
    current_index: int = 0
    responses: list[NormalizedAnswer] = Field(default_factory=list)
    pending_answer: NormalizedAnswer | None = None
    score: ScoreResult | None = None
    safety_events: list[SafetyEvent] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
