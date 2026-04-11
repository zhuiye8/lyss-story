import logging

from backend.agents.base import BaseAgent
from backend.prompts.titler import TITLER_SYSTEM, TITLER_USER

logger = logging.getLogger(__name__)


class TitlerAgent(BaseAgent):
    name = "titler"

    async def run(
        self,
        *,
        chapter_draft: str,
        chapter_num: int,
        story_title: str = "",
        chapter_goal: str = "",
        story_id: str | None = None,
    ) -> dict:
        user_prompt = TITLER_USER.format(
            story_title=story_title,
            chapter_num=chapter_num,
            chapter_goal=chapter_goal,
            chapter_excerpt=chapter_draft[:1000],
        )

        result = await self._call_json(
            TITLER_SYSTEM,
            user_prompt,
            story_id=story_id,
            chapter_num=chapter_num,
            temperature=0.3,
            max_tokens=256,
        )

        title = result.get("title", "").strip()
        logger.info(f"[titler] Chapter {chapter_num} title: {title}")
        return {"title": title}
