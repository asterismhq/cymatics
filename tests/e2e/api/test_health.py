"""End-to-end tests executed against the Dockerised FastAPI app."""

import pytest


@pytest.mark.asyncio
class TestE2EAPI:
    """End-to-end tests for the FastAPI application."""

    async def test_health_endpoint_returns_ok(self, async_client):
        response = await async_client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
