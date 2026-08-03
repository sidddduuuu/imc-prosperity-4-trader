from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Atlas"
    environment: str = "development"
    secret_key: str = "atlas-dev-secret-change-me-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7
    algorithm: str = "HS256"

    database_url: str = f"sqlite:///{DATA_DIR / 'atlas.db'}"
    redis_url: str | None = None
    cors_origins: str = "*"

    openrouter_api_key: str | None = None
    fireworks_api_key: str | None = None
    market_data_provider: str = "yahoo"  # yahoo | polygon | tiingo
    polygon_api_key: str | None = None
    tiingo_api_key: str | None = None

    rate_limit_per_minute: int = 120
    max_backtest_days: int = 3650
    paper_starting_cash: float = 100_000.0

    disclaimer: str = (
        "Atlas is for informational and educational purposes only. "
        "Nothing here is investment, tax, or legal advice. "
        "Past performance does not guarantee future results. "
        "Market data may be delayed. You are solely responsible for your trading decisions."
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
