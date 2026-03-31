import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from models import Run, Step

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class RunCreate(BaseModel):
    id: Optional[str] = None
    task_name: str
    context: Optional[Dict[str, Any]] = None
    status: str = "running"


class RunUpdate(BaseModel):
    status: Optional[str] = None
    total_cost: Optional[float] = None
    total_tokens: Optional[int] = None
    duration_ms: Optional[int] = None
    ended_at: Optional[datetime] = None


def _serialize_run(run: Run) -> dict:
    return {
        "id": run.id,
        "task_name": run.task_name,
        "status": run.status,
        "context": json.loads(run.context) if run.context else {},
        "total_cost": run.total_cost,
        "total_tokens": run.total_tokens,
        "duration_ms": run.duration_ms,
        "created_at": run.created_at,
        "ended_at": run.ended_at,
    }


def _serialize_step(step: Step) -> dict:
    return {
        "id": step.id,
        "run_id": step.run_id,
        "sequence": step.sequence,
        "step_type": step.step_type,
        "name": step.name,
        "input": json.loads(step.input) if step.input else None,
        "output": json.loads(step.output) if step.output else None,
        "cost": step.cost,
        "tokens": step.tokens,
        "duration_ms": step.duration_ms,
        "recorded_at": step.recorded_at,
    }


# ---------------------------------------------------------------------------
# POST /runs
# ---------------------------------------------------------------------------

@router.post("/runs", status_code=201)
def create_run(body: RunCreate, session: Session = Depends(get_session)):
    run = Run(
        task_name=body.task_name,
        status=body.status,
        context=json.dumps(body.context) if body.context else None,
    )
    if body.id:
        run.id = body.id
    session.add(run)
    session.commit()
    session.refresh(run)
    return _serialize_run(run)


# ---------------------------------------------------------------------------
# GET /runs
# ---------------------------------------------------------------------------

@router.get("/runs")
def list_runs(session: Session = Depends(get_session)):
    runs = session.exec(select(Run).order_by(Run.created_at.desc())).all()
    return [_serialize_run(r) for r in runs]


# ---------------------------------------------------------------------------
# GET /runs/compare  — must be declared before /runs/{run_id}
# ---------------------------------------------------------------------------

@router.get("/runs/compare")
def compare_runs(
    run_a: str = Query(...),
    run_b: str = Query(...),
    session: Session = Depends(get_session),
):
    def get_run_with_steps(run_id: str):
        run = session.get(Run, run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
        steps = session.exec(
            select(Step).where(Step.run_id == run_id).order_by(Step.sequence)
        ).all()
        return run, steps

    run_a_obj, steps_a = get_run_with_steps(run_a)
    run_b_obj, steps_b = get_run_with_steps(run_b)

    ctx_a: dict = json.loads(run_a_obj.context) if run_a_obj.context else {}
    ctx_b: dict = json.loads(run_b_obj.context) if run_b_obj.context else {}

    all_keys = set(ctx_a) | set(ctx_b)
    context_diff = {}
    for key in sorted(all_keys):
        val_a = ctx_a.get(key)
        val_b = ctx_b.get(key)
        if val_a != val_b:
            context_diff[key] = {"run_a": val_a, "run_b": val_b}

    return {
        "run_a": {**_serialize_run(run_a_obj), "steps": [_serialize_step(s) for s in steps_a]},
        "run_b": {**_serialize_run(run_b_obj), "steps": [_serialize_step(s) for s in steps_b]},
        "context_diff": context_diff,
        "cost_diff": round(run_b_obj.total_cost - run_a_obj.total_cost, 6),
        "token_diff": run_b_obj.total_tokens - run_a_obj.total_tokens,
    }


# ---------------------------------------------------------------------------
# GET /runs/{run_id}
# ---------------------------------------------------------------------------

@router.get("/runs/{run_id}")
def get_run(run_id: str, session: Session = Depends(get_session)):
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    steps = session.exec(
        select(Step).where(Step.run_id == run_id).order_by(Step.sequence)
    ).all()
    return {**_serialize_run(run), "steps": [_serialize_step(s) for s in steps]}


# ---------------------------------------------------------------------------
# PATCH /runs/{run_id}
# ---------------------------------------------------------------------------

@router.patch("/runs/{run_id}")
def update_run(run_id: str, body: RunUpdate, session: Session = Depends(get_session)):
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(run, field, value)
    session.add(run)
    session.commit()
    session.refresh(run)
    return _serialize_run(run)
