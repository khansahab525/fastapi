import os
from pathlib import Path

from dotenv import load_dotenv

# Project root: fastapi/
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_env_file() -> Path | None:
    """Load variables from .env into os.environ (idempotent)."""
    candidates = (
        PROJECT_ROOT / ".env",
        Path.cwd() / ".env",
    )
    for path in candidates:
        if path.is_file():
            load_dotenv(path, override=True)
            return path
    # No file found; still allow real environment variables from the shell
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    return None


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def getenv(name: str, default: str = "") -> str:
    """Read one variable after ensuring .env has been loaded."""
    load_env_file()
    return (os.getenv(name) or default).strip()


class Settings:
    """Settings read from .env / process environment via os.getenv."""

    @property
    def app_name(self) -> str:
        return getenv("APP_NAME", "AlbassamiChat API")

    @property
    def debug(self) -> bool:
        load_env_file()
        return _env_bool("DEBUG", default=False)

    @property
    def odoo_url(self) -> str:
        return getenv("ODOO_URL", "http://localhost:8069")

    @property
    def odoo_api_key(self) -> str:
        return getenv("ODOO_API_KEY")

    @property
    def openai_api_key(self) -> str:
        return getenv("OPENAI_API_KEY")

    @property
    def openai_model(self) -> str:
        return getenv("OPENAI_MODEL", "gpt-4o-mini")


settings = Settings()

# Load .env as soon as this module is imported
load_env_file()
