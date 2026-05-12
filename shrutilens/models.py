from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class AssessmentMode(StrEnum):
    clinical_locked = "clinical_locked"
    research_flexible = "research_flexible"


class SessionStatus(StrEnum):
    in_progress = "in_progress"
    awaiting_confirmation = "awaiting_confirmation"
    needs_clarification = "needs_clarification"
    safety_interrupted = "safety_interrupted"
    completed = "completed"


class ResponseType(StrEnum):
    choice = "choice"
    multi_select = "multi_select"
    numeric = "numeric"
    rating = "rating"
    open_text = "open_text"
    boolean = "boolean"


class ResponseAnchor(BaseModel):
    id: str
    label: str
    score: int | float | None = None
    value: str | int | float | bool | None = None
    utterance_patterns: list[str] = Field(default_factory=list)


class BranchRule(BaseModel):
    id: str
    item_id: str
    operator: Literal["equals", "not_equals", "in", "gte", "lte", "gt", "lt"]
    value: Any
    goto: str


class SafetyHook(BaseModel):
    id: str
    kind: Literal["anchor_match", "score_threshold", "keyword"]
    item_id: str | None = None
    anchor_ids: list[str] = Field(default_factory=list)
    threshold: int | float | None = None
    keywords: list[str] = Field(default_factory=list)
    severity: Literal["low", "moderate", "high", "crisis"] = "high"
    interrupt: bool = True
    message: str


class AssessmentItem(BaseModel):
    id: str
    text: str
    response_type: ResponseType
    required: bool = True
    locked_wording: bool = False
    anchors: list[ResponseAnchor] = Field(default_factory=list)
    allow_skip: bool = False
    max_followups: int = 0
    tags: list[str] = Field(default_factory=list)


class SeverityBand(BaseModel):
    min: int | float
    max: int | float
    label: str


class ScoringConfig(BaseModel):
    method: Literal["none", "sum"] = "none"
    severity_bands: list[SeverityBand] = Field(default_factory=list)


class PackPolicy(BaseModel):
    paraphrasing_allowed: bool = False
    adaptive_followup_allowed: bool = False
    clarification_on_ambiguous: bool = True
    confirmation_required: Literal["always", "low_confidence", "never"] = "low_confidence"
    confidence_threshold: float = 0.78


class AssessmentPack(BaseModel):
    id: str
    version: str
    title: str
    mode: AssessmentMode
    language: str = "en"
    licensing: str = ""
    consent: str = ""
    disclaimer: str = ""
    policy: PackPolicy = Field(default_factory=PackPolicy)
    items: list[AssessmentItem]
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    branches: list[BranchRule] = Field(default_factory=list)
    safety_hooks: list[SafetyHook] = Field(default_factory=list)
    export_schema: dict[str, Any] = Field(default_factory=dict)


class NormalizedResponse(BaseModel):
    item_id: str
    value: str | int | float | bool | list[str] | None = None
    anchor_id: str | None = None
    anchor_ids: list[str] = Field(default_factory=list)
    raw_text: str | None = None
    confidence: float = 1.0
    ambiguous: bool = False
    skipped: bool = False
    needs_confirmation: bool = False
    source: Literal["deterministic", "llm", "manual"] = "manual"


class ScoreResult(BaseModel):
    total: int | float | None = None
    severity: str | None = None
    by_item: dict[str, int | float] = Field(default_factory=dict)


class SafetyEvent(BaseModel):
    hook_id: str
    kind: str
    severity: str
    interrupt: bool
    item_id: str | None
    message: str
    evidence: str
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class AssessmentTurn(BaseModel):
    index: int
    item_id: str
    response: NormalizedResponse


class TurnRecord(BaseModel):
    speaker: Literal["system", "assistant", "user"]
    text: str
    item_id: str | None = None
    event: str = "turn"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    pack_id: str
    pack_version: str = ""
    status: SessionStatus = SessionStatus.in_progress
    current_item_id: str | None = None
    visited_item_ids: list[str] = Field(default_factory=list)
    responses: dict[str, NormalizedResponse] = Field(default_factory=dict)
    turns: list[AssessmentTurn] = Field(default_factory=list)
    score: ScoreResult = Field(default_factory=ScoreResult)
    safety_events: list[SafetyEvent] = Field(default_factory=list)
    pending_response: NormalizedResponse | None = None
    clarification_item_id: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
