import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

def get_db_path() -> str:
    return os.getenv("APP_DB_PATH", "app.db")

def get_db_url() -> str:
    # SQLite file path
    path = get_db_path()
    return f"sqlite:///{path}"

engine = create_engine(
    get_db_url(),
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
