# Shrutilens UI Design Document

## 1. Product Overview

Shrutilens is a local-first, audio-first structured conversational assessment runtime. The current application is primarily a backend engine and FastAPI surface that can run assessment packs, persist sessions locally, apply deterministic scoring, trigger safety gates, and export completed records.

The UI should become the human-facing layer for this runtime: a calm, trustworthy interface where an operator or participant can choose an assessment pack, conduct a guided voice/text session, confirm uncertain answers, handle safety interruptions, review structured outputs, and manage exported records.

The design must respect the project's core constraint:

> LLMs may assist with conversational experience in future versions, but scoring, branching, item order, and crisis handling must remain deterministic and inspectable.

## 2. Current Development Snapshot

### 2.1 Implemented Backend Capabilities

The current `shrutilens` package supports:

- Pack discovery from `shrutilens/packs/*.json`.
- Two assessment modes:
  - `clinical_locked`
  - `research_flexible`
- FastAPI endpoints:
  - `GET /health`
  - `GET /packs`
  - `POST /sessions`
  - `GET /sessions/{session_id}`
  - `POST /sessions/{session_id}/utterance`
  - `POST /sessions/{session_id}/confirmation`
- Session lifecycle states:
  - `in_progress`
  - `awaiting_confirmation`
  - `safety_interrupted`
  - `completed`
- Deterministic answer normalization.
- Deterministic scoring.
- Safety hook evaluation.
- SQLite session persistence.
- JSONL audit logging.
- JSON export generation on completion.
- A `ModelClient` abstraction for future OpenRouter-backed model use.

### 2.2 Existing Demo Packs

#### PHQ-9 Demo Pack

Pack ID: `phq9_demo`

Purpose:

- Demonstrates locked clinical screening.
- Uses fixed item wording.
- Uses anchored frequency responses.
- Applies deterministic sum scoring.
- Interrupts on self-harm signal.

UI implication:

- Must feel restrained, clinical, and safety-aware.
- Must display consent and disclaimer before the first item.
- Must make answer confirmation explicit when the backend requests it.
- Must treat safety interruption as a first-class state, not an error.

#### Product Discovery Demo Pack

Pack ID: `product_discovery_demo`

Purpose:

- Demonstrates flexible research interview behavior.
- Uses free-text answers.
- Has no scoring.
- Allows more conversational framing.
- Still includes safety keyword handling.

UI implication:

- Can feel more exploratory and lightweight.
- Should support long-form answers and interviewer notes.
- Should surface tags and themes in future versions.

### 2.3 Parallel Assessment Track

The `voice_assessor` module contains a second engine track with concepts that are not fully mirrored in the main `shrutilens` API yet:

- YAML pack loading.
- Branch rules.
- Clarification states.
- Skippable items.
- Multi-select, numeric, rating, boolean, and open-text response models.
- Item-level validation.

UI implication:

- The UI should be designed so it can absorb branching, skip logic, and richer response controls without a redesign.
- The first version can target the current FastAPI contract, but the layout should leave room for future item metadata and dynamic question paths.

## 3. Product Goals

### 3.1 Primary Goal

Create a clean, operator-friendly interface for running structured assessment sessions with confidence, transparency, and safety.

### 3.2 Secondary Goals

- Make pack selection and session startup simple.
- Make the current question, expected answer format, and progress obvious.
- Support both text entry and future voice capture.
- Provide clear confirmation and repair flows for uncertain answers.
- Show session state without exposing unnecessary technical detail.
- Make completed exports easy to review.
- Keep clinical and research workflows visually distinct without fragmenting the product.
- Preserve local-first trust: users should understand where data lives and what has been recorded.

### 3.3 Non-Goals for the First UI

- Full clinical deployment.
- Real-time clinician escalation network.
- Remote account system.
- Multi-tenant organization management.
- Advanced analytics dashboards.
- Pack authoring UI.
- Live audio transcription pipeline, unless added separately to the backend.

## 4. Target Users

### 4.1 Participant

