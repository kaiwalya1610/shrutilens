---
marp: true
theme: uncover
paginate: true
math: katex
html: true
size: 16:9
style: |
  :root {
    --bg: #0d1117;
    --fg: #e6edf3;
    --muted: #8b949e;
    --accent: #58a6ff;
    --accent-2: #3fb950;
    --accent-3: #d2a8ff;
    --surface: #161b22;
    --border: #30363d;
  }
  section {
    background: var(--bg);
    color: var(--fg);
    font-family: -apple-system, "SF Pro Display", "Inter", system-ui, sans-serif;
    font-size: 26px;
    padding: 60px 72px;
    text-align: left;
    justify-content: flex-start;
  }
  section.lead {
    text-align: center;
    justify-content: center;
  }
  h1 {
    color: var(--fg);
    font-size: 1.75em;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin: 0 0 0.5em;
    line-height: 1.15;
  }
  section.lead h1 { font-size: 2.4em; }
  h2 { color: var(--accent); font-weight: 600; font-size: 1.05em; margin-top: 0.5em; }
  code {
    background: #21262d;
    color: #79c0ff;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: "SF Mono", "JetBrains Mono", ui-monospace, monospace;
    font-size: 0.85em;
  }
  pre {
    background: #161b22;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 18px;
    font-size: 0.78em;
    line-height: 1.5;
  }
  ul { line-height: 1.55; }
  li::marker { color: var(--accent); }
  .callout {
    border-left: 6px solid var(--accent);
    background: rgba(88, 166, 255, 0.1);
    padding: 12px 16px;
    border-radius: 4px;
    margin: 16px 0;
    font-size: 0.92em;
  }
  .callout-label {
    font-size: 0.72em;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--accent);
  }
  section::after { color: var(--muted); font-size: 0.68em; }
---

<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
  mermaid.initialize({
    startOnLoad: true,
    theme: 'base',
    themeVariables: {
      primaryColor: '#161b22',
      primaryTextColor: '#e6edf3',
      primaryBorderColor: '#58a6ff',
      lineColor: '#8b949e',
      secondaryColor: '#21262d',
      tertiaryColor: '#0d1117',
      background: 'transparent'
    }
  });
</script>

<!-- _class: lead -->
<!-- _paginate: false -->

# **Shrutilens — how this repo runs**
## Your mental map for daily development

<br>

Local-first assessment API · Python 3.13 · uv

---

# The confusion is normal: four stacked layers

<div class="mermaid">
flowchart TB
  subgraph T["Tooling"]
    uv["uv sync / uv run"]
    py["pytest"]
  end
  subgraph S["Shipped app (`shrutilens`)"]
    cli["CLI → uvicorn"]
    api["FastAPI routes"]
    run["AssessmentRunner"]
  end
  subgraph D["Disk"]
    sql["SQLite sessions"]
    aud["JSONL audit"]
    exp["JSON exports"]
  end
  subgraph P["Content"]
    json["`shrutilens/packs/*.json`"]
  end
  T --> S --> D
  P --> run
</div>

<div class="callout">
<span class="callout-label">Analogy</span><br>
uv = app store + launcher. FastAPI = front desk. Runner = the form logic. JSON packs = the form blueprints.
</div>

---

# Commands you actually type

| Intent | Command |
|--------|---------|
| Install deps + project | `UV_NO_EDITABLE=1 uv sync` (see note below) |
| Run API | `uv run shrutilens --port 8000` |
| API docs UI | Open `http://127.0.0.1:8000/docs` |
| Tests | `uv run pytest` |

<div class="callout">
<span class="callout-label">Why UV_NO_EDITABLE?</span><br>
Python 3.13 can skip underscore-leading <code>.pth</code> files — editable installs may not put the package on <code>sys.path</code>. Non-editable sync copies the package into the env so imports always work.
</div>

---

# Request path: one HTTP round-trip

