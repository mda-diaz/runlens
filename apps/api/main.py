from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import create_db_and_tables
from routes.runs import router as runs_router
from routes.steps import router as steps_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="RunLens API", lifespan=lifespan)


@app.get("/")
def read_root():
    return {"message": "RunLens API running"}


app.include_router(runs_router)
app.include_router(steps_router)
