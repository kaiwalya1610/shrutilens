# Agent Context: Audio-First Conversational Assessment Platform

## High-Level Vision

I am building an audio-first conversational assessment platform.

The primary use case is psychiatric evaluation: the system should conduct structured, clinically valid psychiatric assessments through natural spoken conversation. It should guide users through validated instruments such as PHQ-9, GAD-7, PCL-5, ASQ, AUDIT-C, and related screeners while preserving scoring fidelity, item integrity, safety handling, consent, and auditability.

However, the platform must not be hardcoded only for psychiatry. The deeper product is a domain-agnostic structured conversational assessment engine. Psychiatry is the first and most safety-critical domain pack, but the same engine should also support non-clinical workflows such as market surveys, product discovery interviews, UX research, intake forms, customer feedback calls, educational assessments, and structured interviews.

The core product tension is:

- Validated clinical instruments are rigid by design.
- Spoken conversations need to feel adaptive, humane, and worth completing.
- The system must preserve clinical fidelity where required, while still feeling conversational.
- In non-clinical survey modes, the system can be more flexible, adaptive, and exploratory.

The architecture should solve this by separating:

1. Voice/audio interface
2. Conversation/session state
3. Assessment pack engine
4. Scoring and branching logic
5. Safety/crisis gates
6. LLM rendering and repair
7. Persistence and audit logging
8. Exports and clinician/researcher review

The LLM must not be the source of truth for clinical scoring, clinical branching, crisis escalation, or validated item order. The LLM may help with conversational warmth, reflective transitions, answer normalization, repair prompts, summaries, and non-clinical adaptive probing, but deterministic code must enforce the rules.

## Product Identity

This is not a generic chatbot.

It is an audio-first structured interview runtime with pluggable assessment packs.

The product should feel like:

- A careful voice interviewer
- A structured clinical/research protocol runner
- A modular engine for spoken assessments
- A local-first tool that a solo technical maintainer can run, debug, and extend

It should not feel like:

- A form read aloud
- An unconstrained therapy bot
- A diagnosis generator
- A bloated SaaS architecture
- A tangled prototype where UI, prompts, scoring, and clinical rules live in one file

## Primary Product Modes

The engine should support at least two modes.

### 1. `clinical_locked`

Used for psychiatric and health instruments.

Rules:

- Fixed validated item wording where required
- Fixed item order where required
- Deterministic scoring
- Deterministic skip/branch rules
- Deterministic safety triggers
- Clear consent and disclaimers
- Strict audit log
- User answer confirmation when STT or normalization is uncertain
- LLM cannot override scoring, safety, or instrument logic
- Crisis and self-harm signals interrupt the normal flow

Examples:

- PHQ-9
- GAD-7
- PCL-5
- ASQ
- AUDIT-C
- C-SSRS-style risk triage, subject to licensing and implementation constraints

### 2. `research_flexible`

Used for market surveys, product interviews, customer discovery, and non-clinical structured conversations.

Rules:

- Question order may be configurable
- LLM may ask limited follow-ups
- LLM may paraphrase questions if pack allows
- LLM may probe vague answers within configured limits
- Branching can be deterministic or semi-adaptive
- Scoring may be replaced by tagging, coding, clustering, or summary extraction
- Safety gates still exist, but clinical-grade crisis paths are only activated when relevant

Examples:

- Market survey
- Product discovery interview
- UX research
- Customer support intake
- Hiring screen
- Educational oral quiz

## Audio-First Principle

This platform is audio-first, not text-first.

Text chat may exist for debugging, fallback, accessibility, transcripts, and optional confirmation. But the primary user experience is spoken conversation.

Voice requirements:

- Streaming speech-to-text
- Turn detection
- Barge-in support
- Low-latency responses
- Text-to-speech output
- Live transcript visibility
- Optional tappable answer chips for confirmation
- Audio recording disabled by default unless explicitly enabled
- Transcript and structured records stored by default
- Clear recovery from STT mistakes
- Graceful fallback when the model or TTS fails

The system should not simply take a web form and read each question aloud. The voice layer should support pacing, brief transitions, non-leading reflections, repair questions, and interruption handling.

## Recommended Technical Direction

Use a small, local-first architecture.

Preferred stack for MVP:

- Python
- FastAPI for local HTTP/session API
- Pipecat for voice pipeline orchestration
- SQLite for persistence
- OpenRouter for LLM access using `OPENROUTER_API_KEY`
- Optional LangGraph only if useful for graph state, checkpointing, and resumability
- JSONL logs for audit trail
- JSON export first
- PDF export later
- No Redis unless needed
- No vector database for v1 unless clearly justified
- No cloud microservices by default

The smallest MVP process model should be:

> One FastAPI app + Pipecat voice runtime + SQLite file + JSONL transcript folder + OpenRouter model client.

## LLM Usage Policy