A person answering assessment or interview questions. They need:

- Clear consent/disclaimer language.
- A visible current prompt.
- A low-friction way to answer.
- A sense of progress.
- Reassurance when the system asks for confirmation.
- Immediate supportive messaging during safety interruption.

### 4.2 Facilitator or Researcher

A person running sessions for another person or conducting interviews. They need:

- Fast pack selection.
- Session metadata entry.
- A stable conversation panel.
- Transcript and structured response review.
- Export access after completion.
- Confidence that the engine is following pack rules.

### 4.3 Developer or Evaluator

A person validating packs and engine behavior. They need:

- Visibility into raw session state.
- Pack metadata.
- Normalization confidence.
- Safety events.
- Export payload preview.
- API/debug affordances in non-production mode.

## 5. Design Principles

### 5.1 Calm Before Clever

The interface should not feel like a chatbot toy. It should feel like a focused assessment console with soft conversational affordances.

### 5.2 Deterministic Transparency

When the system records an answer, the UI should show what was captured and why. If confidence is low, confirmation should be explicit.

### 5.3 Safety Is a State

Safety interruption is part of the workflow. It should be represented with deliberate visual hierarchy, clear support language, and disabled normal progression.

### 5.4 Local-First Trust

The product stores sessions, audit logs, and exports locally. UI copy should reinforce that data is local without turning the interface into documentation.

### 5.5 Mode-Sensitive Experience

Clinical locked mode and research flexible mode share the same shell, but differ in interaction constraints:

- Clinical: fixed wording, anchored answers, scoring, stricter confirmation.
- Research: free text, tags, future follow-ups, interview notes.

## 6. Information Architecture

### 6.1 Main Navigation

Recommended first-version navigation:

- Sessions
- Packs
- Exports
- Settings

Developer-mode navigation:

- Audit Log
- API State
- Pack JSON

### 6.2 Application Areas

#### Sessions

Primary work area for starting, running, resuming, and reviewing sessions.

Key views:

- New Session
- Active Session
- Session Review

#### Packs

Catalog of installed assessment packs.

Key views:

- Pack List
- Pack Detail
- Pack Validation Status

#### Exports

Completed session records.

Key views:

- Export List
- Export Detail
- JSON Preview

#### Settings

Runtime configuration.

Key views:

- Storage paths
- Model provider status
- Audio capture preferences
- Developer mode toggle

## 7. Core User Flows

### 7.1 Start a Session

1. User opens Sessions.
2. User selects New Session.
3. UI calls `GET /packs`.
4. User selects a pack.
5. UI displays pack title, mode, language, consent, disclaimer, and licensing note.
6. User optionally enters metadata.
7. UI calls `POST /sessions`.
8. UI opens Active Session with the first prompt.

### 7.2 Submit an Answer

1. UI displays active prompt.
2. User types or speaks an answer.
3. UI sends `POST /sessions/{session_id}/utterance`.
4. UI updates session state and prompt.
5. If status remains `in_progress`, show next prompt.
6. If status is `awaiting_confirmation`, show confirmation panel.
7. If status is `completed`, show completion panel.
8. If status is `safety_interrupted`, show safety interruption panel.

### 7.3 Confirm an Uncertain Answer

1. Backend returns prompt with event `confirmation_requested`.
2. UI shows the interpreted answer.
3. User chooses Confirm or Correct.
4. If Confirm, UI calls `POST /sessions/{session_id}/confirmation` with `accepted: true`.
5. If Correct, user enters corrected text and UI calls the same endpoint with `accepted: false` and `corrected_text`.
6. UI advances based on returned session state.

### 7.4 Complete a Session

1. Backend marks state as `completed`.
2. Exporter writes a JSON file.
3. UI shows final score if available.
4. UI shows all captured responses.
5. UI provides export review and copy/download affordances.

### 7.5 Safety Interruption

