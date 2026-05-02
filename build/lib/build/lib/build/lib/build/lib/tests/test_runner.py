from __future__ import annotations

from shrutilens.core.contracts import SessionStatus


def test_clinical_pack_preserves_locked_flow_and_scores(runner, pack_repository):
    pack = pack_repository.get("phq9_demo")
    state, prompt = runner.start(pack)

    assert prompt.item_id == "phq9_1"
    assert "little interest or pleasure" in prompt.text

    state, prompt = runner.accept_utterance(pack, state, "not at all")
    assert state.current_index == 1
    assert prompt.item_id == "phq9_2"

    state, prompt = runner.accept_utterance(pack, state, "several days")
    assert state.score.total == 1
    assert prompt.item_id == "phq9_9"

    state, prompt = runner.accept_utterance(pack, state, "not at all")
    assert state.status == SessionStatus.completed
    assert state.score.total == 1
    assert state.score.severity == "minimal"
    assert prompt.event == "complete"


def test_low_confidence_clinical_answer_requires_confirmation(runner, pack_repository):
    pack = pack_repository.get("phq9_demo")
    state, _ = runner.start(pack)

    state, prompt = runner.accept_utterance(pack, state, "uh maybe once or twice")

    assert state.status == SessionStatus.awaiting_confirmation
    assert state.pending_answer is not None
    assert prompt.event == "confirmation_requested"

    state, prompt = runner.confirm_pending(pack, state, accepted=False, corrected_text="several days")
    assert state.status == SessionStatus.in_progress
    assert state.responses[0].anchor_id == "several_days"
    assert prompt.item_id == "phq9_2"


def test_self_harm_item_interrupts_assessment(runner, pack_repository):
    pack = pack_repository.get("phq9_demo")
    state, _ = runner.start(pack)

    state, _ = runner.accept_utterance(pack, state, "not at all")
    state, _ = runner.accept_utterance(pack, state, "not at all")
    state, prompt = runner.accept_utterance(pack, state, "several days")

    assert state.status == SessionStatus.safety_interrupted
    assert state.safety_events
    assert state.safety_events[0].severity == "crisis"
    assert prompt.event == "safety_protocol"


def test_research_pack_accepts_free_text_without_confirmation(runner, pack_repository):
    pack = pack_repository.get("product_discovery_demo")
    state, prompt = runner.start(pack)
    assert prompt.item_id == "role"

    state, prompt = runner.accept_utterance(pack, state, "I run support operations for a small clinic.")

    assert state.status == SessionStatus.in_progress
    assert state.responses[0].value == "I run support operations for a small clinic."
    assert state.responses[0].needs_confirmation is False
    assert prompt.item_id == "pain"
