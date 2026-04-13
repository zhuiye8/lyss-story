"""Plot pattern deduplication using ChromaDB embeddings.

Indexes each chapter's plot structure (goal + conflict + events summary)
as a vector, and provides similarity search so the Planner can avoid
repeating the same narrative patterns.
"""

import json
import logging

import chromadb

logger = logging.getLogger(__name__)


class PlotDedupStore:
    def __init__(self, chroma_path: str):
        self.client = chromadb.PersistentClient(path=chroma_path)

    def _collection(self, story_id: str) -> chromadb.Collection:
        return self.client.get_or_create_collection(
            name=f"plot_patterns_{story_id}",
            metadata={"hnsw:space": "cosine"},
        )

    def index_chapter(
        self,
        story_id: str,
        chapter_num: int,
        plot_structure: dict,
        new_events: list[dict],
    ) -> None:
        """Vector-index this chapter's plot pattern for later dedup queries."""
        goal = plot_structure.get("chapter_goal", "")
        conflict = plot_structure.get("key_conflict", "")
        emotional = plot_structure.get("emotional_arc", "")
        events_text = " / ".join(
            e.get("description", "") for e in new_events[:6]
        )

        # Combine into one searchable document
        doc = f"目标: {goal}  冲突: {conflict}  情感: {emotional}  事件: {events_text}"
        doc_id = f"ch{chapter_num}"

        try:
            coll = self._collection(story_id)
            coll.upsert(
                ids=[doc_id],
                documents=[doc],
                metadatas=[{
                    "chapter_num": chapter_num,
                    "goal": goal[:200],
                    "conflict": conflict[:200],
                }],
            )
        except Exception as e:
            logger.warning(f"[plot_dedup] Failed to index chapter {chapter_num}: {e}")

    def find_similar(
        self,
        story_id: str,
        query_text: str,
        top_k: int = 5,
        exclude_recent: int = 2,
    ) -> list[dict]:
        """Find historically similar plot patterns.

        Args:
            story_id: story identifier
            query_text: the current arc goal + chapter goal to search against
            top_k: number of results to return
            exclude_recent: skip the N most recent chapters to avoid
                            matching against the immediate context

        Returns:
            list of {chapter_num, goal, conflict, distance, text}
        """
        try:
            coll = self._collection(story_id)
            if coll.count() == 0:
                return []
            actual_k = min(top_k + exclude_recent, coll.count())
            results = coll.query(
                query_texts=[query_text],
                n_results=actual_k,
            )
        except Exception as e:
            logger.warning(f"[plot_dedup] Query failed: {e}")
            return []

        if not results or not results["documents"] or not results["documents"][0]:
            return []

        items = []
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            items.append({
                "chapter_num": meta.get("chapter_num", 0),
                "goal": meta.get("goal", ""),
                "conflict": meta.get("conflict", ""),
                "distance": results["distances"][0][i] if results["distances"] else 1.0,
                "text": doc,
            })

        # Sort by chapter_num ascending, then drop the most recent N
        items.sort(key=lambda x: x["chapter_num"])
        if exclude_recent > 0:
            items = items[:-exclude_recent] if len(items) > exclude_recent else []

        # Re-sort by distance ascending (most similar first)
        items.sort(key=lambda x: x["distance"])
        return items[:top_k]
