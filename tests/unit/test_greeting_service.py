"""Unit tests for the greeting services."""

import pytest

from dev.mocks.services.mock_greeting_service import MockGreetingService
from fapi_tmpl.api.dependencies import get_app_settings, get_greeting_service
from fapi_tmpl.services.greeting_service import GreetingService


@pytest.fixture(autouse=True)
def reset_settings_cache():
    get_app_settings.cache_clear()
    yield
    get_app_settings.cache_clear()


class TestGreetingService:
    """Unit tests for greeting services."""

    def test_greeting_service_generate_greeting(self):
        service = GreetingService()
        result = service.generate_greeting("World")
        assert result == "Hello, World"

    def test_mock_greeting_service_generate_greeting(self):
        service = MockGreetingService()
        result = service.generate_greeting("Developers")
        assert result == "[mock] Hello, Developers"

    def test_get_greeting_service_defaults_to_real(self, monkeypatch):
        monkeypatch.delenv("FAPI_TMPL_USE_MOCK_GREETING", raising=False)

        service = get_greeting_service()

        assert isinstance(service, GreetingService)

    def test_get_greeting_service_uses_mock_when_enabled(self, monkeypatch):
        monkeypatch.setenv("FAPI_TMPL_USE_MOCK_GREETING", "true")

        service = get_greeting_service()

        assert isinstance(service, MockGreetingService)
