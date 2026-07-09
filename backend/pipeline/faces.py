"""Track 4: Face Intelligence — face_recognition + DBSCAN clustering."""

import logging
from pathlib import Path

logger = logging.getLogger("[PIPELINE:T4]")


class FaceTrack:
    def __init__(self) -> None:
        pass

    async def process(self, video_path: Path) -> dict:
        """Detect faces in keyframes, extract encodings, cluster with DBSCAN."""
        logger.info("Processing face track for %s", video_path.name)
        # TODO: face_recognition detect → encode → DBSCAN cluster
        return {}
