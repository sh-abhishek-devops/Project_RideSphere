from pydantic import BaseModel


class DatabaseHealthResponse(BaseModel):
    status: str
    engine: str
    driver: str
    host: str | None = None
    port: int | None = None
    database: str | None = None


class HealthResponse(BaseModel):
    status: str
    application: str
    database: DatabaseHealthResponse
