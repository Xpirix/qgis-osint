from __future__ import annotations
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "osint_matrix"
    postgres_user: str = "qgis"
    postgres_password: str

    # Redis
    redis_url: str = "redis://cache:6379/0"

    # GitHub
    github_token: Optional[str] = None

    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # Public domain
    domain: str = "localhost"

    # Logging
    log_level: str = "INFO"

    # Cache TTL
    proxy_cache_ttl: int = 3600

    # Worker intervals (seconds)
    fetch_interval_commits: int = 300
    fetch_interval_rss: int = 900
    fetch_interval_plugins: int = 600
    fetch_interval_hub: int = 1800
    fetch_interval_analytics: int = 86400
    fetch_interval_metabase: int = 3600    # Metabase dashboards refresh roughly hourly
    fetch_interval_scrape: int = 86400      # Daily — members/groups/events change infrequently
    fetch_interval_layers: int = 3600

    # Metabase card UUIDs (public dashboard)
    metabase_analytics_host: str = "feed.qgis.org"
    metabase_plugins_host: str = "plugins.qgis.org"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def github_headers(self) -> dict:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"
        return headers


settings = Settings()
