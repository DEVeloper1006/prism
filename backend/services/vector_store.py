"""ChromaDB vector store for CLIP embeddings."""

import logging

import chromadb

logger = logging.getLogger("[SEARCH:VECTOR]")


class VectorStore:
    def __init__(self, persist_dir: str) -> None:
        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="clip_embeddings",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB initialized at %s (%d embeddings)",
            persist_dir,
            self.collection.count(),
        )

    def add(self, clip_id: str, embedding: list[float], metadata: dict | None = None) -> None:
        self.collection.upsert(
            ids=[clip_id],
            embeddings=[embedding],
            metadatas=[metadata or {}],
        )

    def search(self, query_embedding: list[float], top_k: int = 20) -> list[dict]:
        if self.collection.count() == 0:
            return []
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
        )
        output = []
        ids = results["ids"][0] if results["ids"] else []
        distances = results["distances"][0] if results["distances"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        for i, clip_id in enumerate(ids):
            output.append({
                "clip_id": clip_id,
                "distance": distances[i] if i < len(distances) else 1.0,
                "score": 1.0 - (distances[i] if i < len(distances) else 1.0),
                "metadata": metadatas[i] if i < len(metadatas) else {},
            })
        return output

    def get_embedding(self, clip_id: str) -> list[float] | None:
        result = self.collection.get(ids=[clip_id], include=["embeddings"])
        if result["embeddings"] and len(result["embeddings"]) > 0:
            return result["embeddings"][0]
        return None

    def find_similar(self, clip_id: str, top_k: int = 10) -> list[dict]:
        embedding = self.get_embedding(clip_id)
        if embedding is None:
            return []
        results = self.search(embedding, top_k=top_k + 1)
        return [r for r in results if r["clip_id"] != clip_id][:top_k]

    def find_duplicates(self, threshold: float = 0.95) -> list[list[str]]:
        all_data = self.collection.get(include=["embeddings"])
        if not all_data["ids"] or not all_data["embeddings"]:
            return []

        ids = all_data["ids"]
        groups: list[list[str]] = []
        seen: set[str] = set()

        for i, clip_id in enumerate(ids):
            if clip_id in seen:
                continue
            results = self.collection.query(
                query_embeddings=[all_data["embeddings"][i]],
                n_results=min(20, len(ids)),
            )
            group = []
            for j, match_id in enumerate(results["ids"][0]):
                if match_id == clip_id:
                    continue
                dist = results["distances"][0][j]
                if (1.0 - dist) >= threshold and match_id not in seen:
                    group.append(match_id)
                    seen.add(match_id)
            if group:
                seen.add(clip_id)
                group.insert(0, clip_id)
                groups.append(group)

        return groups

    def delete(self, clip_id: str) -> None:
        self.collection.delete(ids=[clip_id])

    def count(self) -> int:
        return self.collection.count()
