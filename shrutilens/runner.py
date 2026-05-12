from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from shrutilens.branching import next_item_id
from shrutilens.models import (
    AssessmentItem,
    AssessmentMode,
    AssessmentPack,
    AssessmentTurn,
    NormalizedResponse,
    ResponseType,
    SessionState,
    SessionStatus,
    TurnRecord,
)
from shrutilens.normalizer import normalize_utterance
from shrutilens.safety import evaluate_safety
from shrutilens.scoring import score_pack


SAFETY_PROTOCOL_TEXT = (
    "I need to pause the assessment because your last answer may indicate immediate safety risk. "
    "If you are in immediate danger, contact local emergency services now. "
    "If you can, reach out to a trusted person or crisis support in your area."
)


def start_session(pack: AssessmentPack, metadata: dict[str, Any] | None = None) -> SessionState:
    first_item = pack.items[0]
    return SessionState(
        pack_id=pack.id,
        pack_version=pack.version,
        current_item_id=first_item.id,
        metadata=metadata or {},
    )


def next_item(pack: AssessmentPack, state: SessionState) -> AssessmentItem | None:
    if state.status in {SessionStatus.completed, SessionStatus.safety_interrupted}:
        return None
    if state.current_item_id is None:
        return None
    return _find_item(pack, state.current_item_id)


def next_prompt(pack: AssessmentPack, state: SessionState) -> TurnRecord:
    if state.status == SessionStatus.safety_interrupted:
        return TurnRecord(speaker="assistant", text=SAFETY_PROTOCOL_TEXT, event="safety_protocol")
    if state.status == SessionStatus.completed or state.current_item_id is None:
        return TurnRecord(speaker="assistant", text="That completes this assessment. Thank you.", event="complete")

    item = _find_item(pack, state.current_item_id)
    is_first = not state.visited_item_ids and not state.responses
    intro = f"{pack.consent} {pack.disclaimer} " if is_first and (pack.consent or pack.disclaimer) else ""
    return TurnRecord(speaker="assistant", text=intro + item.text, item_id=item.id)


def accept_response(
    pack: AssessmentPack, state: SessionState, response: NormalizedResponse
) -> SessionState:
    if state.status in {SessionStatus.completed, SessionStatus.safety_interrupted}:
        raise RuntimeError(f"cannot accept responses when session is {state.status}")
    if state.current_item_id is None:
        raise RuntimeError("session has no active item")
    if response.item_id != state.current_item_id:
        raise ValueError(f"expected response for {state.current_item_id}, got {response.item_id}")

    item = _find_item(pack, state.current_item_id)
    _validate_response(item, response)

    if response.ambiguous and pack.policy.clarification_on_ambiguous:
        state.status = SessionStatus.needs_clarification
        state.clarification_item_id = item.id
        return state

    if response.skipped and item.required and not item.allow_skip:
        state.status = SessionStatus.needs_clarification
        state.clarification_item_id = item.id
        return state

    return _commit_response(pack, state, item, response)


def accept_utterance(
    pack: AssessmentPack, state: SessionState, utterance: str
) -> tuple[SessionState, TurnRecord]:
    if state.status in {SessionStatus.completed, SessionStatus.safety_interrupted}:
        return state, next_prompt(pack, state)
    if state.current_item_id is None:
        return state, next_prompt(pack, state)

    item = _find_item(pack, state.current_item_id)
    response = normalize_utterance(item, utterance, pack.policy.confidence_threshold)

    if _requires_confirmation(pack, response):
        state.pending_response = response
        state.status = SessionStatus.awaiting_confirmation
        return state, TurnRecord(
            speaker="assistant",
            text=_confirmation_text(item.text, response),
            item_id=item.id,
            event="confirmation_requested",
            metadata={"response": response.model_dump(mode="json")},
        )

    state = _commit_response(pack, state, item, response)
    return state, next_prompt(pack, state)


