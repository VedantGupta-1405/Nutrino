"""
Application configuration settings loaded from environment variables using Pydantic Settings.
"""

from functools import lru_cache
from typing import Any, List, Optional, Union
from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Project metadata
    PROJECT_NAME: str = "Nutrino"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "AI Nutrition & Meal Planning System"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "nutrino"
    POSTGRES_PASSWORD: str = "nutrino_password"
    POSTGRES_DB: str = "nutrino_db"
    DATABASE_URL: Union[str, None] = None

    @property
    def sync_database_url(self) -> str:
        """Return the database URL, assembling from components if not explicitly provided."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        password = f":{self.POSTGRES_PASSWORD}" if self.POSTGRES_PASSWORD else ""
        return f"postgresql+psycopg2://{self.POSTGRES_USER}{password}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Security & JWT
    SECRET_KEY: str = "development_secret_key_change_in_production_min32chars"
    JWT_SECRET_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    JWT_ALGORITHM: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: Optional[int] = None

    # AI / Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"
    OLLAMA_TIMEOUT_SECONDS: float = 180.0

    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:80",
        "http://localhost",
    ]
    CORS_ORIGINS: Optional[Union[List[str], str]] = None

    @model_validator(mode="before")
    @classmethod
    def reconcile_environment_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Reconcile JWT_SECRET_KEY <-> SECRET_KEY
            jwt_sec = data.get("JWT_SECRET_KEY")
            sec = data.get("SECRET_KEY")
            if jwt_sec:
                data["SECRET_KEY"] = jwt_sec
                data["JWT_SECRET_KEY"] = jwt_sec
            elif sec:
                data["JWT_SECRET_KEY"] = sec

            # Reconcile JWT_ALGORITHM <-> ALGORITHM
            jwt_alg = data.get("JWT_ALGORITHM")
            alg = data.get("ALGORITHM")
            if jwt_alg:
                data["ALGORITHM"] = jwt_alg
                data["JWT_ALGORITHM"] = jwt_alg
            elif alg:
                data["JWT_ALGORITHM"] = alg

            # Reconcile JWT_ACCESS_TOKEN_EXPIRE_MINUTES <-> ACCESS_TOKEN_EXPIRE_MINUTES
            jwt_exp = data.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
            exp = data.get("ACCESS_TOKEN_EXPIRE_MINUTES")
            if jwt_exp is not None:
                data["ACCESS_TOKEN_EXPIRE_MINUTES"] = jwt_exp
                data["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = jwt_exp
            elif exp is not None:
                data["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = exp

            # Reconcile CORS_ORIGINS <-> BACKEND_CORS_ORIGINS
            cors = data.get("CORS_ORIGINS")
            backend_cors = data.get("BACKEND_CORS_ORIGINS")
            if cors is not None:
                data["BACKEND_CORS_ORIGINS"] = cors
                data["CORS_ORIGINS"] = cors
            elif backend_cors is not None:
                data["CORS_ORIGINS"] = backend_cors
        return data

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            return json.loads(v)
        elif isinstance(v, list):
            return v
        return []


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
