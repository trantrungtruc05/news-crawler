"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings

CATEGORIES: dict[str, str] = {
    "AI": "https://techcrunch.com/category/artificial-intelligence/",
    "Startups": "https://techcrunch.com/category/startups/",
    "Venture": "https://techcrunch.com/category/venture/",
    "Apple": "https://techcrunch.com/tag/apple/",
    "Security": "https://techcrunch.com/category/security/",
    "Apps": "https://techcrunch.com/category/apps/",
}


class Settings(BaseSettings):
    """Global application settings.

    All values are read from environment variables or a `.env` file.
    """

    database_url: str = "postgresql://postgres:postgres@localhost:5432/news_crawler"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    enable_translation: bool = False

    crawl_max_pages: int = 10
    crawl_timeout: int = 30

    scheduler_interval_hours: int = 12
    rss_check_interval_minutes: int = 30

    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
