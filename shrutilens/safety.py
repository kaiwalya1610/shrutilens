from __future__ import annotations

from shrutilens.models import AssessmentPack, NormalizedResponse, SafetyEvent, SafetyHook, ScoreResult


def evaluate_safety(
    pack: AssessmentPack, response: NormalizedResponse, score: ScoreResult
) -> list[SafetyEvent]:
    events: list[SafetyEvent] = []
    raw_text = (response.raw_text or "").lower()

    for hook in pack.safety_hooks:
        if hook.item_id is not None and hook.item_id != response.item_id:
            continue

        if hook.kind == "anchor_match":
            response_anchors = {response.anchor_id, *response.anchor_ids}
            matched = [a for a in hook.anchor_ids if a in response_anchors]
            if matched:
                events.append(_event(hook, response.item_id, ",".join(matched)))

        elif hook.kind == "keyword":
            matched_kw = [k for k in hook.keywords if k.lower() in raw_text]
            if matched_kw:
                events.append(_event(hook, response.item_id, ",".join(matched_kw)))

        elif hook.kind == "score_threshold":
            if score.total is not None and hook.threshold is not None and score.total >= hook.threshold:
                events.append(_event(hook, response.item_id, f"score={score.total}"))

    return events


def _event(hook: SafetyHook, item_id: str, evidence: str) -> SafetyEvent:
    return SafetyEvent(
        hook_id=hook.id,
        kind=hook.kind,
        severity=hook.severity,
        interrupt=hook.interrupt,
        item_id=item_id,
        message=hook.message,
        evidence=evidence,
    )
