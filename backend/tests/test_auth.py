"""Tests for token authentication middleware."""

import pytest


@pytest.mark.asyncio
async def test_health_no_auth(client):
    """Health endpoint should not require authentication."""
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_missing_token_rejected(client):
    """Requests without a token should be rejected."""
    # TODO: test a protected endpoint once routes are mounted
    pass


@pytest.mark.asyncio
async def test_invalid_token_rejected(client):
    """Requests with an invalid token should be rejected."""
    # TODO: test with wrong token
    pass
