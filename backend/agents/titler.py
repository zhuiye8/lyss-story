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
        previous_time_marker: str = "",
        story_id: str | None = None,
    ) -> dict:
        previous_time_context = ""
        if previous_time_marker:
            previous_time_context = f"\n前一章时间标记：{previous_time_marker}\n"

        user_prompt = TITLER_USER.format(
            story_title=story_title,
            chapter_num=chapter_num,
            chapter_goal=chapter_goal,
            previous_time_context=previous_time_context,
            chapter_excerpt=chapter_draft[:1000],
        )

        result = await self._call_json(
            TITLER_SYSTEM,
            user_prompt,
            story_id=story_id,
            chapter_num=chapter_num,
            temperature=0.3,
            max_tokens=512,
        )

        title = result.get("title", "").strip()
        time_marker = result.get("time_marker", "").strip()
        logger.info(f"[titler] Chapter {chapter_num}: title={title}, time={time_marker}")
        return result
