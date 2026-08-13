from sqlalchemy.engine import make_url

from app.core.config import Settings, get_settings


def get_database_url(settings: Settings | None = None) -> str:
    active_settings = settings or get_settings()
    return active_settings.database_url


def get_database_connect_args(settings: Settings | None = None) -> dict[str, bool]:
    url = make_url(get_database_url(settings))

    if url.get_backend_name() == "sqlite":
        return {"check_same_thread": False}

    return {}


def get_database_public_info(settings: Settings | None = None) -> dict[str, str | int | None]:
    url = make_url(get_database_url(settings))

    return {
        "engine": url.get_backend_name(),
        "driver": url.get_driver_name(),
        "host": url.host,
        "port": url.port,
        "database": url.database,
    }
