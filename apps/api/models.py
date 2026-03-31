from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid


class Run(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    task_name: str
    status: str = "running"
    context: Optional[str] = None  # JSON string
    total_cost: float = 0.0
    total_tokens: int = 0
    duration_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None


class Step(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    run_id: str = Field(foreign_key="run.id")
    sequence: int
    step_type: str
    name: str
    input: Optional[str] = None   # JSON string
    output: Optional[str] = None  # JSON string
    cost: float = 0.0
    tokens: int = 0
    duration_ms: Optional[int] = None
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
