"""Job queue, worker pool, and progress event bus for the ingestion pipeline."""

import logging
from pathlib import Path

logger = logging.getLogger("[PIPELINE:ORCHESTRATOR]")


class PipelineOrchestrator:
    def __init__(self, media_root: Path) -> None:
        self.media_root = media_root
        # TODO: set up ProcessPoolExecutor, progress event bus

    async def ingest(self, folder: Path) -> None:
        """Run all 5 tracks on every new/modified file in the folder."""
        logger.info("Starting ingestion for %s", folder)
        # TODO: scan → build job list → dispatch to worker pool

    async def cancel(self) -> None:
        """Cancel the current ingestion run."""
        # TODO: signal workers to stop
        pass
