from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="RideSphere", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    frontend_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        alias="FRONTEND_ORIGINS",
    )
    database_url: str = Field(
        default="postgresql+psycopg://ridesphere@localhost:5432/ridesphere",
        alias="DATABASE_URL",
    )
    database_retry_attempts: int = Field(default=10, alias="DATABASE_RETRY_ATTEMPTS")
    database_retry_delay_seconds: int = Field(default=2, alias="DATABASE_RETRY_DELAY_SECONDS")
    jwt_secret_key: str = Field(default="replace_with_secure_secret_key", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    payment_base_fare: float = Field(default=4.5, alias="PAYMENT_BASE_FARE")
    payment_distance_rate_per_km: float = Field(default=1.75, alias="PAYMENT_DISTANCE_RATE_PER_KM")
    payment_duration_rate_per_minute: float = Field(
        default=0.35,
        alias="PAYMENT_DURATION_RATE_PER_MINUTE",
    )
    payment_currency: str = Field(default="USD", alias="PAYMENT_CURRENCY")
    mongodb_enabled: bool = Field(default=False, alias="MONGODB_ENABLED")
    mongodb_url: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URL")
    mongodb_database: str = Field(default="ridesphere", alias="MONGODB_DATABASE")
    mongodb_events_collection: str = Field(default="operational_events", alias="MONGODB_EVENTS_COLLECTION")
    mongodb_connect_timeout_ms: int = Field(default=1000, alias="MONGODB_CONNECT_TIMEOUT_MS")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    azure_key_vault_url: str | None = Field(default=None, alias="AZURE_KEY_VAULT_URL")
    application_insights_connection_string: str | None = Field(
        default=None,
        alias="APPLICATIONINSIGHTS_CONNECTION_STRING",
    )
    azure_blob_storage_account_url: str | None = Field(
        default=None,
        alias="AZURE_BLOB_STORAGE_ACCOUNT_URL",
    )
    azure_blob_storage_container: str | None = Field(
        default=None,
        alias="AZURE_BLOB_STORAGE_CONTAINER",
    )
    celery_enabled: bool = Field(default=False, alias="CELERY_ENABLED")
    celery_broker_url: str = Field(default="redis://localhost:6379/0", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/1", alias="CELERY_RESULT_BACKEND")
    celery_task_always_eager: bool = Field(default=False, alias="CELERY_TASK_ALWAYS_EAGER")
    celery_task_eager_propagates: bool = Field(default=True, alias="CELERY_TASK_EAGER_PROPAGATES")
    celery_worker_log_level: str = Field(default="INFO", alias="CELERY_WORKER_LOG_LEVEL")
    celery_default_queue: str = Field(default="ridesphere", alias="CELERY_DEFAULT_QUEUE")
    celery_task_max_retries: int = Field(default=3, alias="CELERY_TASK_MAX_RETRIES")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )

    def get_frontend_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
