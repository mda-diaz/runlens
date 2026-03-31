import json
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from runlens.sdk import start_run, record_step, end_run, _active_runs, _steps


def teardown_function():
    """Clean up any leaked runs between tests."""
    _active_runs.clear()
    _steps.clear()


# ---------------------------------------------------------------------------
# start_run
# ---------------------------------------------------------------------------

def test_start_run_returns_handle_with_id():
    run = start_run(task="test task")
    assert run.id
    assert run.task == "test task"
    end_run(run.id)


def test_start_run_stores_context():
    ctx = {"model": "gpt-4o", "prompt_version": "v2", "temperature": 0.5}
    run = start_run(task="ctx test", context=ctx)
    assert run.context == ctx
    end_run(run.id)


def test_start_run_context_is_optional():
    run = start_run(task="no context")
    assert run.context == {}
    end_run(run.id)


def test_start_run_registers_in_memory():
    run = start_run(task="memory test")
    assert run.id in _active_runs
    end_run(run.id)


# ---------------------------------------------------------------------------
# record_step
# ---------------------------------------------------------------------------

def test_record_step_adds_step():
    run = start_run(task="step test")
    record_step(run.id, "llm_call", input={"prompt": "hi"}, output={"text": "hello"}, cost=0.01)
    assert len(_steps[run.id]) == 1
    end_run(run.id)


def test_record_step_sequence_increments():
    run = start_run(task="sequence test")
    record_step(run.id, "llm_call", input={}, output={})
    record_step(run.id, "tool_call", input={}, output={})
    record_step(run.id, "llm_call", input={}, output={})
    sequences = [s["sequence"] for s in _steps[run.id]]
    assert sequences == [1, 2, 3]
    end_run(run.id)


def test_record_step_captures_cost_and_tokens():
    run = start_run(task="cost test")
    record_step(run.id, "llm_call", input={}, output={}, cost=0.05, tokens=500)
    step = _steps[run.id][0]
    assert step["cost"] == 0.05
    assert step["tokens"] == 500
    end_run(run.id)


def test_record_step_unknown_run_raises():
    with pytest.raises(ValueError, match="not found"):
        record_step("nonexistent-id", "llm_call", input={}, output={})


def test_record_step_uses_step_type_as_default_name():
    run = start_run(task="name test")
    record_step(run.id, "retrieval", input={}, output={})
    assert _steps[run.id][0]["name"] == "retrieval"
    end_run(run.id)


def test_record_step_custom_name():
    run = start_run(task="custom name")
    record_step(run.id, "tool_call", input={}, output={}, name="search_web")
    assert _steps[run.id][0]["name"] == "search_web"
    end_run(run.id)


# ---------------------------------------------------------------------------
# end_run
# ---------------------------------------------------------------------------

def test_end_run_returns_completed_record():
    run = start_run(task="end test")
    result = end_run(run.id)
    assert result["id"] == run.id
    assert result["status"] == "completed"
    assert result["task"] == "end test"


def test_end_run_aggregates_cost_and_tokens():
    run = start_run(task="aggregate test")
    record_step(run.id, "llm_call", input={}, output={}, cost=0.02, tokens=200)
    record_step(run.id, "tool_call", input={}, output={}, cost=0.00, tokens=0)
    record_step(run.id, "llm_call", input={}, output={}, cost=0.03, tokens=300)
    result = end_run(run.id)
    assert result["total_cost"] == pytest.approx(0.05)
    assert result["total_tokens"] == 500


def test_end_run_includes_steps():
    run = start_run(task="steps in result")
    record_step(run.id, "llm_call", input={"q": "hello"}, output={"text": "world"})
    result = end_run(run.id)
    assert len(result["steps"]) == 1
    assert result["steps"][0]["step_type"] == "llm_call"


def test_end_run_preserves_context():
    ctx = {"model": "claude-3-5-sonnet", "prompt_version": "v1"}
    run = start_run(task="ctx preserve", context=ctx)
    result = end_run(run.id)
    assert result["context"] == ctx


def test_end_run_cleans_up_memory():
    run = start_run(task="cleanup test")
    end_run(run.id)
    assert run.id not in _active_runs
    assert run.id not in _steps


def test_end_run_unknown_run_raises():
    with pytest.raises(ValueError, match="not found"):
        end_run("nonexistent-id")


def test_end_run_records_duration():
    run = start_run(task="duration test")
    result = end_run(run.id)
    assert result["duration_ms"] >= 0


# ---------------------------------------------------------------------------
# Local storage persistence
# ---------------------------------------------------------------------------

def test_end_run_writes_to_storage_path(tmp_path):
    storage = str(tmp_path / "runs.json")
    run = start_run(task="persist test", context={"v": 1}, storage_path=storage)
    record_step(run.id, "llm_call", input={}, output={}, cost=0.01)
    end_run(run.id)

    data = json.loads(Path(storage).read_text())
    assert len(data) == 1
    assert data[0]["task"] == "persist test"
    assert data[0]["total_cost"] == pytest.approx(0.01)


def test_end_run_appends_to_existing_storage_file(tmp_path):
    storage = str(tmp_path / "runs.json")
    for i in range(3):
        run = start_run(task=f"run {i}", storage_path=storage)
        end_run(run.id)

    data = json.loads(Path(storage).read_text())
    assert len(data) == 3
    assert [r["task"] for r in data] == ["run 0", "run 1", "run 2"]
