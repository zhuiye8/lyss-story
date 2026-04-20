"""Three-layer context assembler (Phase 3).

Responsibilities:
- L1 global: story bible core (logline + current volume outline + special ability)
- L2 recent: last N chapter summaries + previous chapter tail snippet
- L3 retrieval: vector search for scene-relevant memories + scene-text chunks
- World Book: keyword-triggered world entries
- Character cards: in-scene character structured info + current states

Each section has its own character budget. Output is a dict of sections the
writer/camera agents consume.
"""
import logging
from dataclasses import dataclass, field

from backend.memory.knowledge_graph import KnowledgeGraph
from backend.memory.world_book import WorldBook
from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore

logger = logging.getLogger(__name__)


DEFAULT_BUDGETS = {
    "bible_core": 1200,
    "recent_summary": 2000,
    "last_tail": 800,
    "vector_memory": 1200,
    "scene_text": 1000,
    "lorebook": 1500,
    "character_cards": 1500,
    "relationships": 800,
    "unresolved_threads": 600,
}


@dataclass
class ContextBundle:
    bible_core: str = ""
    recent_summary: str = ""
    last_tail: str = ""
    vector_memory: str = ""
    scene_text: str = ""
    lorebook: str = ""
    character_cards: str = ""
    relationships: str = ""
    unresolved_threads: str = ""
    # Ancillary data (not prompt text)
    triggered_entry_names: list[str] = field(default_factory=list)
    dependency_chapters: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "bible_core": self.bible_core,
            "recent_summary": self.recent_summary,
            "last_tail": self.last_tail,
            "vector_memory": self.vector_memory,
            "scene_text": self.scene_text,
            "lorebook": self.lorebook,
            "character_cards": self.character_cards,
            "relationships": self.relationships,
            "unresolved_threads": self.unresolved_threads,
            "triggered_entry_names": self.triggered_entry_names,
            "dependency_chapters": self.dependency_chapters,
        }


