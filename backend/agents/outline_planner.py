from backend.agents.base import BaseAgent
from backend.prompts.outline_planner import SYSTEM_PROMPT, build_user_prompt


class OutlinePlannerAgent(BaseAgent):
    name = "outline_planner"

    async def run(
        self,
        *,
        concept: dict,
        world_setting: dict,
        characters_design: dict,
        story_id: str | None = None,
    ) -> dict:
        user_prompt = build_user_prompt(concept, world_setting, characters_design)
        return await self._call_json(
            SYSTEM_PROMPT,
            user_prompt,
            story_id=story_id,
            max_tokens=6144,
        )
