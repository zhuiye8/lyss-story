"""Extract structured memories + chapter summary from generated chapter content."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

import aiosqlite

from backend.llm.client import LLMClient
from backend.memory.knowledge_graph import KnowledgeGraph
from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore

logger = logging.getLogger(__name__)

EXTRACTOR_SYSTEM_PROMPT = """你是小说记忆提取专家。你的任务是从小说章节内容中提取结构化的角色记忆、关系变化，以及本章摘要、关键事件、未解伏笔。

你必须输出严格的JSON格式：
{
  "character_memories": [
    {
      "character_id": "角色ID",
      "category": "event/emotion/relationship/knowledge/decision",
      "content": "该角色在本章经历/感受/学到的具体内容（简洁，1-2句话）",
      "emotional_weight": 0.0-1.0,
      "related_characters": ["关联角色ID"],
      "location": "发生地点",
      "visibility": "witnessed/heard/inferred"
    }
  ],
  "relationship_changes": [
    {
      "subject": "角色ID",
      "predicate": "关系类型（如：信任/怀疑/敌对/保护/依赖/知道秘密）",
      "object": "目标角色ID或事实",
      "detail": "变化说明",
      "change_type": "new/strengthen/weaken/invalidate"
    }
  ],
  "character_states": [
    {
      "character_id": "角色ID",
      "emotional_state": "当前主要情绪",
      "knowledge_summary": "本章后角色知道的关键信息",
      "goals_update": "目标是否变化，如何变化",
      "status": "active/injured/captured/dead"
    }
  ],
  "chapter_summary": {
    "brief": "本章一段话梗概（100-150字，不要剧透下一章，只总结已发生）",
    "key_events": ["事件1（不超过20字）", "事件2", "事件3"],
    "unresolved_threads": ["本章埋的但未解的伏笔/未兑现的承诺（简洁一句话）", "..."]
  }
}

提取规则：
1. 只为在场角色提取记忆（参考可见事件列表）
2. emotional_weight: 0.9-1.0=改变人生的大事, 0.7-0.8=重要发现/冲突, 0.4-0.6=日常事件, 0.1-0.3=琐碎细节
3. visibility: witnessed=亲眼所见, heard=听说/被告知, inferred=推测/间接了解
4. 关系变化要具体：不要只说"关系变化"，要说具体怎么变（如"从怀疑转为初步信任"）
5. 每个角色提取2-5条记忆，不要遗漏关键事件
6. chapter_summary.brief 必须 100-150 字，按时间顺序概括
7. unresolved_threads 只列**本章新埋下且尚未在本章解决**的伏笔、承诺、悬念"""


def _build_extractor_prompt(
    chapter_content: str,
    chapter_num: int,
    character_profiles: list[dict],
    camera_decision: dict,
) -> str:
    pov_id = camera_decision.get("pov_character_id", "")
    visible = camera_decision.get("visible_events", [])

    chars_info = json.dumps(
        [{"id": c.get("character_id"), "name": c.get("name"), "role": c.get("role")}
         for c in character_profiles],
        ensure_ascii=False, indent=2,
    )

    return f"""## 章节信息

第{chapter_num}章（POV角色：{pov_id}）

## 在场角色
{chars_info}

## 可见事件
{json.dumps(visible, ensure_ascii=False)}

## 章节正文

{chapter_content}

