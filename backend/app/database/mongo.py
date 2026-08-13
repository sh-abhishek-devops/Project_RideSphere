from functools import lru_cache

from pymongo import MongoClient
from pymongo.collection import Collection

from app.core.config import get_settings


@lru_cache
def get_mongo_client() -> MongoClient | None:
    settings = get_settings()
    if settings.mongodb_enabled is False:
        return None

    return MongoClient(
        settings.mongodb_url,
        serverSelectionTimeoutMS=settings.mongodb_connect_timeout_ms,
        connectTimeoutMS=settings.mongodb_connect_timeout_ms,
        uuidRepresentation="standard",
    )


def get_operational_events_collection() -> Collection | None:
    client = get_mongo_client()
    if client is None:
        return None

    settings = get_settings()
    return client[settings.mongodb_database][settings.mongodb_events_collection]
