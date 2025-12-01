"""End-to-end tests executed against the Dockerised FastAPI app."""

import pytest


@pytest.mark.asyncio
class TestE2EAPI:
    """End-to-end tests for the cymatics application."""

    async def test_health_endpoint_returns_ok(self, async_client):
        """Test health endpoint returns OK status."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    async def test_cycle_status_endpoint_exists(self, async_client):
        """Test cycle status endpoint is accessible."""
        response = await async_client.get("/v1/cycle/status")

        assert response.status_code == 200
        data = response.json()
        assert "queue_length" in data
        assert "model_state" in data
