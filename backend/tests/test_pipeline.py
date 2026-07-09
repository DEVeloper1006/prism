"""Tests for the ingestion pipeline and individual tracks."""

import pytest


@pytest.mark.asyncio
async def test_scanner_finds_new_files():
    """Scanner should identify new files not in the manifest."""
    # TODO: test with temp directory
    pass


@pytest.mark.asyncio
async def test_tracks_run_concurrently():
    """All 5 tracks should run in parallel for each file."""
    # TODO: test orchestrator with mock tracks
    pass


@pytest.mark.asyncio
async def test_track_error_isolation():
    """A failure in one track should not affect other tracks."""
    # TODO: test with a deliberately failing track
    pass
