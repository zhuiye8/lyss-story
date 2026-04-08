from backend.agents.base import BaseAgent
from backend.prompts.world import SYSTEM_PROMPT, build_user_prompt


class WorldAgent(BaseAgent):
    name = "world"

    async def run(
        self,
        *,
        story_bible: dict,
        world_state: dict,
        event_history: list[dict],
        character_profiles: list[dict],
        story_id: str | None = None,
        chapter_num: int | None = None,
    ) -> dict:
        user_prompt = build_user_prompt(
            story_bible=story_bible,
            world_state=world_state,
            event_history=event_history,
            character_profiles=character_profiles,
        )
        return await self._call_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            story_id=story_id,
            chapter_num=chapter_num,
        )