1. Safety hook detects crisis evidence.
2. Backend marks state as `safety_interrupted`.
3. UI replaces normal assessment controls with safety protocol view.
4. UI displays the backend-provided safety prompt.
5. UI disables normal answer submission.
6. UI shows session status, safety event evidence in facilitator/developer mode, and next-step support guidance.

## 8. Screen Designs

### 8.1 App Shell

Layout:

- Left sidebar navigation.
- Main content area.
- Top status strip with local runtime status.

Sidebar items:

- Sessions
- Packs
- Exports
- Settings

Top status strip:

- API status.
- Storage mode: Local.
- Current session status when active.

Visual tone:

- Quiet, professional, high readability.
- Avoid decorative gradients and marketing-style hero sections.
- Use compact panels and tables where useful.

### 8.2 Sessions Dashboard

Purpose:

Entry point for current and recent work.

Components:

- New Session button.
- Recent Sessions table.
- Filters by pack, status, and date.
- Empty state for first run.

Recent Sessions columns:

- Session ID short form.
- Pack title.
- Mode.
- Status.
- Updated time.
- Score or completion marker.

Current backend gap:

- There is no list sessions API yet. First UI version may need either a frontend-only active session cache or a new endpoint.

Recommended backend addition:

- `GET /sessions`
- Query params: `status`, `pack_id`, `limit`, `offset`

### 8.3 New Session Screen

Purpose:

Select a pack and start safely.

Components:

- Pack selector.
- Pack summary.
- Mode badge.
- Consent block.
- Disclaimer block.
- Metadata fields.
- Start button.

Metadata fields for MVP:

- Participant label.
- Facilitator label.
- Notes.

Behavior:

- Disable Start until a pack is selected.
- For clinical locked packs, display a visible "wording and scoring are locked" indicator.
- For research flexible packs, display "free text interview" indicator.

### 8.4 Active Session Screen

Purpose:

Run the assessment or interview.

Recommended layout:

- Left: session progress and pack details.
- Center: current prompt and response controls.
- Right: transcript/responses panel.

Primary regions:

- Current prompt.
- Answer input.
- Response anchors, when available.
- Confirmation panel, when needed.
- Session timeline.
- Score/status summary.

For `clinical_locked`:

- Display current question exactly as returned by backend.
- If anchors exist, show anchor buttons:
  - Not at all
  - Several days
  - More than half the days
  - Nearly every day
- Also support text entry for spoken/text transcription.
- Avoid paraphrasing the question.

For `research_flexible`:

- Use a larger free-text response box.
- Allow interviewer notes in future.
- Show tags when available.
- Prepare space for future follow-up prompts.

### 8.5 Confirmation State

Trigger:

- `SessionStatus.awaiting_confirmation`
- Prompt event: `confirmation_requested`

Components:

- Interpreted answer summary.
- Original user text.
- Confirm button.
- Correct answer input.
- Submit correction button.

UX copy direction:

- Keep it neutral.
- Avoid implying the participant made a mistake.
- Use language such as: "Confirm captured answer".

Backend mapping:

- Confirm: `accepted: true`
- Correct: `accepted: false`, `corrected_text: "..."`

### 8.6 Completion State

Trigger:

- `SessionStatus.completed`

Components:

- Completion message.
- Score summary when `score.total` exists.
- Severity band when `score.severity` exists.
- Response list.
- Export status.
- Start another session button.

Clinical score display:

- Use restrained severity styling.
- Avoid alarmist colors except where clinically necessary.
- Include "demo only" or licensing caution where applicable.

Research completion display:

- Show captured responses by tag.
- Prepare for future summary extraction.

### 8.7 Safety Interruption State

Trigger:

- `SessionStatus.safety_interrupted`

Components:

- Prominent safety message from backend.
- Session paused indicator.
- Emergency guidance.
- Optional trusted contact workflow in future.
- Facilitator-only safety event details.

Controls:

- Disable normal Continue.
- Allow End Session.
- Allow Export Current State.
- Allow View Safety Events in facilitator/developer mode.

Design requirements:

- This view must not look like a generic error.
- Use clear hierarchy and strong contrast.
- Avoid animations or distracting visuals.

