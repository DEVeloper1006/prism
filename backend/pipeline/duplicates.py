"""Duplicate detection via CLIP embedding similarity."""

import logging
import uuid

logger = logging.getLogger("[PIPELINE:DUPLICATES]")


class DuplicateDetector:
    def __init__(self, vector_store, metadata_store) -> None:  # noqa: ANN001
        self.vector_store = vector_store
        self.metadata_store = metadata_store

    def detect_and_mark(self, threshold: float = 0.95) -> list[list[str]]:
        groups = self.vector_store.find_duplicates(threshold=threshold)

        for group in groups:
            group_id = str(uuid.uuid4())[:8]
            best_clip_id = self._pick_best(group)

            for clip_id in group:
                clip = self.metadata_store.get_clip(clip_id)
                if clip:
                    clip["duplicate_group_id"] = group_id
                    clip["is_best_in_group"] = clip_id == best_clip_id
                    self.metadata_store.insert_clip(clip)

        logger.info("Found %d duplicate groups", len(groups))
        return groups

    def _pick_best(self, clip_ids: list[str]) -> str:
        best_id = clip_ids[0]
        best_score = -1

        for clip_id in clip_ids:
            clip = self.metadata_store.get_clip(clip_id)
            if clip:
                score = clip.get("sharpness_score") or 0
                if score > best_score:
                    best_score = score
                    best_id = clip_id

        return best_id
