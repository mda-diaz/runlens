import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from models import Run, Step

router = APIRouter()


class StepCreate(BaseModel):
    id: Optional[str] = None
    sequence: Optional[int] = None
    step_type: str
    name: Optional[str] = None
    input: Optional[Any] = None
    output: Optional[Any] = None
    cost: float = 0.0
    tokens: int = 0
    duration_ms: Optional[int] = None


@router.post("/runs/{run_id}/steps", status_code=201)
def create_step(run_id: str, body: StepCreate, session: Session = Depends(get_session)):
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Auto-increment sequence if not provided
    if body.sequence is None:
        existing = session.exec(select(Step).where(Step.run_id == run_id)).all()
        sequence = len(existing) + 1
    else:
        sequence = body.sequence

    step = Step(
        run_id=run_id,
        sequence=sequence,
        step_type=body.step_type,
        name=body.name or body.step_type,
        input=json.dumps(body.input) if body.input is not None else None,
        output=json.dumps(body.output) if body.output is not None else None,
        cost=body.cost,
        tokens=body.tokens,
        duration_ms=body.duration_ms,
    )
    if body.id:
        step.id = body.id

    session.add(step)
    session.commit()
    session.refresh(step)

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
