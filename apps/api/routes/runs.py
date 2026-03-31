from fastapi import APIRouter
from sqlmodel import Session
from database import engine
from models import Run

router = APIRouter()


@router.post("/runs")
def create_run(run: Run):
    with Session(engine) as session:
        session.add(run)
        session.commit()
        session.refresh(run)
        return run
