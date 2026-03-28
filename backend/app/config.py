from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_title: str = "Drape API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database (Supabase PostgreSQL)
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/postgres"

    # Supabase Auth
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_jwt_secret: str = ""  # used to verify tokens server-side

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"

    # Replicate
    replicate_api_token: str = ""
    replicate_webhook_secret: str = ""
    replicate_tryon_version: str = "c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4"

    # AWS S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = "drape-assets"
    aws_s3_region: str = "us-east-1"
    aws_s3_endpoint_url: str = ""

    # CORS
    allowed_origins: list[str] = ["http://localhost:5173", "https://drape.app"]

    # App URL (for webhooks)
    app_url: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
