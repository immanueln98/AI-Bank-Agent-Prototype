from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from bankagent_backend import fixtures
from bankagent_backend.app import create_app
from bankagent_backend.routers import calls


@pytest.fixture(autouse=True)
def _reset_fixture_state() -> Iterator[None]:
    yield
    fixtures.reset_state()
    calls.reset_calls()


@pytest.fixture(autouse=True)
def _dummy_livekit_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIVEKIT_URL", "wss://test.livekit.cloud")
    monkeypatch.setenv("LIVEKIT_API_KEY", "test-api-key")
    monkeypatch.setenv("LIVEKIT_API_SECRET", "test-secret-value-of-at-least-32-chars!!")


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
