# RunLens — Project Brief for Claude Code

## What is RunLens

RunLens is a debugging and optimization layer for AI agents. It helps technical teams
understand why an agent run produced an incorrect or costly outcome, identify which
decision caused the issue, and improve future runs efficiently.

The core insight: most observability tools (LangSmith, Langfuse, Helicone) show
**what happened**. RunLens shows **what changed and how to improve it**.

---

## Problem being solved

Teams building tool-using AI agents rely on logs, prompts, and trial-and-error to debug
their systems. When a run fails or becomes expensive, they can't clearly see:

- Which step caused the issue
- What changed between two runs (prompt? model? tool config? logic?)
- Where cost increased and why
- How to reproduce and fix the problem without guessing

### Key gap vs existing tools

LangSmith and similar tools have a structural problem: they version prompts but not the
surrounding code and configuration. Git versions the code but knows nothing about the
prompt. **Nobody connects both.** When something breaks in production, you don't know
if it was the prompt change or the code refactor.

RunLens solves this by capturing a full context snapshot at run time — not as a version
control system, but as metadata attached to every run. This makes run comparison
genuinely useful: you see not just that the output changed, but exactly what was
different in the execution context.

---

## Target user

Technical PMs and engineers in small teams building tool-using AI agents. They are
currently in active iteration — not monitoring production at scale, but debugging and
improving their agent logic.

**They are NOT necessarily LangChain users.** RunLens must be framework-agnostic.

---

## Product phases

### Phase 1 (current focus)
- Ingest runs and steps via SDK
- Inspect run timelines step by step
- Analyze cost by step
- Compare two runs side by side, including context diff

### Phase 2
- Highlight key decisions and failure points
- Surface insights across runs

### Phase 3
- Fork runs, modify steps, re-run flows
- Validate improvements

**Build Phase 1 only. Do not add Phase 2/3 features prematurely.**

---

## Repository structure

```
runlens/
├── apps/
│   ├── api/          — FastAPI backend
│   └── web/          — Frontend (web)
├── packages/
│   └── sdk-python/   — Minimal Python SDK
├── docs/             — Product definition and design docs
└── examples/         — Sample agents and runs
```

---

## SDK design (packages/sdk-python)

### Three functions only

```python
run = start_run(task='example', context={...})
record_step(run_id=run.id, step_type='llm_call', input={}, output={}, cost=0.02)
end_run(run.id)
```

### The `context` parameter (key differentiator)

`start_run()` accepts an optional `context` dict. This is where the developer captures
the execution state at the moment of the run. Example:

```python
run = start_run(
    task='answer_question',
    context={
        'model': 'gpt-4o',
        'prompt_version': 'v3',
        'tools': ['search', 'calculator'],
        'temperature': 0.7,
        'agent_version': '1.2.0',
    }
)
```

This context is stored with the run and displayed in the comparison view, so when two
runs are compared, the diff shows not just output differences but what was different in
the configuration that produced them.

**This is the core differentiator vs LangSmith**: LangSmith versions prompts separately
from code. RunLens captures both in the same run snapshot, making the comparison
actionable.

### SDK principles
- `context` is always optional — the SDK works without it
- No dependency on any agent framework (no LangChain, no LlamaIndex, etc.)
- No automatic instrumentation or monkey-patching
- Works with any Python agent setup
- Integrable in minutes

---

## Backend design (apps/api)

FastAPI. Keep it simple for Phase 1:

- `POST /runs` — create a run
- `POST /runs/{run_id}/steps` — record a step
- `PATCH /runs/{run_id}` — end a run
- `GET /runs` — list runs
- `GET /runs/{run_id}` — get run with all steps
- `GET /runs/compare?run_a={id}&run_b={id}` — compare two runs, including context diff

Use SQLite for Phase 1. Do not over-engineer storage.

---

## Frontend design (apps/web)

Phase 1 UI has three views:

1. **Run list** — all runs, with task, status, total cost, duration
2. **Run detail** — step-by-step timeline with cost per step
3. **Run comparison** — two runs side by side:
   - Context diff (what was different: model, prompt version, tools, etc.)
   - Step-by-step comparison
   - Cost diff per step
   - Output diff

The comparison view is the most important screen. It is the product.

---

## What NOT to do

- Do not add auto-instrumentation or magic decorators in Phase 1
- Do not build a prompt versioning system (that's LangSmith's job)
- Do not add authentication in Phase 1
- Do not use a heavy database — SQLite is enough for Phase 1
- Do not couple the SDK to the backend — the SDK should work standalone (local storage)
  and optionally send data to the API
- Do not add features beyond Phase 1 scope without explicit instruction

---

## Competitive context (for design decisions)

- **LangSmith**: observability + prompt versioning, tightly coupled to LangChain in
  practice, versions prompts but not code, free tier exhausted quickly, UI complex
- **Langfuse**: open source alternative, more flexible, but same fundamental limitation:
  shows what happened, not what changed
- **RunLens position**: the tool that connects prompt + code + config into a single run
  snapshot, enabling structured comparison and iteration

---

## Definition of done for Phase 1

- [ ] SDK installable via pip with the 3 functions + context support
- [ ] Backend running locally with SQLite
- [ ] Run list view working
- [ ] Run detail view with step timeline and cost per step
- [ ] Run comparison view with context diff
- [ ] At least one example agent in /examples using the SDK
