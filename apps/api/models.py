from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid


class Run(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    task_name: str
    status: str = "running"
    total_cost: float = 0.0
    total_tokens: int = 0
    duration_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    parent_run_id: Optional[str] = None


class Step(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    run_id: str
    sequence: int
    step_type: str
    name: str

    input: Optional[str] = None
    output: Optional[str] = None

    cost: Optional[float] = 0.0
    tokens: Optional[int] = 0
    duration_ms: Optional[int] = None