<div class="mermaid">
sequenceDiagram
  participant C as Client / Swagger UI
  participant F as FastAPI (`app.py`)
  participant PR as PackRepository
  participant R as AssessmentRunner
  participant DB as SQLite + audit + exporter

  C->>F: POST /sessions {pack_id}
  F->>PR: load pack JSON
  PR-->>F: AssessmentPack
  F->>R: start(pack, metadata)
  R->>DB: save session, append audit
  R-->>F: SessionState + TurnRecord (prompt)
  F-->>C: JSON response

  C->>F: POST .../utterance {text}
  F->>R: accept_utterance(...)
  R->>DB: normalize log score safety confirm advance
  F-->>C: updated session + next prompt
</div>

---

# What `AssessmentRunner` does (deterministic core)

<div class="mermaid">
flowchart LR
  A["User text"] --> N["DeterministicNormalizer"]
  N --> Q{"Confirmation<br/>needed?"}
  Q -->|yes| W["awaiting_confirmation"]
  Q -->|no| SC["SafetyGate"]
  SC --> S["DeterministicScorer"]
  S --> X{"More items?"}
  X -->|yes| P["next TurnRecord"]
  X -->|no| E["complete + JsonExporter"]
</div>

Scoring, branching policy, and crisis handling stay **code-driven** — not LLM guesses.

---

# Where packs live today

- **`shrutilens/packs/`** — `*.json` files (`phq9_demo.json`, `product_discovery_demo.json`)
- **`PackRepository`** reads file `{pack_id}.json` and validates into **`AssessmentPack`** (Pydantic)

<div class="callout">
<span class="callout-label">Parallel folder</span><br>
<code>voice_assessor/</code> holds a YAML-based loader + runner used heavily by <code>tests/assessment/</code>. README still mentions it as “task 02”; treat it as a second engine track until merged or retired.
</div>

---

# Everything persisted lands under predictable paths

<div class="mermaid">
flowchart TB
  R["AssessmentRunner"]
  R --> SQLite["data/shrutilens.sqlite3"]
  R --> JL["data/audit/*.jsonl"]
  R --> JE["exports/*.json on completion"]
</div>

`build_default_runner(Path("data"), Path("exports"))` wires these — tests use **`tmp_path`** so nothing sticks around.

---

# Tests mirror two concerns

| Area | Location | Checks |
|------|-----------|--------|
| HTTP + wiring | `tests/test_api.py`, `tests/test_runner.py` | API contracts, runner with temp dirs |
| YAML assessment lib | `tests/assessment/` | Pack loader, PHQ9 scoring, safety, golden JSON |

**`tests/conftest.py`** exposes **`pack_repository`** and **`runner`** fixtures pointing at ephemeral **`tmp_path`** data dirs.

---

# Package layout at a glance

```text
shrutilens/
  cli.py              # entry: uvicorn loads api.app
  api/app.py          # REST surface
  core/runner.py      # session loop + persistence hooks
  packs/*.json        # demo packs
  storage/            # SQLite + JSONL audit
voice_assessor/       # YAML packs + standalone assessment modules (parallel track)
```

---

# One picture: from clone to green tests

<div class="mermaid">
flowchart LR
  G["git clone"] --> UV["UV_NO_EDITABLE=1 uv sync"]
  UV --> RUN["uv run shrutilens"]
  RUN --> DOC["/docs interactive"]
  UV --> T["uv run pytest"]
  T --> OK["green"]
</div>

---

# Takeaways

1. **`uv run shrutilens`** starts **FastAPI**; **`AssessmentRunner`** is the brain; packs are **JSON** beside **`shrutilens/packs/`**.
2. **SQLite + JSONL audit + JSON exports** are the three persistence legs — all wired in **`build_default_runner`**.
3. **`voice_assessor/`** + **`tests/assessment/`** are a **parallel YAML assessment stack** — don’t assume they power the HTTP API unless you wire them in.
4. Prefer **`UV_NO_EDITABLE=1`** with Python **3.13** so imports behave reliably.

---

# Render this deck

- **VS Code**: Marp extension → preview the `.md` file.
- **CLI**: `marp docs/shrutilens-development-explained.md -o shrutilens-dev.pdf --html`
