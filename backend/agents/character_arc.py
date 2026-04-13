import logging

from backend.agents.base import BaseAgent
from backend.prompts.character_arc import (
    CHARACTER_ARC_SYSTEM,
    build_character_arc_user_prompt,
)

logger = logging.getLogger(__name__)


class CharacterArcAgent(BaseAgent):
    name = "character_arc"

    async def run(
        self,
        *,
        character_profile: dict,
        recent_chapters: list[dict],
        previous_arc_summary: dict | None,
        current_arc_info: dict,
        story_id: str | None = None,
        chapter_num: int,
    ) -> dict:
        user_prompt = build_character_arc_user_prompt(
            character_profile=character_profile,
            recent_chapters=recent_chapters,
            previous_arc_summary=previous_arc_summary,
            current_arc_info=current_arc_info,
            chapter_num=chapter_num,
        )

        result = await self._call_json(
            CHARACTER_ARC_SYSTEM,
            user_prompt,
            story_id=story_id,
            chapter_num=chapter_num,
            temperature=0.4,
            max_tokens=1024,
        )

        name = character_profile.get("name", "?")
        arc = current_arc_info.get("name", "?")
        logger.info(
            f"[character_arc] {name} @ {arc}: "
            f"phase={result.get('current_phase', '')[:30]}"
        )
        return result
