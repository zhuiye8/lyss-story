import json
from datetime import datetime, timezone

import aiosqlite


class SQLiteStore:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS stories (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT '',
                    theme TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'initializing',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS world_states (
                    story_id TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (story_id) REFERENCES stories(id)
                );
                CREATE TABLE IF NOT EXISTS chapters (
                    story_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    title TEXT NOT NULL DEFAULT '',
                    pov TEXT NOT NULL DEFAULT '',
                    content TEXT NOT NULL,
                    events_json TEXT NOT NULL DEFAULT '[]',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (story_id, chapter_num),
                    FOREIGN KEY (story_id) REFERENCES stories(id)
                );
            """)

    async def create_story(self, story_id: str, title: str, theme: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO stories (id, title, theme, status, created_at, updated_at) VALUES (?, ?, ?, 'initializing', ?, ?)",
                (story_id, title, theme, now, now),
            )
            await db.commit()

    async def get_story(self, story_id: str) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_story(self, story_id: str, **kwargs) -> None:
        now = datetime.now(timezone.utc).isoformat()
        sets = ["updated_at = ?"]
        vals = [now]
        for k, v in kwargs.items():
            sets.append(f"{k} = ?")
            vals.append(v)
        vals.append(story_id)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE stories SET {', '.join(sets)} WHERE id = ?", vals
            )
            await db.commit()

    async def list_stories(self) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM stories ORDER BY created_at DESC")
            return [dict(row) for row in await cursor.fetchall()]

    async def save_world_state(self, story_id: str, state: dict, version: int = 0) -> None:
        now = datetime.now(timezone.utc).isoformat()
        state_json = json.dumps(state, ensure_ascii=False)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO world_states (story_id, state_json, version, updated_at) VALUES (?, ?, ?, ?)",
                (story_id, state_json, version, now),
            )
            await db.commit()

    async def get_world_state(self, story_id: str) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT state_json FROM world_states WHERE story_id = ?", (story_id,)
            )
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None

    async def save_chapter(
        self,
        story_id: str,
        chapter_num: int,
        title: str,
        pov: str,
        content: str,
        events: list[str],
        metadata: dict,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO chapters (story_id, chapter_num, title, pov, content, events_json, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    story_id,
                    chapter_num,
                    title,
                    pov,
                    content,
                    json.dumps(events, ensure_ascii=False),
                    json.dumps(metadata, ensure_ascii=False),
                    now,
                ),
            )
            await db.commit()

    async def get_chapter(self, story_id: str, chapter_num: int) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM chapters WHERE story_id = ? AND chapter_num = ?",
                (story_id, chapter_num),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["events_covered"] = json.loads(d.pop("events_json"))
            d["metadata"] = json.loads(d.pop("metadata_json"))
            return d

    async def list_chapters(self, story_id: str) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT story_id, chapter_num, title, pov, length(content) as word_count, metadata_json, created_at FROM chapters WHERE story_id = ? ORDER BY chapter_num",
                (story_id,),
            )
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                meta = json.loads(d.pop("metadata_json", "{}"))
                d["has_warnings"] = bool(meta.get("consistency_warnings"))
                result.append(d)
            return result

    async def get_chapter_count(self, story_id: str) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM chapters WHERE story_id = ?", (story_id,)
            )
            row = await cursor.fetchone()
            return row[0] if row else 0
