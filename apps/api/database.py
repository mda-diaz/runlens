from sqlmodel import SQLModel, create_engine, Session

sqlite_url = "sqlite:///./runlens.db"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
