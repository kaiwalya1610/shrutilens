from __future__ import annotations

from shrutilens.core.contracts import AssessmentPack, NormalizedAnswer, ScoreResult


class DeterministicScorer:
    def score(self, pack: AssessmentPack, responses: list[NormalizedAnswer]) -> ScoreResult:
        if pack.scoring.method == "none":
            return ScoreResult(total=None, severity=None, detail={})
        if pack.scoring.method != "sum":
            raise NotImplementedError(f"Unsupported scoring method: {pack.scoring.method}")

        items_by_id = {item.id: item for item in pack.items}
        total = 0
        detail: dict[str, int | float] = {}
        for response in responses:
            item = items_by_id.get(response.item_id)
            if item is None or response.anchor_id is None:
                continue
            anchor = next((anchor for anchor in item.anchors if anchor.id == response.anchor_id), None)
            if anchor is None or anchor.score is None:
                continue
            total += anchor.score
            detail[item.id] = anchor.score

        severity = self._severity(pack, total)
        return ScoreResult(total=total, severity=severity, detail=detail)

    def _severity(self, pack: AssessmentPack, total: int | float) -> str | None:
        for band in pack.scoring.severity_bands:
            if band["min"] <= total <= band["max"]:
                return str(band["label"])
        return None
