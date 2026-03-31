import uuid
import time
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RunHandle:
    id: str
    task: str
    context: Dict[str, Any]
    _started_at: float = field(repr=False)
    _api_url: Optional[str] = field(default=None, repr=False)
    _storage_path: Optional[str] = field(default=None, repr=False)


# Module-level in-memory stores
_active_runs: Dict[str, "RunHandle"] = {}
_steps: Dict[str, List[dict]] = {}


def start_run(
    task: str,
    context: Optional[Dict[str, Any]] = None,
    api_url: Optional[str] = None,
    storage_path: Optional[str] = None,
) -> RunHandle:
    """Start a new agent run. Returns a RunHandle whose .id is used in subsequent calls.

    Args:
        task: Short description of what this run is doing.
        context: Optional dict capturing the execution state (model, prompt version,
                 tools, temperature, etc.). This is the key differentiator for comparison.
        api_url: Optional RunLens API base URL to stream data to.
        storage_path: Optional path to a local JSON file for persistence.
    """
    run_id = str(uuid.uuid4())
    handle = RunHandle(
        id=run_id,
        task=task,
        context=context or {},
        _started_at=time.time(),
        _api_url=api_url,
        _storage_path=storage_path,
    )
    _active_runs[run_id] = handle
    _steps[run_id] = []

    if api_url:
        _post(
            f"{api_url}/runs",
            {
                "id": run_id,
                "task_name": task,
                "context": json.dumps(context or {}),
                "status": "running",
            },
        )

    return handle


def record_step(
    run_id: str,
    step_type: str,
    input: Any,
    output: Any,
    cost: float = 0.0,
    tokens: int = 0,
    name: Optional[str] = None,
    duration_ms: Optional[int] = None,
) -> None:
    """Record a single step within a run.

    Args:
        run_id: The id from the RunHandle returned by start_run().
        step_type: Category of step, e.g. "llm_call", "tool_call", "retrieval".
        input: The input to this step (any JSON-serialisable value).
        output: The output of this step (any JSON-serialisable value).
        cost: Cost in USD for this step.
        tokens: Token count for this step.
        name: Optional human-readable label. Defaults to step_type.
        duration_ms: Optional wall-clock duration in milliseconds.
    """
    if run_id not in _active_runs:
        raise ValueError(f"Run '{run_id}' not found. Call start_run() first.")

    steps = _steps[run_id]
    step = {
        "id": str(uuid.uuid4()),
        "run_id": run_id,
        "sequence": len(steps) + 1,
        "step_type": step_type,
        "name": name or step_type,
        "input": input,
        "output": output,
        "cost": cost,
        "tokens": tokens,
        "duration_ms": duration_ms,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    steps.append(step)

    api_url = _active_runs[run_id]._api_url
    if api_url:
        _post(f"{api_url}/runs/{run_id}/steps", step)


def end_run(run_id: str) -> dict:
    """End a run and return the completed run record.

    Persists to local storage and/or the API if configured in start_run().
    """
    if run_id not in _active_runs:
        raise ValueError(f"Run '{run_id}' not found. Call start_run() first.")

    handle = _active_runs[run_id]
    steps = _steps[run_id]
    now = time.time()

    record = {
        "id": run_id,
        "task": handle.task,
        "context": handle.context,
        "status": "completed",
        "steps": steps,
        "total_cost": round(sum(s["cost"] for s in steps), 6),
        "total_tokens": sum(s["tokens"] for s in steps),
        "duration_ms": int((now - handle._started_at) * 1000),
        "started_at": datetime.fromtimestamp(handle._started_at, tz=timezone.utc).isoformat(),
        "ended_at": datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
    }

    if handle._storage_path:
        _append_to_file(handle._storage_path, record)

    if handle._api_url:
        _patch(
            f"{handle._api_url}/runs/{run_id}",
            {
                "status": "completed",
                "total_cost": record["total_cost"],
                "total_tokens": record["total_tokens"],
                "duration_ms": record["duration_ms"],
            },
        )

    del _active_runs[run_id]
    del _steps[run_id]

    return record


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _post(url: str, payload: dict) -> None:
    try:
        import requests
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass  # SDK never crashes the agent


def _patch(url: str, payload: dict) -> None:
    try:
        import requests
        requests.patch(url, json=payload, timeout=5)
    except Exception:
        pass


def _append_to_file(path: str, record: dict) -> None:
    p = Path(path)
    runs: List[dict] = []
    if p.exists():
        try:
            runs = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            runs = []
    runs.append(record)
    p.write_text(json.dumps(runs, indent=2, default=str))
