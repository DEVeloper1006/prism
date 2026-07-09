"""Track 5: Metadata Extraction — ffprobe + ExifTool + filesystem."""

import logging
from pathlib import Path

logger = logging.getLogger("[PIPELINE:T5]")


class MetadataTrack:
    def __init__(self) -> None:
        pass

    async def process(self, video_path: Path) -> dict:
        """Extract codec, resolution, fps, camera info, filesystem metadata."""
        logger.info("Processing metadata track for %s", video_path.name)
        # TODO: ffprobe → ExifTool → filesystem stat
        return {}