### 8.8 Pack List

Purpose:

Show available packs from `GET /packs`.

Columns/cards:

- Title.
- ID.
- Version.
- Mode.
- Language.
- Licensing status.

Actions:

- View pack.
- Start session.

Future actions:

- Validate pack.
- Duplicate pack.
- Import pack.
- Edit pack.

### 8.9 Pack Detail

Purpose:

Make pack behavior understandable.

Sections:

- Overview.
- Consent and disclaimer.
- Policy.
- Items.
- Scoring.
- Safety hooks.
- Export schema.

For item list:

- Item ID.
- Text.
- Response type.
- Required.
- Locked wording.
- Tags.
- Anchor count.

Developer mode:

- Raw JSON viewer.

### 8.10 Export Review

Purpose:

Review completed assessment records.

Components:

- Export list.
- Export metadata.
- Pack details.
- Session state.
- Responses.
- Score.
- Safety events.
- Raw JSON preview.

Current backend gap:

- There is no export listing API.

Recommended backend additions:

- `GET /exports`
- `GET /exports/{session_id}`

## 9. Component Inventory

### 9.1 Global Components

- App shell.
- Sidebar navigation.
- Runtime status badge.
- Mode badge.
- Status badge.
- Empty state.
- Error banner.
- Loading skeleton.

### 9.2 Session Components

- Pack picker.
- Metadata form.
- Prompt panel.
- Answer composer.
- Anchor choice group.
- Voice capture button.
- Confirmation panel.
- Progress rail.
- Transcript timeline.
- Response summary table.
- Safety protocol panel.
- Score summary.

### 9.3 Pack Components

- Pack card.
- Pack policy table.
- Item table.
- Anchor list.
- Safety hook list.
- Scoring band list.
- JSON preview.

### 9.4 Export Components

- Export table.
- Export detail header.
- Response record list.
- Audit event list.
- JSON viewer.

## 10. Data and API Mapping

### 10.1 Pack List

Endpoint:

`GET /packs`

UI data:

- `id`
- `version`
- `title`
- `mode`
- `language`

Needed later:

- Item count.
- Licensing warning.
- Safety hook count.
- Scoring method.

### 10.2 Start Session

Endpoint:

`POST /sessions`

Request:

```json
{
  "pack_id": "phq9_demo",
  "metadata": {}
}
```

Response:

- `session`
- `prompt`

UI behavior:

- Store current `session.id`.
- Render `prompt.text`.
- Initialize progress using `session.current_index`.

### 10.3 Submit Utterance

Endpoint:

`POST /sessions/{session_id}/utterance`

Request:

```json
{
  "text": "several days"
}
```

Response:

- Updated `session`
- Next `prompt`

UI behavior:

- Append user turn locally.
- Render backend prompt.
- Branch by `session.status`.

### 10.4 Confirm Answer

Endpoint:

`POST /sessions/{session_id}/confirmation`

Confirm request:

```json
{
  "accepted": true
}
```

Correction request:

```json
{
  "accepted": false,
  "corrected_text": "not at all"
}
```

UI behavior:

- Use `session.pending_answer` and `prompt.metadata.answer` when present.
- After response, return to active prompt or complete/safety state.

### 10.5 Get Session

Endpoint:

`GET /sessions/{session_id}`

UI behavior:

- Resume session detail.
- Refresh state after reload.

Current limitation:

- The response does not include the current prompt, so the UI may need to reconstruct the active screen from state or request a future endpoint.

Recommended backend addition:

- `GET /sessions/{session_id}/prompt`
- Or include prompt in `GET /sessions/{session_id}`.

## 11. Visual Design Direction

### 11.1 Tone

Shrutilens should feel:

- Trustworthy.
- Quiet.
- Precise.
- Human.
- Locally controlled.

It should not feel:

- Like a marketing landing page.
- Like a generic chatbot.
- Overly clinical to the point of intimidation.
- Decorative or playful during safety-sensitive moments.

### 11.2 Layout Density

