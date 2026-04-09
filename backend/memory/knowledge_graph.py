"""Temporal knowledge graph for tracking character relationships and facts over time."""

import logging
from datetime import datetime, timezone

import aiosqlite

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def add_triple(
        self,
        story_id: str,
        subject: str,
        predicate: str,
        object: str,
        chapter_num: int,
        detail: str = "",
        source: str = "",
    ) -> None:
        """Add a new knowledge triple (e.g., 林默 信任 苏雨)."""
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO knowledge_triples
                   (story_id, subject, predicate, object, detail, valid_from, valid_to, source, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)""",
                (story_id, subject, predicate, object, detail, chapter_num, source, now),
            )
            await db.commit()

    async def invalidate(
        self,
        story_id: str,
        subject: str,
        predicate: str,
        object: str,
        chapter_num: int,
    ) -> None:
        """Invalidate a triple at a specific chapter (set valid_to)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE knowledge_triples
                   SET valid_to = ?
                   WHERE story_id = ? AND subject = ? AND predicate = ? AND object = ?
                     AND valid_to IS NULL""",
                (chapter_num, story_id, subject, predicate, object),
            )
            await db.commit()

    async def query_relationships(
        self,
        story_id: str,
        character_id: str,
        as_of_chapter: int | None = None,
    ) -> list[dict]:
        """Get all active relationships for a character, optionally at a point in time."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if as_of_chapter is not None:
                cursor = await db.execute(
                    """SELECT * FROM knowledge_triples
                       WHERE story_id = ? AND (subject = ? OR object = ?)
                         AND valid_from <= ?
                         AND (valid_to IS NULL OR valid_to > ?)
                       ORDER BY valid_from DESC""",
                    (story_id, character_id, character_id, as_of_chapter, as_of_chapter),
                )
            else:
                cursor = await db.execute(
                    """SELECT * FROM knowledge_triples
                       WHERE story_id = ? AND (subject = ? OR object = ?)
                         AND valid_to IS NULL
                       ORDER BY valid_from DESC""",
                    (story_id, character_id, character_id),
                )
            return [dict(row) for row in await cursor.fetchall()]

    async def get_relationship_between(
        self,
        story_id: str,
        char_a: str,
        char_b: str,
        as_of_chapter: int | None = None,
    ) -> list[dict]:
        """Get relationship triples between two specific characters."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            conditions = """story_id = ? AND (
                (subject = ? AND object = ?) OR (subject = ? AND object = ?)
            )"""
            params: list = [story_id, char_a, char_b, char_b, char_a]

            if as_of_chapter is not None:
                conditions += " AND valid_from <= ? AND (valid_to IS NULL OR valid_to > ?)"
                params.extend([as_of_chapter, as_of_chapter])
            else:
                conditions += " AND valid_to IS NULL"

            cursor = await db.execute(
                f"SELECT * FROM knowledge_triples WHERE {conditions} ORDER BY valid_from DESC",
                params,
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def get_timeline(self, story_id: str, character_id: str) -> list[dict]:
        """Get chronological timeline of all facts about a character."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT * FROM knowledge_triples
                   WHERE story_id = ? AND (subject = ? OR object = ?)
                   ORDER BY valid_from ASC""",
                (story_id, character_id, character_id),
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def format_relationships_for_prompt(
        self, story_id: str, character_id: str, character_profiles: list[dict]
    ) -> str:
        """Format current relationships as readable text for prompt injection."""
        rels = await self.query_relationships(story_id, character_id)
        if not rels:
            return "暂无已知关系记录。"

        # Build name lookup
        id_to_name = {c.get("character_id", ""): c.get("name", "") for c in character_profiles}

        lines = []
        for r in rels:
            subj_name = id_to_name.get(r["subject"], r["subject"])
            obj_name = id_to_name.get(r["object"], r["object"])
            line = f"- {subj_name} → {r['predicate']} → {obj_name}"
            if r.get("detail"):
                line += f"（{r['detail']}）"
            line += f" [自第{r['valid_from']}章]"
            lines.append(line)

        return "\n".join(lines)
