# RunLens

Debug AI agents like systems, not black boxes.

RunLens helps teams understand, compare, and optimize AI agent runs.
It focuses on:
- step-by-step run timelines
- cost per step
- run comparison
- decision-oriented debugging

## Problem
Teams building AI agents often rely on logs and trial-and-error.
They can see that a run failed or became expensive, but not clearly:
- what changed between runs
- which step caused the issue
- where cost increased
- how to improve the flow

## What RunLens does
RunLens is a post-observability layer for AI agents.

Phase 1 focuses on:
- ingesting runs and steps
- inspecting run timelines
- analyzing cost by step
- comparing two runs side by side

## Repository structure
- `apps/api` — FastAPI backend
- `apps/web` — frontend
- `packages/sdk-python` — minimal Python SDK
- `docs` — product definition and design docs
- `examples` — sample agents and runs

## Quickstart

```bash
pip install runlens-sdk
```

```python
from runlens import start_run, record_step, end_run

run = start_run(
    task="answer_question",
    context={"model": "gpt-4o", "prompt_version": "v1"},
    api_url="https://runlens-api.onrender.com",
)

record_step(
    run_id=run.id,
    step_type="llm_call",
    name="answer question",
    input={"prompt": "What is the capital of France?"},
    output={"answer": "Paris"},
    cost=0.000125,
    tokens=25,
)

end_run(run.id)
```

Open [RunLens](https://runlens-api.onrender.com) to inspect the run and compare it against others.

## Vision
Most tools show what happened.
RunLens shows what changed and how to improve it.
