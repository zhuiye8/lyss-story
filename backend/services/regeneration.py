"""Regeneration planning + cascade invalidation (Phase 2).

When a user regenerates chapter N, downstream chapters whose memories
were extracted against the *old* version of chapter N become stale.
This module:
  1. Scans chapter_dependencies to report which downstream chapters
     are affected, so the UI can offer per-chapter stale toggles.
  2. Deactivates (not deletes) the stale memories/triples/states/arcs/summaries
     so that LLM context assembly ignores them until the downstream chapter
     is re-generated.
  3. Supports restoring a previously invalidated set (used when an older
     chapter version is restored via restore_chapter_version).
"""
import logging
from dataclasses import dataclass, field

from backend.memory.knowledge_graph import KnowledgeGraph
from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class AffectedChapter:
    chapter_num: int
    source_version_id: int
    dep_chapters: list[int] = field(default_factory=list)
    memory_count: int = 0
    triple_count: int = 0
    state_count: int = 0
    summary_exists: bool = False
    brief: str = ""


@dataclass
class RegenerationPlan:
    target_chapter: int
    target_current_version_id: int | None
    affected_chapters: list[AffectedChapter] = field(default_factory=list)


class RegenerationPlanner:
    def __init__(
        self,
        sqlite: SQLiteStore,
        vector: VectorStore,
        kg: KnowledgeGraph,
    ):
        self.sqlite = sqlite
        self.vector = vector
        self.kg = kg

    async def plan(self, story_id: str, target_chapter: int) -> RegenerationPlan:
        """Compute the cascade impact of regenerating `target_chapter`."""
        live_id = await self.sqlite.get_live_version_id(story_id, target_chapter)
        downstream = await self.sqlite.get_downstream_chapters(story_id, target_chapter)

        affected: list[AffectedChapter] = []
        for d in downstream:
            ch_num = d["chapter_num"]
            vid = d["source_version_id"]
            # Count memories in vector store
            memory_count = await self._count_memories(story_id, ch_num, vid)
            # Count active triples
            triple_count = await self._count_triples(story_id, ch_num, vid)
            state_count = await self._count_states(story_id, ch_num, vid)
            summary = await self.sqlite.get_chapter_summary(story_id, ch_num)
            brief = (summary.get("brief") if summary else "") or ""

            affected.append(AffectedChapter(
                chapter_num=ch_num,
                source_version_id=vid,
                dep_chapters=d["dep_chapters"],
                memory_count=memory_count,
                triple_count=triple_count,
                state_count=state_count,
                summary_exists=summary is not None,
                brief=brief[:80],
            ))

        return RegenerationPlan(
            target_chapter=target_chapter,
            target_current_version_id=live_id,
            affected_chapters=affected,
        )

    async def _count_memories(self, story_id: str, chapter_num: int, version_id: int) -> int:
        collection = self.vector.get_collection(story_id)
        try:
            got = collection.get(
                where={"$and": [
                    {"chapter": chapter_num},
                    {"source_version_id": int(version_id)},
                    {"is_active": True},
                    {"doc_type": "memory"},
                ]},
                include=[],
            )
            return len(got.get("ids") or [])
        except Exception:
            return 0

    async def _count_triples(self, story_id: str, chapter_num: int, version_id: int) -> int:
        import aiosqlite
        async with aiosqlite.connect(self.sqlite.db_path) as db:
            cur = await db.execute(
                """SELECT COUNT(*) FROM knowledge_triples
                   WHERE story_id = ? AND valid_from = ? AND source_version_id = ? AND is_active = 1""",
                (story_id, chapter_num, version_id),
            )
            row = await cur.fetchone()
            return row[0] if row else 0

    async def _count_states(self, story_id: str, chapter_num: int, version_id: int) -> int:
        import aiosqlite
        async with aiosqlite.connect(self.sqlite.db_path) as db:
            cur = await db.execute(
                """SELECT COUNT(*) FROM character_states
                   WHERE story_id = ? AND chapter_num = ? AND source_version_id = ? AND is_active = 1""",
                (story_id, chapter_num, version_id),
            )
            row = await cur.fetchone()
            return row[0] if row else 0

    async def cascade_invalidate(
        self,
        story_id: str,
        chapter_num: int,
        version_id: int,
        active: bool = False,
    ) -> dict:
        """Mark (chapter_num, version_id)'s memories/triples/states/arcs/summary active/inactive.

        Returns per-category counts for reporting.
        """
        mem_count = self.vector.mark_memories_active(story_id, chapter_num, version_id, active)
        triple_count = await self.kg.mark_triples_active(story_id, chapter_num, version_id, active)
        await self.sqlite.mark_character_states_active(story_id, chapter_num, version_id, active)
        await self.sqlite.mark_arcs_active(story_id, chapter_num, version_id, active)
        await self.sqlite.mark_summary_active(story_id, chapter_num, version_id, active)
        return {
            "chapter_num": chapter_num,
            "version_id": version_id,
            "memory_count": mem_count,
            "triple_count": triple_count,
            "active": active,
        }

    async def apply_invalidation(
        self,
        story_id: str,
        target_chapter: int,
        chapters_to_invalidate: list[int] | None = None,
    ) -> list[dict]:
        """Invalidate memories of downstream chapters.

        If `chapters_to_invalidate` is None, invalidate ALL downstream.
        Otherwise only invalidate the selected chapter numbers.
        """
        downstream = await self.sqlite.get_downstream_chapters(story_id, target_chapter)
        results = []
        for d in downstream:
            ch_num = d["chapter_num"]
            if chapters_to_invalidate is not None and ch_num not in chapters_to_invalidate:
                continue
            vid = d["source_version_id"]
            result = await self.cascade_invalidate(story_id, ch_num, vid, active=False)
            results.append(result)
            logger.info(
                f"[RegenerationPlanner] Invalidated ch{ch_num} v{vid}: "
                f"{result['memory_count']} memories, {result['triple_count']} triples"
            )
        return results

    async def invalidate_old_live_memories(
        self,
        story_id: str,
        chapter_num: int,
        old_version_id: int,
    ) -> dict:
        """Called right before regenerating target chapter: deactivate old version's memories."""
        result = await self.cascade_invalidate(
            story_id, chapter_num, old_version_id, active=False
        )
        logger.info(
            f"[RegenerationPlanner] Deactivated old ch{chapter_num} v{old_version_id}: "
            f"{result['memory_count']} memories, {result['triple_count']} triples"
        )
        return result

    async def reactivate_version(
        self,
        story_id: str,
        chapter_num: int,
        version_id: int,
    ) -> dict:
        """Called when restoring an older version as live: reactivate its memories."""
        return await self.cascade_invalidate(
            story_id, chapter_num, version_id, active=True
        )
