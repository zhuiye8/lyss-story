from backend.agents.base import BaseAgent
from backend.prompts.camera import SYSTEM_PROMPT, build_user_prompt


class CameraAgent(BaseAgent):
    name = "camera"

    async def run(
        self,
        *,
        plot_structure: dict,
        character_profiles: list[dict],
        chapter_num: int,
        previous_povs: list[str],
        story_id: str | None = None,
    ) -> dict:
        user_prompt = build_user_prompt(
            plot_structure=plot_structure,
            character_profiles=character_profiles,
            chapter_num=chapter_num,
            previous_povs=previous_povs,
        )
        return await self._call_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            story_id=story_id,
            chapter_num=chapter_num,
        )
