from app.core.config import Settings
from app.database.config import get_database_connect_args, get_database_public_info


def test_database_public_info_excludes_credentials() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+psycopg://ridesphere:super-secret-password@postgres:5432/ridesphere"
    )

    database_info = get_database_public_info(settings)

    assert database_info == {
        "engine": "postgresql",
        "driver": "psycopg",
        "host": "postgres",
        "port": 5432,
        "database": "ridesphere",
    }


def test_sqlite_database_connect_args_are_configured_for_tests() -> None:
    settings = Settings(DATABASE_URL="sqlite+pysqlite:///:memory:")

    assert get_database_connect_args(settings) == {"check_same_thread": False}