Use a professional tool layout:

- Compact sidebar.
- Dense but readable tables.
- Large current prompt region.
- Persistent session context.
- Minimal decorative imagery.

### 11.3 Color System

Recommended palette:

- Background: near-white or soft neutral.
- Surface: white.
- Text: deep neutral.
- Muted text: gray.
- Primary action: clear blue or teal.
- Success/completed: green.
- Warning/confirmation: amber.
- Safety interruption: red with restrained use.
- Research mode accent: teal.
- Clinical mode accent: blue.

Avoid making the entire app one dominant hue.

### 11.4 Typography

Use a modern system sans-serif stack:

```css
font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

Recommended hierarchy:

- Page title: 24-28px.
- Section title: 16-18px.
- Prompt text: 22-28px depending on viewport.
- Body/table text: 14-15px.
- Metadata labels: 12-13px.

### 11.5 Status Colors

Session states:

- `in_progress`: blue.
- `awaiting_confirmation`: amber.
- `completed`: green.
- `safety_interrupted`: red.

Mode states:

- `clinical_locked`: blue.
- `research_flexible`: teal.

## 12. Interaction Design

### 12.1 Answer Entry

The UI should support three answer paths:

- Text input.
- Anchor button selection.
- Future microphone capture.

For anchored clinical items:

- Anchor buttons should be visible and keyboard accessible.
- Text input should remain available for transcription or typed natural language.
- Selecting an anchor can submit the anchor label as utterance text.

For free-text research items:

- Use a multiline text area.
- Support Cmd/Ctrl+Enter to submit.
- Preserve drafts during API calls.

### 12.2 Voice-First Future

Future voice UI should include:

- Microphone permission state.
- Recording state.
- Live transcript preview.
- Stop/cancel controls.
- "Use transcript" confirmation before submission.
- Audio recording off by default, aligned with current disclaimer.

### 12.3 Loading and Error States

Loading states:

- Loading packs.
- Starting session.
- Submitting answer.
- Confirming answer.
- Fetching session.

Error states:

- API offline.
- Pack not found.
- Session not found.
- Submission failed.
- Export unavailable.

Errors should preserve user text drafts.

### 12.4 Keyboard Accessibility

Required shortcuts:

- Tab through controls.
- Enter to select focused anchor.
- Cmd/Ctrl+Enter to submit text.
- Escape to cancel correction.

Do not rely on hover-only interactions.

## 13. Accessibility Requirements

- WCAG AA contrast minimum.
- Visible focus states.
- Proper labels for all inputs and buttons.
- Status changes announced to screen readers.
- Safety interruption should use an assertive live region.
- Anchor choices should use radio-group semantics where applicable.
- Do not use color alone to communicate session state.

## 14. Privacy and Safety Requirements

### 14.1 Local Data Visibility

The UI should show that:

- Sessions are stored locally in SQLite.
- Audit logs are stored locally as JSONL.
- Exports are stored locally as JSON.

This can live in Settings and export detail screens.

### 14.2 Clinical Caution

For `phq9_demo`, the UI should surface:

- Demo status.
- Licensing caution.
- Not a diagnosis.
- Not an emergency service.

### 14.3 Safety Protocol

When interrupted:

- Normal session progression stops.
- The backend message is shown.
- Emergency guidance is visible.
- Export/review is allowed.
- Continuing normal questions is not allowed without a deliberate future policy.

## 15. Future Feature Roadmap

### 15.1 Near-Term UI Features

- Pack list and detail screens.
- Start session flow.
- Active session runner.
- Confirmation panel.
- Completion review.
- Safety interruption screen.
- Session resume by ID.
- Basic export preview.

### 15.2 Near-Term Backend Features Needed by UI

- List sessions endpoint.
- List exports endpoint.
- Fetch export by session ID.
- Include current prompt in session fetch.
- Include item count/progress metadata in pack list.
- Return current item schema with anchors in prompt response.

### 15.3 Medium-Term Product Features

- Voice capture and transcription.
- Branching support in main `shrutilens` engine.
- Clarification state support.
- Skip handling for skippable items.
- Richer response controls:
  - Single choice.
  - Multi-select.
  - Rating.
  - Numeric.
  - Boolean.
  - Open text.
- Interviewer notes.
- Session search and filters.
- Export download from UI.
- Audit log viewer.
- Pack validation screen.

### 15.4 Advanced Future Features

- Pack authoring and preview.
- Visual branch map for packs.
- Version comparison between packs.
- Human review queue.
- Redaction tools for transcripts.
- Summary generation for research sessions.
- Configurable model profiles.
- Offline speech-to-text integration.
- Multi-language pack support.
- Role-based views for participant, facilitator, and developer.
- Organization/team storage layer.
- Encrypted local storage.
- Import/export pack marketplace.

### 15.5 Clinical Future Features

These require careful policy, legal, and clinical review:

- Verified clinical pack licensing.
- Clinician handoff workflow.
- Safety escalation contacts.
- Jurisdiction-aware crisis resources.
- Immutable audit reports.
- Signed assessment exports.
- Configurable consent templates.

## 16. Recommended MVP UI Scope

The first production-quality UI should include:

1. App shell with Sessions, Packs, Exports, Settings.
2. Pack list from `GET /packs`.
3. New session flow using `POST /sessions`.
4. Active session runner using utterance and confirmation endpoints.
5. Clinical anchor buttons for `frequency_0_3` items.
6. Free-text answer box for research interviews.
7. Confirmation panel for low-confidence clinical answers.
8. Safety interruption screen.
9. Completion review with score and responses.
10. Minimal developer JSON viewer for current session.

The MVP can defer:

- Full session list.
- Full export browser.
- Voice recording.
- Pack editing.
- Authentication.
- Analytics.

## 17. Suggested Frontend Architecture

### 17.1 Technology Direction

Recommended stack:

- React or Next.js for UI.
- TypeScript for API contracts.
- TanStack Query for API state.
- Zustand or reducer-based local state for active session UI state.
- Zod schemas generated or mirrored from backend models.

### 17.2 Page Structure

```text
src/
  app/
    sessions/
    packs/
    exports/
    settings/
  components/
    app-shell/
    session/
    packs/
    exports/
    status/
  lib/
    api.ts
    contracts.ts
    session-state.ts
