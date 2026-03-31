# RunLens

**Debug AI agents like systems, not black boxes.**

RunLens helps you understand why an agent run failed or became expensive — and what to fix. It captures runs step by step, shows cost per step, and lets you compare two runs side by side to see exactly what changed.

👉 **[Live demo](https://runlens-api.onrender.com)**

---

## The problem

When an agent fails or costs too much, existing tools show you *what happened* — logs, traces, token counts. But they don't tell you *what changed* between runs or *which decision caused the issue*.

RunLens adds a comparison layer: you instrument your agent with 3 functions, run it twice with different configs, and see exactly what was different — model, prompt version, tools, temperature — alongside the cost and step diff.

---

## How it works

```
your agent → RunLens SDK → RunLens API → RunLens UI
```

You add 3 function calls to your agent. RunLens records every step, stores it, and lets you compare runs visually.

---

## Quickstart

### 1. Start the API

```bash
git clone https://github.com/mda-diaz/runlens.git
cd runlens/apps/api
pip install -r requirements.txt
uvicorn main:app --reload
```

API runs at `http://localhost:8000`.

### 2. Instrument your agent

```python
from packages.sdk_python.runlens.sdk import start_run, record_step, end_run

# Start a run — capture your execution context
run = start_run(
    task="answer customer question",
    context={
        "model": "gpt-4o",
        "prompt_version": "v2",
        "tools": ["search", "calculator"],
        "temperature": 0.7,
    },
    api_url="http://localhost:8000",
)

# Record each step
record_step(
    run_id=run.id,
    step_type="llm_call",
    name="classify intent",
    input={"prompt": "..."},
    output={"intent": "refund_request"},
    cost=0.002,
    tokens=150,
)

# End the run
end_run(run.id)
```

### 3. Open the UI

Open `apps/web/index.html` in your browser. Select two runs and click **Compare**.

---

## The comparison view

When you compare two runs, RunLens shows:

**Context diff** — what was different between the two runs:
| Key | Run A | Run B |
|-----|-------|-------|
| model | gpt-4o | gpt-4o-mini |
| prompt_version | v1 | v2 |
| temperature | 0.7 | 0.3 |

**Summary** — steps, cost, tokens, duration delta at a glance.

**Step diff** — side by side steps, with extra/missing steps flagged in red.

---

## Run the demo

See a concrete example: a support bot running the same task twice — once over-engineered, once lean. 5x cost difference, same output.

```bash
pip install requests
python examples/demo_agent.py
```

Then open `apps/web/index.html`, select both runs, and click Compare.

---

## Project structure

```
runlens/
├── apps/
│   ├── api/          — FastAPI backend (SQLite)
│   └── web/          — Frontend (plain HTML + JS)
├── packages/
│   └── sdk-python/   — Python SDK
├── examples/
│   └── demo_agent.py — Demo: support bot comparison
└── CLAUDE.md         — Project brief for AI-assisted development
```

---

## SDK reference

### `start_run(task, context=None, api_url=None, storage_path=None)`

Starts a new run. Returns a `RunHandle` with an `.id`.

- `task` — short description of what the agent is doing
- `context` — dict with execution state: model, prompt version, tools, etc.
- `api_url` — RunLens API base URL (optional, streams data to API)
- `storage_path` — local JSON file path (optional, saves data locally)

### `record_step(run_id, step_type, input, output, cost, tokens=0, name=None, duration_ms=None)`

Records a single step within a run.

- `step_type` — e.g. `"llm_call"`, `"tool_call"`, `"retrieval"`
- `cost` — cost in USD for this step
- `tokens` — token count for this step

### `end_run(run_id)`

Ends the run and returns the complete run record.

---

## Self-hosting

The API is a standard FastAPI app. Deploy anywhere that runs Python:

```bash
# Render, Railway, Fly.io, etc.
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Uses SQLite by default. Set `DATABASE_URL` environment variable to use a different database.

---

## Tech stack

- **SDK** — pure Python, zero dependencies
- **Backend** — FastAPI + SQLModel + SQLite
- **Frontend** — plain HTML + vanilla JS, no framework

---

## License

MIT