The LLM is a helper, not the authority.

Allowed LLM responsibilities:

- Render conversational bridge text
- Create gentle, non-leading reflections
- Normalize free speech into structured answer candidates
- Generate repair prompts when the answer is ambiguous
- Summarize completed sessions
- Help non-clinical research packs ask limited follow-ups
- Translate or localize wording only when explicitly allowed by the pack

Forbidden LLM responsibilities in clinical mode:

- Changing validated item wording when exact wording is required
- Reordering clinical items unless the instrument allows it
- Scoring independently
- Overriding deterministic score logic
- Downgrading self-harm or crisis risk
- Deciding to skip required clinical questions
- Inventing clinical interpretations
- Diagnosing the user
- Reassuring away a positive suicide/self-harm response

If an LLM call fails:

- Rendering failure should fall back to deterministic text.
- Normalization failure should trigger answer confirmation.
- Safety uncertainty should fail closed.
- Summary failure should not block export of raw structured data.

## OpenRouter Integration

Use OpenRouter as the LLM edge.

Requirements:

- Read API key from `OPENROUTER_API_KEY`
- Hide provider details behind a `ModelClient` abstraction
- Support model profiles such as:
  - `cheap_fast`
  - `careful`
  - `json_normalizer`
  - `summary`
- Support fallback models
- Support request timeouts
- Support basic cost/rate-limit handling
- Mock the HTTP client in tests
- Never scatter OpenRouter calls across business logic

## Assessment Pack Contract

Assessment packs should be data/config first, with code extensions only where necessary.

A pack should define:

- `id`
- `version`
- `mode`
- `language`
- licensing notes
- consent requirements
- item list
- allowed response types
- response anchors
- scoring method
- branch rules
- safety hooks
- whether paraphrasing is allowed
- whether adaptive follow-up is allowed
- whether answer confirmation is required
- export schema

Clinical pack example behavior:

- The pack says item text is locked.
- The runner asks the exact item.
- The user answers by voice.
- The normalizer maps the utterance to an anchor.
- If confidence is low, the user confirms.
- The deterministic scorer computes the score.
- Safety gate checks item-level triggers.
- The graph advances.

Research pack example behavior:

- The pack defines question goals.
- The renderer may paraphrase.
- The LLM may ask up to N follow-ups.
- The engine stores raw transcript, tags, and structured fields.
- The session exports a research summary.

## Safety Requirements

Safety is non-negotiable.

The system must include deterministic safety gates for clinical packs.

Self-harm or suicide-risk triggers must interrupt ordinary assessment flow. The LLM must never minimize, soften, or ignore a positive self-harm signal.

Safety architecture should include:

1. Deterministic item-level triggers
2. Keyword/phrase triggers
3. Optional LLM-assisted concern detection
4. Crisis protocol path
5. Audit log of trigger and action taken
6. Exportable review packet

Important rule:

> LLMs may add risk flags, but may not clear deterministic risk flags.

## Persistence and Audit

Every session should produce:

- Structured session record
- Turn-by-turn transcript
- Normalized responses
- Scores
- Safety events
- Model calls metadata
- Export artifact

Default storage:

- SQLite for structured state
- JSONL for turn-by-turn audit
- Local `/exports` folder for JSON/PDF output

Avoid storing raw audio by default. If audio recording exists, make it explicit, configurable, and privacy-aware.

## Modularity Goals

The architecture must make it easy to:

- Add a new clinical instrument
- Add a new market survey pack
- Swap STT provider
- Swap TTS provider
- Swap OpenRouter model
- Add a new channel such as CLI, web, websocket, or phone
- Add a new export format
- Add a new safety policy
- Test scoring without audio
- Test conversation flow without LLMs
- Run locally with sane defaults

## Quality Bar

Prefer boring, inspectable, testable code.

Every clinical scoring or branch rule should have golden tests.

A future maintainer should be able to change behavior by editing:

- A pack YAML/JSON file
- A model config file
- A safety policy file
- A renderer prompt file

They should not need to edit a giant orchestration file to add a new instrument.

## Non-Goals for MVP

Do not build these first:

- Full clinician SaaS dashboard
- EHR integration
- FHIR export
- Redis
- Kubernetes
- Multi-tenant auth
- Wearable integrations
- Voice affect detection
- Longitudinal analytics
- Realtime speech-to-speech clinical reasoning
- Diagnosis generation
- Fully autonomous therapy chatbot
- Large RAG system
- Complex marketplace of instruments

## MVP Thesis

The first convincing demo should prove:

1. A user can complete a short structured assessment by voice.
2. The system preserves deterministic item flow and scoring.
3. The system handles STT ambiguity with confirmation.
4. The system creates a structured export and transcript.
5. The same engine can run both:
   - a clinical locked pack, and
   - a flexible market survey pack.

The first implementation should prioritize architecture clarity over feature volume.
