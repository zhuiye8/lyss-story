import chromadb


class VectorStore:
    def __init__(self, chroma_path: str):
        self.client = chromadb.PersistentClient(path=chroma_path)

    def get_collection(self, story_id: str) -> chromadb.Collection:
        return self.client.get_or_create_collection(
            name=f"story_{story_id}",
            metadata={"hnsw:space": "cosine"},
        )

    def add_memory(
        self, story_id: str, memory_id: str, text: str, metadata: dict
    ) -> None:
        # Ensure all metadata values are ChromaDB-compatible (str, int, float, bool)
        clean_meta = {}
        for k, v in metadata.items():
            if isinstance(v, list):
                clean_meta[k] = ",".join(str(x) for x in v)
            elif isinstance(v, (str, int, float, bool)):
                clean_meta[k] = v
            else:
                clean_meta[k] = str(v)

        collection = self.get_collection(story_id)
        collection.upsert(
            ids=[memory_id],
            documents=[text],
            metadatas=[clean_meta],
        )

    def query_memories(
        self,
        story_id: str,
        query_text: str,
        character_id: str | None = None,
        category: str | None = None,
        n_results: int = 5,
        min_emotional_weight: float | None = None,
    ) -> list[dict]:
        collection = self.get_collection(story_id)
        kwargs: dict = {
            "query_texts": [query_text],
            "n_results": n_results,
        }

        # Build where filter
        where_conditions = []
        if character_id:
            where_conditions.append({"character_id": character_id})
        if category:
            where_conditions.append({"category": category})
        if min_emotional_weight is not None:
            where_conditions.append({"emotional_weight": {"$gte": min_emotional_weight}})

        if len(where_conditions) == 1:
            kwargs["where"] = where_conditions[0]
        elif len(where_conditions) > 1:
            kwargs["where"] = {"$and": where_conditions}

        try:
            results = collection.query(**kwargs)
        except Exception:
            return []

        memories = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                memories.append({
                    "id": results["ids"][0][i],
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                })
        return memories

    def query_by_emotional_weight(
        self,
        story_id: str,
        character_id: str,
        top_k: int = 10,
    ) -> list[dict]:
        """Get top-K memories ranked by emotional weight for L1 loading."""
        collection = self.get_collection(story_id)
        try:
            # Get all memories for this character, then sort by emotional_weight
            results = collection.get(
                where={"character_id": character_id},
                include=["documents", "metadatas"],
            )
        except Exception:
            return []

        if not results or not results["documents"]:
            return []

        memories = []
        for i, doc in enumerate(results["documents"]):
            meta = results["metadatas"][i] if results["metadatas"] else {}
            memories.append({
                "id": results["ids"][i],
                "text": doc,
                "metadata": meta,
                "emotional_weight": meta.get("emotional_weight", 0.5) if isinstance(meta.get("emotional_weight"), (int, float)) else 0.5,
            })

        # Sort by emotional_weight descending
        memories.sort(key=lambda m: m["emotional_weight"], reverse=True)
        return memories[:top_k]
