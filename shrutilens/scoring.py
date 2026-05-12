from __future__ import annotations

from shrutilens.models import AssessmentPack, NormalizedResponse, ResponseType, ScoreResult


def score_pack(pack: AssessmentPack, responses: dict[str, NormalizedResponse]) -> ScoreResult:
    if pack.scoring.method == "none":
        return ScoreResult()

    by_item: dict[str, int | float] = {}
    total: int | float = 0

    for item in pack.items:
        response = responses.get(item.id)
        if response is None or response.skipped:
            continue

        if item.response_type == ResponseType.multi_select:
            scores = [a.score for a in item.anchors if a.id in response.anchor_ids and a.score is not None]
            if not scores:
                continue
            item_score: int | float = sum(scores)
        else:
            if response.anchor_id is None:
                continue
            anchor = next((a for a in item.anchors if a.id == response.anchor_id), None)
            if anchor is None or anchor.score is None:
                continue
            item_score = anchor.score

        by_item[item.id] = item_score
        total += item_score

    severity = next((b.label for b in pack.scoring.severity_bands if b.min <= total <= b.max), None)
    return ScoreResult(total=total, severity=severity, by_item=by_item)
