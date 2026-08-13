from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models so Alembic and metadata registration include them.
from app import models  # noqa: E402,F401
