"""Central environment-backed application settings."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development").lower()
    cors_origins: tuple[str, ...] = tuple(item.strip() for item in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if item.strip())
    storage_backend: str = os.getenv("STORAGE_BACKEND", "local").lower()
    upload_dir: str = os.getenv("UPLOAD_DIR", "static/uploads")
    s3_bucket: str = os.getenv("S3_BUCKET", "")
    s3_endpoint_url: str | None = os.getenv("S3_ENDPOINT_URL") or None
    s3_region: str | None = os.getenv("S3_REGION") or None
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    task_mode: str = os.getenv("TASK_MODE", "local").lower()

    def validate(self) -> None:
        """Refuse to start production with development-only configuration."""
        if self.app_env != "production":
            return

        errors: list[str] = []
        secret_key = os.getenv("SECRET_KEY", "")
        database_url = os.getenv("DATABASE_URL", "")
        weak_markers = ("change-me", "replace-with", "secret", "password")

        if len(secret_key) < 32 or any(marker in secret_key.lower() for marker in weak_markers):
            errors.append("SECRET_KEY must be a strong random value of at least 32 characters")
        if not database_url:
            errors.append("DATABASE_URL is required")
        if not self.cors_origins:
            errors.append("CORS_ORIGINS must contain the deployed web origin")
        if any("localhost" in origin or "127.0.0.1" in origin for origin in self.cors_origins):
            errors.append("CORS_ORIGINS cannot contain localhost in production")
        if self.storage_backend == "s3" and not self.s3_bucket:
            errors.append("S3_BUCKET is required when STORAGE_BACKEND=s3")

        if errors:
            raise RuntimeError("Unsafe production configuration: " + "; ".join(errors))


settings = Settings()
settings.validate()