def confirm_pending(
    pack: AssessmentPack, state: SessionState, accepted: bool, corrected_text: str | None = None
) -> tuple[SessionState, TurnRecord]:
    if state.pending_response is None:
        return state, next_prompt(pack, state)

    item = _find_item(pack, state.current_item_id) if state.current_item_id else None
    if not accepted:
        state.pending_response = None
        state.status = SessionStatus.in_progress
        if corrected_text:
            return accept_utterance(pack, state, corrected_text)
        return state, TurnRecord(
            speaker="assistant",
            text="Thanks. Please say that answer again in your own words.",
            item_id=item.id if item else None,
            event="repair_prompt",
        )

    response = state.pending_response.model_copy(update={"needs_confirmation": False, "source": "manual"})
    state.pending_response = None
    state.status = SessionStatus.in_progress
    state = _commit_response(pack, state, item, response)
    return state, next_prompt(pack, state)


def export_record(pack: AssessmentPack, state: SessionState) -> dict[str, Any]:
    return {
        "exported_at": datetime.now(UTC).isoformat(),
        "pack": {
            "id": pack.id,
            "version": pack.version,
            "title": pack.title,
            "mode": pack.mode.value,
            "language": pack.language,
        },
        "session": state.model_dump(mode="json"),
        "items": [
            {
                "id": item.id,
                "text": item.text,
                "locked_wording": item.locked_wording,
                "response_type": item.response_type.value,
                "required": item.required,
            }
            for item in pack.items
            if item.id in state.visited_item_ids
        ],
        "schema": pack.export_schema,
    }


def _commit_response(
    pack: AssessmentPack, state: SessionState, item: AssessmentItem, response: NormalizedResponse
) -> SessionState:
    state.status = SessionStatus.in_progress
    state.clarification_item_id = None
    state.responses[item.id] = response
    if item.id not in state.visited_item_ids:
        state.visited_item_ids.append(item.id)
    state.turns.append(AssessmentTurn(index=len(state.turns), item_id=item.id, response=response))

    state.score = score_pack(pack, state.responses)
    events = evaluate_safety(pack, response, state.score)
    state.safety_events.extend(events)
    if any(e.interrupt for e in events):
        state.status = SessionStatus.safety_interrupted
        return state

    state.current_item_id = next_item_id(pack, item.id, state.responses)
    if state.current_item_id is None:
        state.status = SessionStatus.completed
        state.completed_at = datetime.now(UTC).isoformat()
    return state


def _find_item(pack: AssessmentPack, item_id: str) -> AssessmentItem:
    for item in pack.items:
        if item.id == item_id:
            return item
    raise KeyError(f"unknown item: {item_id}")


def _validate_response(item: AssessmentItem, response: NormalizedResponse) -> None:
    if response.skipped:
        return

    anchor_ids = {a.id for a in item.anchors}

    if item.response_type in {ResponseType.choice, ResponseType.rating, ResponseType.boolean}:
        if response.anchor_id not in anchor_ids:
            raise ValueError(f"{item.id} response must use one of the configured anchors")

    if item.response_type == ResponseType.multi_select:
        invalid = [a for a in response.anchor_ids if a not in anchor_ids]
        if invalid:
            raise ValueError(f"{item.id} response has invalid anchors: {', '.join(invalid)}")

    if item.response_type in {ResponseType.numeric, ResponseType.rating} and response.value is not None:
        if not isinstance(response.value, int | float):
            raise ValueError(f"{item.id} response value must be numeric")

    if item.response_type == ResponseType.open_text and not response.raw_text and response.value is None:
        raise ValueError(f"{item.id} open_text response requires text or value")


def _requires_confirmation(pack: AssessmentPack, response: NormalizedResponse) -> bool:
    if pack.policy.confirmation_required == "always":
        return True
    if pack.policy.confirmation_required == "never":
        return False
    return response.needs_confirmation and pack.mode == AssessmentMode.clinical_locked


def _confirmation_text(item_text: str, response: NormalizedResponse) -> str:
    heard = response.anchor_id.replace("_", " ") if response.anchor_id else (response.raw_text or "")
    return f"I want to make sure I heard you correctly. For: {item_text} Should I record your answer as {heard}?"
