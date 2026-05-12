from __future__ import annotations

from pathlib import Path

from shrutilens.models import NormalizedResponse

from tests.assessment.helpers import assert_matches_golden


GOLDEN = Path(__file__).resolve().parent / "golden"


def test_market_discovery_branch_skips_pain_story_and_completes(runner, market_pack):
    state = runner.start_session(market_pack)
    assert runner.next_item(market_pack, state).id == "role"

    state = runner.accept_response(
        market_pack,
        state,
        NormalizedResponse(item_id="role", value="Product manager", raw_text="I am a product manager."),
    )
    assert runner.next_item(market_pack, state).id == "has_problem"

    state = runner.accept_response(
        market_pack,
        state,
        NormalizedResponse(item_id="has_problem", anchor_id="no", value="no", raw_text="not really"),
    )
    assert runner.next_item(market_pack, state).id == "current_solution"

    state = runner.accept_response(
        market_pack,
        state,
        NormalizedResponse(item_id="current_solution", value="Spreadsheets", raw_text="Mostly spreadsheets."),
    )
    state = runner.accept_response(
        market_pack,
        state,
        NormalizedResponse(item_id="closing", value="Clear time savings", raw_text="It would need to save time."),
    )

    assert state.status == "completed"
    assert "pain_story" not in state.responses
    record = runner.export_record(market_pack, state)
    assert_matches_golden(record, GOLDEN / "market_discovery_complete.json")