```

### 17.3 API Client Shape

```ts
type SessionStatus =
  | "in_progress"
  | "awaiting_confirmation"
  | "safety_interrupted"
  | "completed";

type PackMode = "clinical_locked" | "research_flexible";
```

The frontend should centralize status branching so individual components do not each reimplement backend state logic.

## 18. Open Questions

- Should the UI be participant-facing, facilitator-facing, or both for the first release?
- Should sessions be resumable only by ID, or should the backend expose a searchable session index?
- Should exports be opened directly from disk, served by API, or both?
- Will voice transcription happen in-browser, through a local service, or through a model provider?
- Should the main `shrutilens` engine absorb `voice_assessor` branching and clarification concepts, or should the UI support both engines separately?
- What clinical safety copy should be approved for non-demo use?

## 19. Implementation Sequence

Recommended order:

1. Add backend support for listing sessions and returning current prompts.
2. Build pack list and new session flow.
3. Build active session UI for text entry.
4. Add anchored response controls.
5. Add confirmation flow.
6. Add completion review.
7. Add safety interruption view.
8. Add export preview.
9. Add voice capture prototype.
10. Add future branching/clarification support.

## 20. Success Criteria

The UI is successful when:

- A user can start and complete `phq9_demo` without using Swagger UI.
- A user can start and complete `product_discovery_demo` without using Swagger UI.
- Low-confidence answers trigger a clear confirmation flow.
- Safety interruption is obvious, calm, and blocks normal continuation.
- Completed sessions show responses and score/export state.
- The UI never hides deterministic scoring or safety behavior behind vague AI language.
- The product feels like a serious local assessment tool, not a generic chatbot wrapper.

