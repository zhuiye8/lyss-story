from backend.agents.base import BaseAgent
from backend.prompts.planner import SYSTEM_PROMPT, build_user_prompt


class PlotPlannerAgent(BaseAgent):
    name = "planner"

    async def run(
        self,
        *,
        story_bible: dict,
        new_events: list[dict],
        chapter_num: int,
        event_history: list[dict],
        story_id: str | None = None,
    ) -> dict:
        user_prompt = build_user_prompt(
            story_bible=story_bible,
            new_events=new_events,
            chapter_num=chapter_num,
            event_history=event_history,
        )
        return await self._call_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            story_id=story_id,
            chapter_num=chapter_num,
        )
