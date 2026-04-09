from backend.agents.base import BaseAgent
from backend.prompts.consistency import SYSTEM_PROMPT, build_user_prompt


class ConsistencyAgent(BaseAgent):
    name = "consistency"

    async def run(
        self,
        *,
        chapter_draft: str,
        story_bible: dict,
        world_state: dict,
        character_profiles: list[dict],
        camera_decision: dict,
        plot_structure: dict,
        memory_contexts: dict | None = None,
        story_id: str | None = None,
        chapter_num: int | None = None,
    ) -> dict:
        user_prompt = build_user_prompt(
            chapter_draft=chapter_draft,
            story_bible=story_bible,
            world_state=world_state,
            character_profiles=character_profiles,
            camera_decision=camera_decision,
            plot_structure=plot_structure,
            memory_contexts=memory_contexts,
        )
        return await self._call_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            story_id=story_id,
            chapter_num=chapter_num,
            max_tokens=4096,
        )
