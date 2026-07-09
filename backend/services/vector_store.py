"""ChromaDB vector store for CLIP embeddings."""

import logging

logger = logging.getLogger("[SEARCH:VECTOR]")


class VectorStore:
    def __init__(self, persist_dir: str) -> None:
        self.persist_dir = persist_dir
        # TODO: initialize ChromaDB client with persist_directory

    def add(self, clip_id: str, embedding: list[float], metadata: dict | None = None) -> None:
        """Add a CLIP embedding for a clip."""
        pass

    def search(self, query_embedding: list[float], top_k: int = 20) -> list[dict]:
        """Return top-k clips by cosine similarity."""
        return []

    def delete(self, clip_id: str) -> None:
        """Remove a clip's embedding."""
        pass

    def count(self) -> int:
        """Total number of stored embeddings."""
        return 0