请从以上章节中提取每个在场角色的记忆、关系变化、状态更新，以及本章摘要、关键事件、未解伏笔。"""


def _extract_tail_snippet(chapter_content: str, max_chars: int = 300) -> str:
    """Take the last ~max_chars of the chapter as a raw tail snippet for prompt continuity."""
    content = chapter_content.strip()
    if len(content) <= max_chars:
        return content
    # Try to cut at a paragraph boundary
    tail = content[-max_chars:]
    first_break = tail.find("\n")
    if 0 < first_break < max_chars // 3:
        tail = tail[first_break + 1 :]
    return tail.strip()


@dataclass
class ExtractionResult:
    character_memories: list[dict] = field(default_factory=list)
    relationship_changes: list[dict] = field(default_factory=list)
    character_states: list[dict] = field(default_factory=list)
    chapter_summary: dict = field(default_factory=dict)


class ChapterExtractor:
    name = "extractor"

    def __init__(
        self,
        llm: LLMClient,
        vector_store: VectorStore,
        knowledge_graph: KnowledgeGraph,
        db_path: str,
        sqlite_store: SQLiteStore | None = None,
    ):
        self.llm = llm
        self.vector = vector_store
        self.kg = knowledge_graph
        self.db_path = db_path
        self.sqlite = sqlite_store

    async def extract_and_save(
        self,
        story_id: str,
        chapter_num: int,
        chapter_content: str,
        character_profiles: list[dict],
        camera_decision: dict,
        source_version_id: int | None = None,
    ) -> ExtractionResult:
        """Extract memories + summary from chapter content and save to stores."""
        # 1. Call LLM to extract structured data
        user_prompt = _build_extractor_prompt(
            chapter_content, chapter_num, character_profiles, camera_decision
        )

        try:
            extracted = await self.llm.complete_json(
                system_prompt=EXTRACTOR_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                agent_name=self.name,
                story_id=story_id,
                chapter_num=chapter_num,
                max_tokens=4096,
            )
        except Exception as e:
            logger.error(f"[ChapterExtractor] LLM extraction failed: {e}")
            return ExtractionResult()

        result = ExtractionResult(
            character_memories=extracted.get("character_memories", []),
            relationship_changes=extracted.get("relationship_changes", []),
            character_states=extracted.get("character_states", []),
            chapter_summary=extracted.get("chapter_summary") or {},
        )

        # 2. Save character memories to vector store (versioned)
        for i, mem in enumerate(result.character_memories):
            cid = mem.get("character_id", "")
            if not cid:
                continue
            memory_id = f"ch{chapter_num}_v{source_version_id or 0}_{cid}_{i}"
            self.vector.add_memory(
                story_id=story_id,
                memory_id=memory_id,
                text=mem.get("content", ""),
                metadata={
                    "character_id": cid,
                    "chapter": chapter_num,
                    "category": mem.get("category", "event"),
                    "emotional_weight": mem.get("emotional_weight", 0.5),
                    "related_characters": mem.get("related_characters", []),
                    "location": mem.get("location", ""),
                    "visibility": mem.get("visibility", "witnessed"),
                },
                source_version_id=source_version_id,
            )

        # 3. Save relationship changes to knowledge graph (versioned)
        for rel in result.relationship_changes:
            subject = rel.get("subject", "")
            predicate = rel.get("predicate", "")
            obj = rel.get("object", "")
            if not (subject and predicate and obj):
                continue

            change_type = rel.get("change_type", "new")
            if change_type == "invalidate" or change_type == "weaken":
                await self.kg.invalidate(story_id, subject, predicate, obj, chapter_num)
                if change_type == "weaken":
                    await self.kg.add_triple(
                        story_id, subject, f"{predicate}（减弱）", obj,
                        chapter_num, detail=rel.get("detail", ""),
                        source=f"ch{chapter_num}",
                        source_version_id=source_version_id,
                    )
            else:
                await self.kg.add_triple(
                    story_id, subject, predicate, obj,
                    chapter_num, detail=rel.get("detail", ""),
                    source=f"ch{chapter_num}",
                    source_version_id=source_version_id,
                )

        # 4. Save character states (versioned)
        async with aiosqlite.connect(self.db_path) as db:
            for cs in result.character_states:
                cid = cs.get("character_id", "")
                if not cid:
                    continue
                await db.execute(
                    """INSERT OR REPLACE INTO character_states
                       (story_id, character_id, chapter_num, source_version_id,
                        emotional_state, knowledge_summary, goals_update, status,
                        state_json, is_active)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                    (
                        story_id, cid, chapter_num, source_version_id or 0,
                        cs.get("emotional_state", ""),
                        cs.get("knowledge_summary", ""),
                        cs.get("goals_update", ""),
                        cs.get("status", "active"),
                        json.dumps(cs, ensure_ascii=False),
                    ),
                )
            await db.commit()

        # 5. Save chapter summary (Phase 3 - brief + key_events + unresolved_threads + tail)
        if self.sqlite and result.chapter_summary:
            try:
                brief = str(result.chapter_summary.get("brief", "")).strip()
                key_events = result.chapter_summary.get("key_events") or []
                unresolved = result.chapter_summary.get("unresolved_threads") or []
                tail = _extract_tail_snippet(chapter_content, max_chars=300)
                await self.sqlite.save_chapter_summary(
                    story_id=story_id,
                    chapter_num=chapter_num,
                    source_version_id=source_version_id or 0,
                    brief=brief,
                    key_events=[str(e) for e in key_events if e],
                    unresolved_threads=[str(u) for u in unresolved if u],
                    tail_snippet=tail,
                )
            except Exception as e:
                logger.warning(f"[ChapterExtractor] Failed to save chapter summary: {e}")

        logger.info(
            f"[ChapterExtractor] ch{chapter_num} v{source_version_id}: "
            f"{len(result.character_memories)} memories, "
            f"{len(result.relationship_changes)} rel changes, "
            f"{len(result.character_states)} state updates, "
            f"summary={'yes' if result.chapter_summary else 'no'}"
        )
        return result
