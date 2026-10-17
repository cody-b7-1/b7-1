from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Settings loaded from environment variables and the repository .env file."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_host: str
    db_port: int = 3306
    db_user: str
    db_password: str
    db_name: str

    app_env: Literal["local", "test", "production"] = "local"
    
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_access_token_expire_days: int = Field(default=7, gt=0)
    jwt_refresh_token_expire_days: int = Field(default=14, gt=0)

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )

    @property
    def is_local(self) -> bool:
        return self.app_env == "local"


settings = Settings()
