"""File walker, checksum computation, and manifest diffing."""

import logging
from pathlib import Path

logger = logging.getLogger("[PIPELINE:SCANNER]")


class FileScanner:
    def __init__(self, media_root: Path) -> None:
        self.media_root = media_root

    def scan(self) -> list[Path]:
        """Walk directory, checksum files, compare to manifest, return new/modified files."""
        logger.info("Scanning %s", self.media_root)
        # TODO: implement file walking, checksumming, manifest diffing
        return []
