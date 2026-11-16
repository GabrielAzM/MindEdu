from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MindEdu API"
    environment: str = "dev"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    recovery_token_minutes: int = 15
    db_file: str = "data/mindedu.db"
    export_dir: str = "exports"
    recovery_outbox_path: str = "data/recovery_outbox.log"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    admin_user_id: str = "MDU-ADMIN-0001"
    admin_email: str = "admin@mindedu.local"
    admin_username: str = "Admin"
    admin_password: str = "Admin12345"

    model_config = SettingsConfigDict(
        env_prefix="MINDEDU_",
        env_file=".env",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        path = Path(self.db_file)
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path.as_posix()}"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

