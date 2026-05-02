from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from shrutilens.core.contracts import (
    AssessmentMode,
    AssessmentPack,
    NormalizedAnswer,
    SessionState,
    SessionStatus,
    TurnRecord,
)
from shrutilens.core.normalizer import DeterministicNormalizer
from shrutilens.core.safety import SafetyGate
from shrutilens.core.scoring import DeterministicScorer
from shrutilens.exports.json_export import JsonExporter
from shrutilens.storage.audit import JsonlAuditLog
from shrutilens.storage.sqlite import SQLiteSessionStore


class AssessmentRunner:
    def __init__(
        self,
        store: SQLiteSessionStore,
        audit_log: JsonlAuditLog,
        exporter: JsonExporter,
        normalizer: DeterministicNormalizer | None = None,
        scorer: DeterministicScorer | None = None,
        safety_gate: SafetyGate | None = None,
    ) -> None:
        self.store = store
        self.audit_log = audit_log
        self.exporter = exporter
        self.normalizer = normalizer or DeterministicNormalizer()
        self.scorer = scorer or DeterministicScorer()
        self.safety_gate = safety_gate or SafetyGate()

    def start(self, pack: AssessmentPack, metadata: dict | None = None) -> tuple[SessionState, TurnRecord]:
        state = SessionState(id=str(uuid4()), pack_id=pack.id, metadata=metadata or {})
        self.store.save(state)
        self.audit_log.append(state.id, "session_started", {"pack_id": pack.id, "mode": pack.mode.value})
        prompt = self.next_prompt(pack, state)
        return state, prompt

    def next_prompt(self, pack: AssessmentPack, state: SessionState) -> TurnRecord:
        if state.status == SessionStatus.safety_interrupted:
            return TurnRecord(
                speaker="assistant",
                text="I need to pause the assessment because your last answer may indicate immediate safety risk. If you are in immediate danger, contact local emergency services now. If you can, reach out to a trusted person or crisis support in your area.",
                event="safety_protocol",
            )
        if state.current_index >= len(pack.items):
            return TurnRecord(speaker="assistant", text="That completes this assessment. Thank you.", event="complete")

        item = pack.items[state.current_index]
        intro = "" if state.current_index else f"{pack.consent} {pack.disclaimer} "
        text = intro + item.text
        return TurnRecord(speaker="assistant", text=text, item_id=item.id)

    def accept_utterance(self, pack: AssessmentPack, state: SessionState, utterance: str) -> tuple[SessionState, TurnRecord]:
        if state.status not in {SessionStatus.in_progress, SessionStatus.awaiting_confirmation}:
            return state, self.next_prompt(pack, state)
        if state.current_index >= len(pack.items):
            state.status = SessionStatus.completed
            self.store.save(state)
            return state, self.next_prompt(pack, state)

        item = pack.items[state.current_index]
        answer = self.normalizer.normalize(item, utterance, pack.policy.confidence_threshold)
        self.audit_log.append(state.id, "user_utterance", {"item_id": item.id, "text": utterance})
        self.audit_log.append(state.id, "normalized_answer", answer.model_dump(mode="json"))

        if self._requires_confirmation(pack, answer):
            state.pending_answer = answer
            state.status = SessionStatus.awaiting_confirmation
            self.store.save(state)
            return state, TurnRecord(
                speaker="assistant",
                text=self._confirmation_text(item.text, answer),
                item_id=item.id,
                event="confirmation_requested",
                metadata={"answer": answer.model_dump(mode="json")},
            )

        return self._commit_answer(pack, state, answer)

    def confirm_pending(self, pack: AssessmentPack, state: SessionState, accepted: bool, corrected_text: str | None = None) -> tuple[SessionState, TurnRecord]:
        if state.pending_answer is None:
            return state, self.next_prompt(pack, state)
        item = pack.items[state.current_index]
        if not accepted:
            retry_text = corrected_text or ""
            state.pending_answer = None
            state.status = SessionStatus.in_progress
            self.store.save(state)
            if retry_text:
                return self.accept_utterance(pack, state, retry_text)
            return state, TurnRecord(
                speaker="assistant",
                text="Thanks. Please say that answer again in your own words.",
                item_id=item.id,
                event="repair_prompt",
            )

        answer = state.pending_answer.model_copy(update={"needs_confirmation": False, "source": "manual"})
        state.pending_answer = None
        state.status = SessionStatus.in_progress
        return self._commit_answer(pack, state, answer)

    def _commit_answer(self, pack: AssessmentPack, state: SessionState, answer: NormalizedAnswer) -> tuple[SessionState, TurnRecord]:
        state.responses.append(answer)
        events = self.safety_gate.evaluate(pack, answer)
        state.safety_events.extend(events)
        for event in events:
            self.audit_log.append(state.id, "safety_event", event.model_dump(mode="json"))

        if any(event.severity == "crisis" for event in events):
            state.status = SessionStatus.safety_interrupted
            state.score = self.scorer.score(pack, state.responses)
            self.store.save(state)
            return state, self.next_prompt(pack, state)

        state.current_index += 1
        state.score = self.scorer.score(pack, state.responses)
        if state.current_index >= len(pack.items):
            state.status = SessionStatus.completed
            export_path = self.exporter.export(pack, state)
            self.audit_log.append(state.id, "session_completed", {"export_path": str(export_path)})
        self.store.save(state)
        return state, self.next_prompt(pack, state)

    def _requires_confirmation(self, pack: AssessmentPack, answer: NormalizedAnswer) -> bool:
        if pack.policy.confirmation_required == "always":
            return True
        if pack.policy.confirmation_required == "never":
            return False
        return answer.needs_confirmation and pack.mode == AssessmentMode.clinical_locked

    def _confirmation_text(self, item_text: str, answer: NormalizedAnswer) -> str:
        if answer.anchor_id:
            heard = answer.anchor_id.replace("_", " ")
        else:
            heard = answer.raw_text
        return f"I want to make sure I heard you correctly. For: {item_text} Should I record your answer as {heard}?"


def build_default_runner(data_dir: Path = Path("data"), export_dir: Path = Path("exports")) -> AssessmentRunner:
    return AssessmentRunner(
        store=SQLiteSessionStore(data_dir / "shrutilens.sqlite3"),
        audit_log=JsonlAuditLog(data_dir / "audit"),
        exporter=JsonExporter(export_dir),
    )
