from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        rank_proxy_token="test-token",
        rank_proxy_database_url=f"sqlite:///{tmp_path / 'rank_cache.sqlite3'}",
        rank_cache_ttl_days=180,
        rank_cache_negative_ttl_days=7,
        easyscholar_rate_limit_per_second=100,
        rank_batch_max_size=10,
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-token"}
