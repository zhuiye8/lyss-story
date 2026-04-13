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
                    is_published BOOLEAN NOT NULL DEFAULT 0,
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
                    is_published BOOLEAN NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (story_id, chapter_num),
                    FOREIGN KEY (story_id) REFERENCES stories(id)
                );
                CREATE TABLE IF NOT EXISTS model_configs (
                    id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    litellm_model TEXT NOT NULL,
                    api_key TEXT NOT NULL DEFAULT '',
                    api_base TEXT,
                    max_tokens INT DEFAULT 4096,
                    default_temperature REAL DEFAULT 0.7,
                    cost_per_million_input REAL DEFAULT 0,
                    cost_per_million_output REAL DEFAULT 0,
                    currency TEXT DEFAULT 'CNY',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS agent_model_bindings (
                    agent_name TEXT PRIMARY KEY,
                    model_config_id TEXT NOT NULL,
                    temperature_override REAL,
                    max_tokens_override INT,
                    FOREIGN KEY (model_config_id) REFERENCES model_configs(id)
                );
                CREATE TABLE IF NOT EXISTS llm_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_id TEXT,
                    chapter_num INT,
                    agent_name TEXT NOT NULL,
                    model_config_id TEXT NOT NULL DEFAULT '',
                    litellm_model TEXT NOT NULL,
                    system_prompt TEXT,
                    user_prompt TEXT,
                    response TEXT,
                    input_tokens INT DEFAULT 0,
                    output_tokens INT DEFAULT 0,
                    total_tokens INT DEFAULT 0,
                    cost_estimate REAL DEFAULT 0,
                    latency_ms INT DEFAULT 0,
                    status TEXT DEFAULT 'success',
                    error_message TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_llm_logs_agent ON llm_logs(agent_name);
                CREATE INDEX IF NOT EXISTS idx_llm_logs_story ON llm_logs(story_id);
                CREATE INDEX IF NOT EXISTS idx_llm_logs_created ON llm_logs(created_at);
                CREATE TABLE IF NOT EXISTS knowledge_triples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object TEXT NOT NULL,
                    detail TEXT DEFAULT '',
                    valid_from INT NOT NULL,
                    valid_to INT,
                    source TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_kt_story_subject ON knowledge_triples(story_id, subject);
                CREATE INDEX IF NOT EXISTS idx_kt_story_valid ON knowledge_triples(story_id, valid_to);
                CREATE TABLE IF NOT EXISTS character_states (
                    story_id TEXT NOT NULL,
                    character_id TEXT NOT NULL,
                    chapter_num INT NOT NULL,
                    emotional_state TEXT DEFAULT '',
                    knowledge_summary TEXT DEFAULT '',
                    goals_update TEXT DEFAULT '',
                    status TEXT DEFAULT 'active',
                    state_json TEXT DEFAULT '{}',
                    PRIMARY KEY (story_id, character_id, chapter_num)
                );
                CREATE TABLE IF NOT EXISTS chapter_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    version_num INTEGER NOT NULL,
                    title TEXT NOT NULL DEFAULT '',
                    pov TEXT NOT NULL DEFAULT '',
                    content TEXT NOT NULL,
                    events_json TEXT NOT NULL DEFAULT '[]',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    feedback TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (story_id) REFERENCES stories(id)
                );
                CREATE INDEX IF NOT EXISTS idx_chapter_versions_chapter
                    ON chapter_versions(story_id, chapter_num, version_num DESC);
                CREATE TABLE IF NOT EXISTS character_arcs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_id TEXT NOT NULL,
                    character_id TEXT NOT NULL,
                    chapter_num INTEGER NOT NULL,
                    arc_name TEXT NOT NULL DEFAULT '',
                    summary_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (story_id) REFERENCES stories(id)
                );
                CREATE INDEX IF NOT EXISTS idx_character_arcs_char
                    ON character_arcs(story_id, character_id, chapter_num DESC);
            """)
            # Migrate existing tables: add is_published if missing
            for table, col in [("stories", "is_published"), ("chapters", "is_published")]:
                try:
                    await db.execute(f"ALTER TABLE {table} ADD COLUMN {col} BOOLEAN NOT NULL DEFAULT 0")
                except Exception:
                    pass  # Column already exists

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
                "SELECT story_id, chapter_num, title, pov, length(content) as word_count, is_published, metadata_json, created_at FROM chapters WHERE story_id = ? ORDER BY chapter_num",
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

    # --- Chapter version methods ---

    async def save_chapter_version(
        self,
        story_id: str,
        chapter_num: int,
        title: str,
        pov: str,
        content: str,
        events: list[str],
        metadata: dict,
        feedback: str = "",
    ) -> int:
        """Snapshot a chapter into chapter_versions. Returns new version_num."""
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COALESCE(MAX(version_num), 0) FROM chapter_versions WHERE story_id = ? AND chapter_num = ?",
                (story_id, chapter_num),
            )
            row = await cursor.fetchone()
            next_version = (row[0] if row else 0) + 1
            await db.execute(
                """INSERT INTO chapter_versions
                   (story_id, chapter_num, version_num, title, pov, content,
                    events_json, metadata_json, feedback, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    story_id,
                    chapter_num,
                    next_version,
                    title,
                    pov,
                    content,
                    json.dumps(events, ensure_ascii=False),
                    json.dumps(metadata, ensure_ascii=False),
                    feedback,
                    now,
                ),
            )
            await db.commit()
            return next_version

    async def list_chapter_versions(
        self, story_id: str, chapter_num: int
    ) -> list[dict]:
        """List all historical versions of a chapter (most recent first)."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT id, story_id, chapter_num, version_num, title, pov,
                          length(content) as word_count, feedback, created_at
                   FROM chapter_versions
                   WHERE story_id = ? AND chapter_num = ?
                   ORDER BY version_num DESC""",
                (story_id, chapter_num),
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def get_chapter_version(self, version_id: int) -> dict | None:
        """Fetch a single chapter version by id with full content."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM chapter_versions WHERE id = ?", (version_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["events_covered"] = json.loads(d.pop("events_json"))
            d["metadata"] = json.loads(d.pop("metadata_json"))
            return d

    async def restore_chapter_version(self, version_id: int) -> dict | None:
        """Overwrite the current chapter with the given historical version.

        Before overwriting, the current live chapter is snapshotted into
        chapter_versions so the restore itself is reversible.
        Returns the restored chapter dict, or None if version not found.
        """
        version = await self.get_chapter_version(version_id)
        if not version:
            return None

        story_id = version["story_id"]
        chapter_num = version["chapter_num"]

        # Snapshot current live chapter first
        current = await self.get_chapter(story_id, chapter_num)
        if current:
            await self.save_chapter_version(
                story_id=story_id,
                chapter_num=chapter_num,
                title=current.get("title", ""),
                pov=current.get("pov", ""),
                content=current.get("content", ""),
                events=current.get("events_covered", []),
                metadata=current.get("metadata", {}),
                feedback=f"[restore snapshot] before restoring v{version['version_num']}",
            )

        # Restore by replacing live chapter
        await self.save_chapter(
            story_id=story_id,
            chapter_num=chapter_num,
            title=version.get("title", ""),
            pov=version.get("pov", ""),
            content=version.get("content", ""),
            events=version.get("events_covered", []),
            metadata=version.get("metadata", {}),
        )
        return version

    # --- Character arc methods ---

    async def save_character_arc(
        self,
        story_id: str,
        character_id: str,
        chapter_num: int,
        arc_name: str,
        summary: dict,
    ) -> int:
        """Persist a character arc summary. Returns the new row id."""
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO character_arcs
                   (story_id, character_id, chapter_num, arc_name, summary_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    story_id,
                    character_id,
                    chapter_num,
                    arc_name,
                    json.dumps(summary, ensure_ascii=False),
                    now,
                ),
            )
            await db.commit()
            return cursor.lastrowid or 0

    async def get_latest_character_arc(
        self, story_id: str, character_id: str
    ) -> dict | None:
        """Get the most recently stored arc row for a character."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT * FROM character_arcs
                   WHERE story_id = ? AND character_id = ?
                   ORDER BY chapter_num DESC, id DESC
                   LIMIT 1""",
                (story_id, character_id),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["summary"] = json.loads(d.pop("summary_json", "{}"))
            return d

    async def list_character_arcs(
        self, story_id: str, character_id: str
    ) -> list[dict]:
        """List all historical arc entries for a character (newest first)."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT * FROM character_arcs
                   WHERE story_id = ? AND character_id = ?
                   ORDER BY chapter_num DESC, id DESC""",
                (story_id, character_id),
            )
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d["summary"] = json.loads(d.pop("summary_json", "{}"))
                result.append(d)
            return result

    # --- Publish methods ---

    async def publish_story(self, story_id: str, publish: bool) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE stories SET is_published = ?, updated_at = ? WHERE id = ?",
                (1 if publish else 0, now, story_id),
            )
            await db.commit()

    async def publish_chapter(self, story_id: str, chapter_num: int, publish: bool) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE chapters SET is_published = ? WHERE story_id = ? AND chapter_num = ?",
                (1 if publish else 0, story_id, chapter_num),
            )
            await db.commit()

    async def list_published_stories(self) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM stories WHERE is_published = 1 ORDER BY updated_at DESC"
            )
            rows = [dict(row) for row in await cursor.fetchall()]
            for r in rows:
                cursor2 = await db.execute(
                    "SELECT COUNT(*) FROM chapters WHERE story_id = ? AND is_published = 1",
                    (r["id"],),
                )
                count_row = await cursor2.fetchone()
                r["published_chapter_count"] = count_row[0] if count_row else 0
            return rows

    async def list_published_chapters(self, story_id: str) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT story_id, chapter_num, title, pov, length(content) as word_count, created_at
                   FROM chapters WHERE story_id = ? AND is_published = 1
                   ORDER BY chapter_num""",
                (story_id,),
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def get_published_chapter(self, story_id: str, chapter_num: int) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT * FROM chapters
                   WHERE story_id = ? AND chapter_num = ? AND is_published = 1""",
                (story_id, chapter_num),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["events_covered"] = json.loads(d.pop("events_json"))
            d["metadata"] = json.loads(d.pop("metadata_json"))
            return d
