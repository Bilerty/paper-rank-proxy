from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    easyscholar_secret_key: str = Field(default="", validation_alias="EASYSCHOLAR_SECRET_KEY")
    easyscholar_api_url: str = Field(
        default="https://www.easyscholar.cc/open/getPublicationRank",
        validation_alias="EASYSCHOLAR_API_URL",
    )
    rank_proxy_token: str = Field(default="", validation_alias="RANK_PROXY_TOKEN")
    rank_cache_ttl_days: int = Field(default=180, validation_alias="RANK_CACHE_TTL_DAYS")
    rank_cache_negative_ttl_days: int = Field(
        default=7,
        validation_alias="RANK_CACHE_NEGATIVE_TTL_DAYS",
    )
    easyscholar_rate_limit_per_second: float = Field(
        default=2.0,
        validation_alias="EASYSCHOLAR_RATE_LIMIT_PER_SECOND",
    )
    rank_proxy_database_url: str = Field(
        default="sqlite:///./data/rank_cache.sqlite3",
        validation_alias="RANK_PROXY_DATABASE_URL",
    )
    rank_batch_max_size: int = Field(default=100, validation_alias="RANK_BATCH_MAX_SIZE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    def ensure_runtime_ready(self) -> None:
        if not self.rank_proxy_token:
            raise RuntimeError("RANK_PROXY_TOKEN must be set before starting the service.")
        if self.rank_cache_ttl_days <= 0:
            raise RuntimeError("RANK_CACHE_TTL_DAYS must be positive.")
        if self.rank_cache_negative_ttl_days <= 0:
            raise RuntimeError("RANK_CACHE_NEGATIVE_TTL_DAYS must be positive.")
        if self.easyscholar_rate_limit_per_second <= 0:
            raise RuntimeError("EASYSCHOLAR_RATE_LIMIT_PER_SECOND must be positive.")
        if self.rank_batch_max_size <= 0:
            raise RuntimeError("RANK_BATCH_MAX_SIZE must be positive.")

    def ensure_database_parent(self) -> None:
        prefix = "sqlite:///"
        if self.rank_proxy_database_url.startswith(prefix):
            raw_path = self.rank_proxy_database_url[len(prefix) :]
            if raw_path and raw_path != ":memory:":
                Path(raw_path).parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
