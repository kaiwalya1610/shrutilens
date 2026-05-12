from __future__ import annotations

from shrutilens.models import NormalizedResponse
from shrutilens.scoring import score_pack


def test_phq9_sum_scoring_and_severity(phq9_pack):
    responses = {
        f"phq9_{index}": NormalizedResponse(item_id=f"phq9_{index}", anchor_id="several_days")
        for index in range(1, 8)
    }
    responses["phq9_8"] = NormalizedResponse(item_id="phq9_8", anchor_id="more_than_half")
    responses["phq9_9"] = NormalizedResponse(item_id="phq9_9", anchor_id="not_at_all")

    score = score_pack(phq9_pack, responses)

    assert score.total == 9
    assert score.severity == "mild"
    assert score.by_item["phq9_8"] == 2
