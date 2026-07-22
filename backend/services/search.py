"""Hybrid search engine combining ChromaDB semantic search with SQLite filtering."""

import logging

logger = logging.getLogger("[SEARCH]")


class HybridSearchEngine:
    def __init__(self, vector_store, metadata_store, clip_encoder=None) -> None:  # noqa: ANN001
        self.vector_store = vector_store
        self.metadata_store = metadata_store
        self.clip_encoder = clip_encoder

    def search(
        self,
        query: str | None = None,
        filters: dict | None = None,
        color_similar_to: str | None = None,
        top_k: int = 20,
    ) -> list[dict]:
        logger.info("Search query=%s filters=%s top_k=%d", query, filters, top_k)

        if query and self.clip_encoder:
            query_embedding = self.clip_encoder.encode_text(query)
            vector_results = self.vector_store.search(query_embedding, top_k=100)
            candidate_ids = [r["clip_id"] for r in vector_results]
            score_map = {r["clip_id"]: r["score"] for r in vector_results}

            if filters:
                filtered = self.metadata_store.filter_by_ids(candidate_ids, filters)
            else:
                filtered = self.metadata_store.filter_by_ids(candidate_ids)

            for clip in filtered:
                clip["relevance_score"] = score_map.get(clip["id"], 0.0)

            filtered.sort(key=lambda c: c.get("relevance_score", 0), reverse=True)
            return filtered[:top_k]

        if query and not self.clip_encoder:
            logger.warning("No CLIP encoder available; falling back to metadata-only search")

        results = self.metadata_store.list_clips(limit=top_k, filters=filters)
        for clip in results:
            clip["relevance_score"] = 1.0
        return results
