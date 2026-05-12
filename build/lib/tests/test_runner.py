from __future__ import annotations

from shrutilens import runner
from shrutilens.models import SessionStatus


def test_clinical_pack_preserves_locked_flow_and_scores(packs):
    pack = packs["phq9_demo"]
    state = runner.start_session(pack)
    prompt = runner.next_prompt(pack, state)

    assert prompt.item_id == "phq9_1"
    assert "little interest or pleasure" in prompt.text

    state, prompt = runner.accept_utterance(pack, state, "not at all")
    assert state.current_item_id == "phq9_2"
    assert prompt.item_id == "phq9_2"

    state, prompt = runner.accept_utterance(pack, state, "several days")
    assert state.score.total == 1
    assert prompt.item_id == "phq9_9"

    state, prompt = runner.accept_utterance(pack, state, "not at all")
    assert state.status == SessionStatus.completed
    assert state.score.total == 1
    assert state.score.severity == "minimal"
    assert prompt.event == "complete"


def test_low_confidence_clinical_answer_requires_confirmation(packs):
    pack = packs["phq9_demo"]
    state = runner.start_session(pack)

    state, prompt = runner.accept_utterance(pack, state, "uh maybe once or twice")

    assert state.status == SessionStatus.awaiting_confirmation
    assert state.pending_response is not None
    assert prompt.event == "confirmation_requested"

    state, prompt = runner.confirm_pending(pack, state, accepted=False, corrected_text="several days")
    assert state.status == SessionStatus.in_progress
    assert state.responses["phq9_1"].anchor_id == "several_days"
    assert prompt.item_id == "phq9_2"


def test_self_harm_item_interrupts_assessment(packs):
    pack = packs["phq9_demo"]
    state = runner.start_session(pack)

    state, _ = runner.accept_utterance(pack, state, "not at all")
    state, _ = runner.accept_utterance(pack, state, "not at all")
    state, prompt = runner.accept_utterance(pack, state, "several days")

    assert state.status == SessionStatus.safety_interrupted
    assert state.safety_events
    assert state.safety_events[0].severity == "crisis"
    assert prompt.event == "safety_protocol"


def test_research_pack_accepts_free_text_without_confirmation(packs):
    pack = packs["product_discovery_demo"]
    state = runner.start_session(pack)
    prompt = runner.next_prompt(pack, state)
    assert prompt.item_id == "role"

    state, prompt = runner.accept_utterance(pack, state, "I run support operations for a small clinic.")

    assert state.status == SessionStatus.in_progress
    assert state.responses["role"].value == "I run support operations for a small clinic."
    assert state.responses["role"].needs_confirmation is False
    assert prompt.item_id == "pain"
