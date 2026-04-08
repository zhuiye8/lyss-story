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
        collection = self.get_collection(story_id)
        collection.upsert(
            ids=[memory_id],
            documents=[text],
            metadatas=[metadata],
        )

    def query_memories(
        self,
        story_id: str,
        query_text: str,
        character_id: str | None = None,
        n_results: int = 5,
    ) -> list[dict]:
        collection = self.get_collection(story_id)
        kwargs: dict = {
            "query_texts": [query_text],
            "n_results": n_results,
        }
        if character_id:
            kwargs["where"] = {"character_id": character_id}

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
