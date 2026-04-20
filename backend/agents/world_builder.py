from backend.agents.base import BaseAgent
from backend.prompts.world_builder import SYSTEM_PROMPT, build_user_prompt


class WorldBuilderAgent(BaseAgent):
    name = "world_builder"

    async def run(
        self,
        *,
        concept: dict,
        story_id: str | None = None,
    ) -> dict:
        user_prompt = build_user_prompt(concept)
        return await self._call_json(
            SYSTEM_PROMPT,
            user_prompt,
            story_id=story_id,
            max_tokens=4096,
        )
