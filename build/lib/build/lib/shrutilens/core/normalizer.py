from __future__ import annotations

import re

from shrutilens.core.contracts import AssessmentItem, NormalizedAnswer


class DeterministicNormalizer:
    """Maps common spoken answers to configured anchors without using an LLM."""

    def normalize(self, item: AssessmentItem, utterance: str, threshold: float) -> NormalizedAnswer:
        text = utterance.strip()
        if item.response_type == "free_text" or not item.anchors:
            return NormalizedAnswer(
                item_id=item.id,
                raw_text=text,
                value=text,
                confidence=1.0 if text else 0.0,
                needs_confirmation=False,
            )

        lowered = self._normalize_text(text)
        best_anchor_id: str | None = None
        best_score = 0.0
        for anchor in item.anchors:
            candidates = [anchor.label, *anchor.utterance_patterns]
            for candidate in candidates:
                score = self._match_score(lowered, self._normalize_text(candidate))
                if score > best_score:
                    best_score = score
                    best_anchor_id = anchor.id

        return NormalizedAnswer(
            item_id=item.id,
            raw_text=text,
            anchor_id=best_anchor_id if best_score >= 0.45 else None,
            confidence=round(best_score, 3),
            needs_confirmation=best_score < threshold,
        )

    def _match_score(self, utterance: str, candidate: str) -> float:
        if not utterance or not candidate:
            return 0.0
        if utterance == candidate:
            return 1.0
        if candidate in utterance:
            return 0.95
        utterance_tokens = set(utterance.split())
        candidate_tokens = set(candidate.split())
        if not candidate_tokens:
            return 0.0
        overlap = len(utterance_tokens & candidate_tokens) / len(candidate_tokens)
        return min(overlap, 0.89)

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", text.lower())).strip()
