"""Tests for hybrid search engine."""

import pytest


@pytest.mark.asyncio
async def test_semantic_search():
    """Semantic search should return clips ranked by similarity."""
    # TODO: test with mock ChromaDB
    pass


@pytest.mark.asyncio
async def test_filtered_search():
    """Filtered search should return clips matching metadata constraints."""
    # TODO: test with mock SQLite
    pass


@pytest.mark.asyncio
async def test_combined_search():
    """Combined search should apply both semantic ranking and metadata filtering."""
    # TODO: test hybrid pipeline
    pass
