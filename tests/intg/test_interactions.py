"""Integration tests for component interactions."""

import pytest
from httpx import AsyncClient

from fapi_tmpl.api.dependencies import get_app_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear the settings cache before and after each test."""
    get_app_settings.cache_clear()
    yield
    get_app_settings.cache_clear()


class TestIntegration:
    """Integration tests for component interactions."""

    @pytest.mark.asyncio
    async def test_greeting_service_integration_with_real_service(
        self, monkeypatch, async_client: AsyncClient
    ):
        """Test that the greeting service integrates correctly with the real implementation."""
        monkeypatch.delenv("FAPI_TMPL_USE_MOCK_GREETING", raising=False)

        response = await async_client.get("/hello/Alice")

        assert response.status_code == 200
        assert response.json() == {"message": "Hello, Alice"}

    @pytest.mark.asyncio
    async def test_greeting_service_integration_with_mock_service(
        self, monkeypatch, async_client: AsyncClient
    ):
        """Test that the greeting service integrates correctly with the mock implementation."""
        monkeypatch.setenv("FAPI_TMPL_USE_MOCK_GREETING", "true")

        response = await async_client.get("/hello/World")

        assert response.status_code == 200
        assert response.json() == {"message": "[mock] Hello, World"}

    @pytest.mark.asyncio
    async def test_health_check_integration(self, async_client: AsyncClient):
        """Test that the health check endpoint integrates properly with the application."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
