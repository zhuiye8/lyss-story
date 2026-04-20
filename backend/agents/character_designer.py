from backend.agents.base import BaseAgent
from backend.prompts.character_designer import SYSTEM_PROMPT, build_user_prompt


class CharacterDesigner(BaseAgent):
    name = "character_designer"

    async def run(
        self,
        *,
        concept: dict,
        world_setting: dict,
        story_id: str | None = None,
    ) -> dict:
        user_prompt = build_user_prompt(concept, world_setting)
        return await self._call_json(
            SYSTEM_PROMPT,
            user_prompt,
            story_id=story_id,
            max_tokens=4096,
        )
