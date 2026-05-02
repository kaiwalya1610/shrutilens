from __future__ import annotations

from shrutilens.core.contracts import AssessmentPack, NormalizedAnswer, SafetyEvent


class SafetyGate:
    def evaluate(self, pack: AssessmentPack, answer: NormalizedAnswer) -> list[SafetyEvent]:
        events: list[SafetyEvent] = []
        raw_lower = answer.raw_text.lower()

        for hook in pack.safety_hooks:
            if hook.item_id is not None and hook.item_id != answer.item_id:
                continue
            if hook.kind == "keyword":
                for keyword in hook.keywords:
                    if keyword.lower() in raw_lower:
                        events.append(
                            SafetyEvent(
                                hook_kind=hook.kind,
                                severity=hook.severity,
                                item_id=answer.item_id,
                                message=hook.message,
                                evidence=keyword,
                            )
                        )
            if hook.kind == "anchor_match" and answer.anchor_id in hook.anchor_ids:
                events.append(
                    SafetyEvent(
                        hook_kind=hook.kind,
                        severity=hook.severity,
                        item_id=answer.item_id,
                        message=hook.message,
                        evidence=answer.anchor_id or "",
                    )
                )

        return events
