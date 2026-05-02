# Shrutilens

Shrutilens is a local-first, audio-first structured conversational assessment runtime. The current MVP skeleton proves the core engine without locking the product to psychiatry:

- Pluggable assessment packs in JSON
- `clinical_locked` and `research_flexible` modes
- Deterministic answer normalization, scoring, and safety gates
- SQLite session persistence
- JSONL audit logs
- JSON export artifacts
- FastAPI session API
- OpenRouter hidden behind a `ModelClient` abstraction

The LLM is intentionally not used for clinical scoring, branching, item order, or crisis handling.

## Run

```bash
uv run shrutilens --port 8000
```

Then open:

```text
http://127.0.0.1:8000/docs
```

## Test

```bash
uv run pytest
```

## Demo Packs

- `phq9_demo`: locked clinical demo pack with deterministic sum scoring and self-harm interruption. This is for architecture validation only; verify licensing and wording before clinical use.
- `product_discovery_demo`: flexible research interview pack with free-text responses.

## Storage

- SQLite: `data/shrutilens.sqlite3`
- Audit JSONL: `data/audit/*.jsonl`
- Exports: `exports/*.json`
