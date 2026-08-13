import time

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.database.config import get_database_public_info
from app.database.session import engine
from app.schemas.health import DatabaseHealthResponse


def can_connect_to_database(target_engine: Engine = engine) -> bool:
    with target_engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True


def get_database_health(target_engine: Engine = engine) -> DatabaseHealthResponse:
    database_info = get_database_public_info()

    try:
        can_connect_to_database(target_engine)
        status = "healthy"
    except SQLAlchemyError:
        status = "unavailable"

    return DatabaseHealthResponse(status=status, **database_info)


def wait_for_database(
    max_attempts: int,
    delay_seconds: int,
    target_engine: Engine = engine,
) -> None:
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            can_connect_to_database(target_engine)
            return
        except SQLAlchemyError as exc:
            last_error = exc
            if attempt == max_attempts:
                break
            time.sleep(delay_seconds)

    raise RuntimeError("Database did not become available during startup.") from last_error
