"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def discover_repository_root() -> Path:
    """Find a source checkout without assuming a fixed installed-package depth."""

    for parent in Path(__file__).resolve().parents:
        if (parent / "examples").is_dir():
            return parent
    return Path.cwd()


REPOSITORY_ROOT = discover_repository_root()
EXAMPLE_ROOT = REPOSITORY_ROOT / "examples"


class Settings(BaseSettings):
    """Runtime settings with safe local defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ASK_LUCAS_",
        extra="ignore",
    )

    build_version: str = "local"
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    content_dir: Path = EXAMPLE_ROOT / "content"
    answer_fixture_path: Path = EXAMPLE_ROOT / "fixtures" / "answers.json"
    evaluation_path: Path = EXAMPLE_ROOT / "evals" / "employer-questions.yaml"
    index_path: Path = REPOSITORY_ROOT / "apps" / "api" / "data" / "content.db"
    provider: str = "auto"
    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-haiku-4-5"
    anthropic_timeout_seconds: float = 30.0

    @property
    def allowed_origin_list(self) -> list[str]:
        """Return normalized, non-empty CORS origins."""

        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the process-level settings instance."""

    return Settings()
