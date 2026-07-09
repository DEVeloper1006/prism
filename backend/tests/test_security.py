"""Security tests: path traversal, SQL injection, input validation."""

import pytest


@pytest.mark.asyncio
async def test_path_traversal_rejected():
    """Paths containing ../ should be rejected."""
    # TODO: test ingest endpoint with malicious paths
    pass


@pytest.mark.asyncio
async def test_sql_injection_prevented():
    """Search queries with SQL injection attempts should be safely handled."""
    # TODO: test search with injection payloads
    pass


@pytest.mark.asyncio
async def test_query_length_limit():
    """Search queries exceeding 500 chars should be rejected."""
    # TODO: test with oversized query
    pass
