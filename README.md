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

## Vision
Most tools show what happened.
RunLens shows what changed and how to improve it.
