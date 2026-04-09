"""Four-layer memory stack for character agents, inspired by MemPalace."""

import logging
from dataclasses import dataclass, field

from backend.memory.knowledge_graph import KnowledgeGraph
from backend.storage.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class CharacterMemoryContext:
    character_id: str
    character_name: str
    identity_core: str = ""       # L0
    key_memories: str = ""        # L1
    scene_relevant: str = ""      # L2
    relationship_summary: str = "" # From knowledge graph
    total_tokens_estimate: int = 0

    def to_prompt_text(self) -> str:
        """Format memory context for prompt injection."""
        sections = []

        if self.identity_core:
            sections.append(f"### 身份核心\n{self.identity_core}")

        if self.key_memories:
            sections.append(f"### 关键记忆\n{self.key_memories}")

        if self.scene_relevant:
            sections.append(f"### 当前场景相关\n{self.scene_relevant}")

        if self.relationship_summary:
            sections.append(f"### 人际关系\n{self.relationship_summary}")

        if not sections:
            return "暂无角色记忆数据。"

        return "\n\n".join(sections)


class LayeredMemory:
    """Builds tiered memory context for characters.

    L0 - Identity Core (~100 tokens): personality, background, goals. Always loaded.
    L1 - Key Memories (~500 tokens): top-K by emotional_weight. Loaded at chapter start.
    L2 - Scene Relevant (~300 tokens): filtered by current scene context. Loaded per scene.
    L3 - Deep Search (on demand): full semantic search. Only for specific queries.
    """

    def __init__(self, vector_store: VectorStore, knowledge_graph: KnowledgeGraph):
        self.vector = vector_store
        self.kg = knowledge_graph

    async def build_context(
        self,
        story_id: str,
        character_id: str,
        character_profiles: list[dict],
        chapter_num: int,
        scene_query: str = "",
    ) -> CharacterMemoryContext:
        """Build layered memory context for a character."""
        # Find character profile
        char_profile = None
        for c in character_profiles:
            if c.get("character_id") == character_id:
                char_profile = c
                break

        if not char_profile:
            return CharacterMemoryContext(
                character_id=character_id,
                character_name=character_id,
            )

        char_name = char_profile.get("name", character_id)

        # Build all layers
        l0 = self._build_l0(char_profile)
        l1 = self._build_l1(story_id, character_id)
        l2 = self._build_l2(story_id, character_id, scene_query) if scene_query else ""
        rel_summary = await self.kg.format_relationships_for_prompt(
            story_id, character_id, character_profiles
        )

        # Estimate tokens (~1 token per 1.5 Chinese chars)
        total_text = l0 + l1 + l2 + rel_summary
        token_estimate = int(len(total_text) / 1.5)

        ctx = CharacterMemoryContext(
            character_id=character_id,
            character_name=char_name,
            identity_core=l0,
            key_memories=l1,
            scene_relevant=l2,
            relationship_summary=rel_summary,
            total_tokens_estimate=token_estimate,
        )

        logger.info(
            f"[LayeredMemory] {char_name}: L0={len(l0)}c L1={len(l1)}c "
            f"L2={len(l2)}c REL={len(rel_summary)}c total~{token_estimate}tok"
        )
        return ctx

    def _build_l0(self, char_profile: dict) -> str:
        """L0: Identity core - always loaded."""
        parts = []
        name = char_profile.get("name", "")
        personality = char_profile.get("personality", "")
        background = char_profile.get("background", "")
        goals = char_profile.get("goals", [])
        role = char_profile.get("role", "")

        if name:
            parts.append(f"姓名：{name}（{role}）")
        if personality:
            parts.append(f"性格：{personality}")
        if background:
            # Truncate background to ~100 chars for L0
            bg = background[:150] + "..." if len(background) > 150 else background
            parts.append(f"背景：{bg}")
        if goals:
            parts.append(f"目标：{'、'.join(goals[:3])}")

        return "\n".join(parts)

    def _build_l1(self, story_id: str, character_id: str) -> str:
        """L1: Key memories ranked by emotional weight."""
        memories = self.vector.query_by_emotional_weight(
            story_id, character_id, top_k=8
        )

        if not memories:
            return ""

        lines = []
        for m in memories:
            chapter = m.get("metadata", {}).get("chapter", "?")
            category = m.get("metadata", {}).get("category", "event")
            weight = m.get("emotional_weight", 0.5)
            # Show weight indicator
            weight_indicator = "!!!" if weight >= 0.8 else "!!" if weight >= 0.6 else "!"
            lines.append(f"[第{chapter}章/{category}]{weight_indicator} {m['text']}")

        return "\n".join(lines)

    def _build_l2(self, story_id: str, character_id: str, scene_query: str) -> str:
        """L2: Scene-relevant memories via semantic search."""
        if not scene_query:
            return ""

        memories = self.vector.query_memories(
            story_id, scene_query, character_id=character_id, n_results=5
        )

        if not memories:
            return ""

        lines = []
        for m in memories:
            chapter = m.get("metadata", {}).get("chapter", "?")
            lines.append(f"[第{chapter}章] {m['text']}")

        return "\n".join(lines)
