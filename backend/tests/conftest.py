"""Shared test fixtures for PRISM backend tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import create_app

TEST_TOKEN = "test-token-for-testing"


@pytest.fixture
def app():
    return create_app(token=TEST_TOKEN)


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {TEST_TOKEN}"}
