from __future__ import annotations

import re

from shrutilens.models import AssessmentItem, NormalizedResponse, ResponseType


def normalize_utterance(item: AssessmentItem, utterance: str, threshold: float) -> NormalizedResponse:
    text = utterance.strip()
    if item.response_type == ResponseType.open_text or not item.anchors:
        return NormalizedResponse(
            item_id=item.id,
            raw_text=text,
            value=text or None,
            confidence=1.0 if text else 0.0,
            source="deterministic",
        )

    lowered = _clean(text)
    best_id: str | None = None
    best_score = 0.0
    for anchor in item.anchors:
        for candidate in [anchor.label, *anchor.utterance_patterns]:
            score = _match_score(lowered, _clean(candidate))
            if score > best_score:
                best_score = score
                best_id = anchor.id

    return NormalizedResponse(
        item_id=item.id,
        raw_text=text,
        anchor_id=best_id if best_score >= 0.45 else None,
        confidence=round(best_score, 3),
        needs_confirmation=best_score < threshold,
        source="deterministic",
    )


def _match_score(utterance: str, candidate: str) -> float:
    if not utterance or not candidate:
        return 0.0
    if utterance == candidate:
        return 1.0
    if candidate in utterance:
        return 0.95
    u_tokens = set(utterance.split())
    c_tokens = set(candidate.split())
    if not c_tokens:
        return 0.0
    return min(len(u_tokens & c_tokens) / len(c_tokens), 0.89)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", text.lower())).strip()
