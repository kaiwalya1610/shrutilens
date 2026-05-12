from __future__ import annotations

from pathlib import Path

from shrutilens.models import NormalizedResponse

from tests.assessment.helpers import assert_matches_golden


GOLDEN = Path(__file__).resolve().parent / "golden"


def test_phq9_all_zero_flow_exports_golden_record(runner, phq9_pack):
    state = runner.start_session(phq9_pack)

    for index in range(1, 10):
        item = runner.next_item(phq9_pack, state)
        assert item is not None
        assert item.id == f"phq9_{index}"
        state = runner.accept_response(
            phq9_pack,
            state,
            NormalizedResponse(item_id=item.id, anchor_id="not_at_all", raw_text="not at all"),
        )

    assert state.status == "completed"
    record = runner.export_record(phq9_pack, state)
    assert_matches_golden(record, GOLDEN / "phq9_all_zero.json")


def test_phq9_moderate_flow_exports_golden_record(runner, phq9_pack):
    anchors = [
        "several_days",
        "several_days",
        "several_days",
        "more_than_half",
        "more_than_half",
        "several_days",
        "several_days",
        "several_days",
        "not_at_all",
    ]
    state = runner.start_session(phq9_pack)
    for index, anchor_id in enumerate(anchors, start=1):
        state = runner.accept_response(
            phq9_pack,
            state,
            NormalizedResponse(item_id=f"phq9_{index}", anchor_id=anchor_id, raw_text=anchor_id),
        )

    assert state.score.total == 10
    assert state.score.severity == "moderate"
    record = runner.export_record(phq9_pack, state)
    assert_matches_golden(record, GOLDEN / "phq9_moderate.json")


def test_phq9_ambiguous_response_needs_clarification(runner, phq9_pack):
    state = runner.start_session(phq9_pack)
    state = runner.accept_response(
        phq9_pack,
        state,
        NormalizedResponse(item_id="phq9_1", anchor_id="not_at_all", ambiguous=True),
    )

    assert state.status == "needs_clarification"
    assert state.clarification_item_id == "phq9_1"
    assert state.current_item_id == "phq9_1"
    assert state.responses == {}