class ContextBuilder:
    def __init__(
        self,
        sqlite: SQLiteStore,
        vector: VectorStore,
        kg: KnowledgeGraph,
        world_book: WorldBook,
    ):
        self.sqlite = sqlite
        self.vector = vector
        self.kg = kg
        self.world_book = world_book

    async def build(
        self,
        story_id: str,
        chapter_num: int,
        story_bible: dict,
        character_profiles: list[dict],
        plot_structure: dict | None = None,
        scene: dict | None = None,
        primary_characters: list[str] | None = None,
        budgets: dict | None = None,
    ) -> ContextBundle:
        b = dict(DEFAULT_BUDGETS)
        if budgets:
            b.update(budgets)

        bundle = ContextBundle()

        # 1. Bible core (logline + current volume outline + special ability + style guide)
        bundle.bible_core = self._build_bible_core(story_bible, chapter_num, b["bible_core"])

        # 2. Recent summaries (last 5 chapters)
        recent, dep_chapters = await self._build_recent_summary(
            story_id, chapter_num, b["recent_summary"]
        )
        bundle.recent_summary = recent
        bundle.dependency_chapters.extend(dep_chapters)

        # 3. Last chapter tail (preserve prose rhythm)
        tail, tail_dep = await self._build_last_tail(story_id, chapter_num, b["last_tail"])
        bundle.last_tail = tail
        if tail_dep is not None:
            bundle.dependency_chapters.append(tail_dep)

        # Dedup dep list
        bundle.dependency_chapters = sorted(set(bundle.dependency_chapters))

        # 4. Vector retrieval (memories relevant to current scene/plot)
        query_text = self._build_query_text(plot_structure, scene)
        bundle.vector_memory = self._build_vector_memory(
            story_id, query_text, primary_characters, b["vector_memory"]
        )

        # 5. Scene text retrieval (Phase 4)
        bundle.scene_text = self._build_scene_text(story_id, query_text, b["scene_text"])

        # 6. World book (keyword-triggered)
        scan_text = query_text + "\n" + bundle.last_tail
        triggered = await self.world_book.get_triggered(
            story_id, scan_text, max_entries=5, char_budget=b["lorebook"]
        )
        bundle.lorebook = self.world_book.format_for_prompt(triggered)
        bundle.triggered_entry_names = [e.get("name", "") for e in triggered]

        # 7. Character cards (structured)
        bundle.character_cards = await self._build_character_cards(
            story_id, character_profiles, chapter_num,
            primary_characters=primary_characters, budget=b["character_cards"]
        )

        # 8. Relationship graph snapshot
        bundle.relationships = await self._build_relationships(
            story_id, character_profiles, chapter_num, b["relationships"]
        )

        # 9. Unresolved threads from recent chapters
        bundle.unresolved_threads = await self._build_unresolved_threads(
            story_id, chapter_num, b["unresolved_threads"]
        )

        logger.info(
            f"[ContextBuilder] ch{chapter_num}: "
            f"bible={len(bundle.bible_core)}, recent={len(bundle.recent_summary)}, "
            f"tail={len(bundle.last_tail)}, mem={len(bundle.vector_memory)}, "
            f"scene_text={len(bundle.scene_text)}, "
            f"lorebook={len(bundle.lorebook)} ({len(triggered)} entries), "
            f"cards={len(bundle.character_cards)}, "
            f"rels={len(bundle.relationships)}, unresolved={len(bundle.unresolved_threads)}"
        )
        return bundle

    # --- Section builders ---

    def _build_bible_core(self, bible: dict, chapter_num: int, budget: int) -> str:
        if not bible:
            return ""
        parts = []
        title = bible.get("title", "")
        genre = bible.get("genre", "")
        tone = bible.get("tone", "")
        one_line = bible.get("one_line_summary", "")
        if title:
            parts.append(f"《{title}》")
        meta_bits = []
        if genre:
            meta_bits.append(f"题材：{genre}")
        if tone:
            meta_bits.append(f"基调：{tone}")
        if meta_bits:
            parts.append("｜".join(meta_bits))
        if one_line:
            parts.append(f"一句话梗概：{one_line}")

        # Current volume outline
        volumes = bible.get("volumes") or []
        current_vol = None
        for vol in volumes:
            start = vol.get("chapter_start")
            end = vol.get("chapter_end")
            if start is None or end is None:
                continue
            if start <= chapter_num <= end:
                current_vol = vol
                break
        if not current_vol and volumes:
            current_vol = volumes[-1]
        if current_vol:
            parts.append(f"\n【当前卷】{current_vol.get('volume_name', '')}")
            if current_vol.get("main_plot"):
                parts.append(f"主线：{current_vol['main_plot']}")
            subplots = current_vol.get("subplots") or []
            if subplots:
                parts.append("支线：" + "；".join([str(s) for s in subplots[:3]]))
            conflicts = current_vol.get("conflicts") or []
            if conflicts:
                parts.append("冲突：" + "；".join([str(c) for c in conflicts[:3]]))
            if current_vol.get("climax_event"):
                parts.append(f"本卷高潮：{current_vol['climax_event']}")

        # Style guide tone
        style = bible.get("style_guide") or {}
        if isinstance(style, dict):
            bits = []
            for k in ("pov_preference", "language_style", "dialogue_style"):
                v = style.get(k)
                if v:
                    bits.append(f"{k}={v}")
            if bits:
                parts.append("风格：" + "，".join(bits))

        text = "\n".join(parts)
        return _truncate(text, budget)

    async def _build_recent_summary(
        self, story_id: str, chapter_num: int, budget: int
    ) -> tuple[str, list[int]]:
        if chapter_num <= 1:
            return "", []
        summaries = await self.sqlite.list_recent_summaries(
            story_id, up_to_chapter=chapter_num - 1, limit=5
        )
        if not summaries:
            return "", []

        # Oldest first for reading flow
        summaries.sort(key=lambda s: s["chapter_num"])
        lines = []
        dep_chapters = []
        for s in summaries:
            dep_chapters.append(s["chapter_num"])
            brief = s.get("brief") or ""
            key_events = s.get("key_events") or []
            ev = ("；".join(key_events[:3])) if key_events else ""
            line = f"第{s['chapter_num']}章: {brief}"
            if ev:
                line += f"\n  关键事件: {ev}"
            lines.append(line)
        text = "\n".join(lines)
        return _truncate(text, budget), dep_chapters

    async def _build_last_tail(
        self, story_id: str, chapter_num: int, budget: int
    ) -> tuple[str, int | None]:
        if chapter_num <= 1:
            return "", None
        prev = chapter_num - 1
        summary = await self.sqlite.get_chapter_summary(story_id, prev)
        if summary and summary.get("tail_snippet"):
            return _truncate(summary["tail_snippet"], budget), prev
        # Fallback to chapter content tail
        ch = await self.sqlite.get_chapter(story_id, prev)
        if ch and ch.get("content"):
            content = ch["content"]
            tail_chars = min(budget, 400)
            return content[-tail_chars:].strip(), prev
        return "", None

    def _build_query_text(self, plot_structure: dict | None, scene: dict | None) -> str:
        parts = []
        if scene:
            if scene.get("purpose"):
                parts.append(str(scene["purpose"]))
            if scene.get("location"):
                parts.append(str(scene["location"]))
            beats = scene.get("beats") or []
            for b in beats[:3]:
                parts.append(str(b))
        if plot_structure:
            goal = plot_structure.get("chapter_goal")
            if goal:
                parts.append(str(goal))
            for b in (plot_structure.get("beats") or [])[:3]:
                parts.append(str(b.get("summary", "") if isinstance(b, dict) else b))
        return "\n".join(parts)

    def _build_vector_memory(
        self,
        story_id: str,
        query_text: str,
        primary_characters: list[str] | None,
        budget: int,
    ) -> str:
        if not query_text:
            return ""
        lines = []
        used = 0
        # Per-character retrieval when primary_characters given
        if primary_characters:
            for cid in primary_characters[:3]:
                memories = self.vector.query_memories(
                    story_id=story_id, query_text=query_text,
                    character_id=cid, n_results=3,
                )
                for m in memories:
                    meta = m.get("metadata", {})
                    ch = meta.get("chapter", "?")
                    line = f"[ch{ch} {cid}] {m['text']}"
                    if used + len(line) > budget:
                        break
                    lines.append(line)
                    used += len(line)
        # Global semantic search top-3
        globals_ = self.vector.query_memories(
            story_id=story_id, query_text=query_text, n_results=3,
        )
        for m in globals_:
            meta = m.get("metadata", {})
            ch = meta.get("chapter", "?")
            cid = meta.get("character_id", "")
            line = f"[ch{ch} {cid}] {m['text']}"
            if line in lines:
                continue
            if used + len(line) > budget:
                break
            lines.append(line)
            used += len(line)
        return "\n".join(lines)

    def _build_scene_text(self, story_id: str, query_text: str, budget: int) -> str:
        if not query_text:
            return ""
        scenes = self.vector.query_scene_texts(
            story_id=story_id, query_text=query_text, n_results=2
        )
        lines = []
        used = 0
        for s in scenes:
            meta = s.get("metadata", {})
            ch = meta.get("chapter", "?")
            snippet = s["text"][:400]
            line = f"[ch{ch} 场景片段]\n{snippet}"
            if used + len(line) > budget:
                break
            lines.append(line)
            used += len(line)
        return "\n\n".join(lines)

    async def _build_character_cards(
        self,
        story_id: str,
        character_profiles: list[dict],
        chapter_num: int,
        primary_characters: list[str] | None = None,
        budget: int = 1500,
    ) -> str:
        if not character_profiles:
            return ""
        id_set = set(primary_characters) if primary_characters else None
        cards = []
        used = 0
        for c in character_profiles:
            cid = c.get("character_id", "")
            if id_set and cid not in id_set:
                continue
            card = await self._render_character_card(story_id, c, chapter_num)
            if used + len(card) > budget and cards:
                break
            cards.append(card)
            used += len(card)
        return "\n\n".join(cards)

    async def _render_character_card(
        self, story_id: str, char: dict, chapter_num: int
    ) -> str:
        name = char.get("name", "")
        role = char.get("role", "")
        cid = char.get("character_id", "")
        lines = [f"■ {name}（{role}/{cid}）"]
        personality = char.get("personality", "")
        if personality:
            lines.append(f"性格：{personality}")
        speech_examples = char.get("speech_examples") or []
        if speech_examples:
            examples = "；".join([f"「{s}」" for s in speech_examples[:3]])
            lines.append(f"说话风格示例：{examples}")
        speech_rules = char.get("speech_rules") or []
        if speech_rules:
            lines.append("说话规则：" + "；".join(speech_rules[:3]))
        mannerisms = char.get("mannerisms") or []
        if mannerisms:
            lines.append("习惯动作：" + "；".join(mannerisms[:3]))
        hard_constraints = char.get("hard_constraints") or []
        if hard_constraints:
            lines.append("⚠️ 硬约束（不可违反）：")
            for hc in hard_constraints[:5]:
                lines.append(f"  · {hc}")
        # Load latest active state
        state = await self._get_latest_state(story_id, cid, chapter_num - 1)
        if state:
            parts = []
            if state.get("emotional_state"):
                parts.append(f"情绪={state['emotional_state']}")
            if state.get("status"):
                parts.append(f"状态={state['status']}")
            if state.get("knowledge_summary"):
                parts.append(f"当前已知={state['knowledge_summary'][:80]}")
            if state.get("goals_update"):
                parts.append(f"目标动态={state['goals_update'][:80]}")
            if parts:
                lines.append("当前态势：" + "；".join(parts))
        return "\n".join(lines)

    async def _get_latest_state(
        self, story_id: str, character_id: str, up_to: int
    ) -> dict | None:
        import aiosqlite
        if up_to < 1:
            return None
        async with aiosqlite.connect(self.sqlite.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT * FROM character_states
                   WHERE story_id = ? AND character_id = ?
                     AND chapter_num <= ? AND is_active = 1
                   ORDER BY chapter_num DESC LIMIT 1""",
                (story_id, character_id, up_to),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def _build_relationships(
        self, story_id: str, character_profiles: list[dict],
        chapter_num: int, budget: int,
    ) -> str:
        lines = []
        used = 0
        for c in character_profiles:
            cid = c.get("character_id", "")
            if not cid:
                continue
            text = await self.kg.format_relationships_for_prompt(
                story_id, cid, character_profiles
            )
            if text and text != "暂无已知关系记录。":
                line = f"— {c.get('name', cid)} —\n{text}"
                if used + len(line) > budget and lines:
                    break
                lines.append(line)
                used += len(line)
        return "\n\n".join(lines)

    async def _build_unresolved_threads(
        self, story_id: str, chapter_num: int, budget: int
    ) -> str:
        if chapter_num <= 1:
            return ""
        summaries = await self.sqlite.list_recent_summaries(
            story_id, up_to_chapter=chapter_num - 1, limit=8
        )
        all_threads: list[tuple[int, str]] = []
        for s in summaries:
            ch = s["chapter_num"]
            for t in s.get("unresolved_threads") or []:
                all_threads.append((ch, str(t)))
        if not all_threads:
            return ""
        lines = []
        used = 0
        # Most recent first (LIFO — they're typically still open)
        for ch, t in reversed(all_threads):
            line = f"[ch{ch}] {t}"
            if used + len(line) > budget and lines:
                break
            lines.append(line)
            used += len(line)
        return "\n".join(lines)


def _truncate(text: str, budget: int) -> str:
    if not text or len(text) <= budget:
        return text or ""
    # Truncate on paragraph boundary if possible
    cut = text[:budget]
    last_nl = cut.rfind("\n")
    if last_nl > budget * 0.7:
        return cut[:last_nl] + "\n…(已截断)"
    return cut + "…(已截断)"


def bundle_to_writer_text(bundle: ContextBundle) -> str:
    """Render a ContextBundle as a single prompt block for writer-style agents."""
    sections: list[tuple[str, str]] = [
        ("### 作品设定核心", bundle.bible_core),
        ("### 世界设定（触发）", bundle.lorebook),
        ("### 在场角色卡", bundle.character_cards),
        ("### 当前人物关系", bundle.relationships),
        ("### 最近章节梗概", bundle.recent_summary),
        ("### 上章结尾原文（保持语感）", bundle.last_tail),
        ("### 未解伏笔 / 未兑现承诺（本章可呼应）", bundle.unresolved_threads),
        ("### 相关记忆检索", bundle.vector_memory),
        ("### 相关场景片段", bundle.scene_text),
    ]
    parts = [f"{title}\n{body}" for title, body in sections if body and body.strip()]
    return "\n\n".join(parts)
