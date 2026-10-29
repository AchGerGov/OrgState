from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base

DB_URL = "sqlite:///org.db"
engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_session() -> Session:
    return SessionLocal()
