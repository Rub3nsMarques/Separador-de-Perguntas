from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn, DirectoryPath, Field
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    # Database
    PG_HOST: str
    PG_PORT: int = 5432
    PG_DB: str
    PG_USER: str
    PG_PASSWORD: str
    DATABASE_URL: Optional[PostgresDsn] = None

    # Storage
    FILES_BASE_PATH: Path = Path("/var/www/gps20test/frontend/web/files")
    OUTPUT_BASE_PATH: Path = Path("/var/www/gps20test/frontend/web/files/Questões e respostas separadas")

    # Runtime
    LOG_LEVEL: str = "INFO"
    SAFE_MODE: bool = True
    ALLOW_MASS_PROCESSING: bool = False
    DEFAULT_LIMIT: int = 1

    # Celery / Redis
    REDIS_URL: RedisDsn = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: Optional[RedisDsn] = None
    CELERY_RESULT_BACKEND: Optional[RedisDsn] = None
    WORKER_CONCURRENCY: int = 4

    # Parsing
    EXPECTED_ALTERNATIVES: int = 4
    ALLOW_VARIABLE_ALTERNATIVES: bool = True
    CONFIDENCE_THRESHOLD_NEEDS_REVIEW: int = 70

    # Report
    REPORT_FORMAT: str = "html"
    REPORT_FILENAME: str = "report.html"

    # Flags
    TRIM_RELATIONSHIPS: bool = False
    WRITE_DB_RESULTS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )

    def get_db_url(self) -> str:
        if self.DATABASE_URL:
            return str(self.DATABASE_URL)
        return f"postgresql://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DB}"

settings = Settings()
