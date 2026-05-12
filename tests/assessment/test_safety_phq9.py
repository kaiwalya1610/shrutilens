from __future__ import annotations

from pathlib import Path

from shrutilens.models import NormalizedResponse

from tests.assessment.helpers import assert_matches_golden


GOLDEN = Path(__file__).resolve().parent / "golden"


def test_item9_positive_triggers_crisis_interrupt(runner, phq9_pack):
    state = runner.start_session(phq9_pack)
    for index in range(1, 9):
        state = runner.accept_response(
            phq9_pack,
            state,
            NormalizedResponse(item_id=f"phq9_{index}", anchor_id="not_at_all"),
        )

    state = runner.accept_response(
        phq9_pack,
        state,
        NormalizedResponse(item_id="phq9_9", anchor_id="several_days", raw_text="several days"),
    )

    assert state.status == "safety_interrupted"
    assert state.safety_events[0].hook_id == "item9_positive"
    assert state.current_item_id == "phq9_9"
    assert_matches_golden(runner.export_record(phq9_pack, state), GOLDEN / "phq9_item9_positive.json")


def test_self_harm_keyword_triggers_crisis_interrupt(runner, phq9_pack):
    state = runner.start_session(phq9_pack)
    state = runner.accept_response(
        phq9_pack,
        state,
        NormalizedResponse(item_id="phq9_1", anchor_id="not_at_all", raw_text="I might kill myself"),
    )

    assert state.status == "safety_interrupted"
    assert state.safety_events[0].hook_id == "self_harm_keywords"
