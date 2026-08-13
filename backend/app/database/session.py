from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.config import get_database_connect_args, get_database_url


def create_db_engine():
    database_url = get_database_url()
    connect_args = get_database_connect_args()
    engine_kwargs = {
        "pool_pre_ping": True,
        "connect_args": connect_args,
    }

    if database_url == "sqlite+pysqlite:///:memory:":
        engine_kwargs["poolclass"] = StaticPool

    return create_engine(database_url, **engine_kwargs)


engine = create_db_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
