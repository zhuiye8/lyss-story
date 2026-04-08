from backend.agents.base import BaseAgent
from backend.prompts.writer import SYSTEM_PROMPT, build_user_prompt


class WriterAgent(BaseAgent):
    name = "writer"

    async def run(
        self,
        *,
        story_bible: dict,
        plot_structure: dict,
        camera_decision: dict,
        character_profiles: list[dict],
        chapter_num: int,
        previous_chapter_summary: str = "",
        retry_feedback: str = "",
        story_id: str | None = None,
    ) -> str:
        user_prompt = build_user_prompt(
            story_bible=story_bible,
            plot_structure=plot_structure,
            camera_decision=camera_decision,
            character_profiles=character_profiles,
            chapter_num=chapter_num,
            previous_chapter_summary=previous_chapter_summary,
            retry_feedback=retry_feedback,
        )
        return await self._call_text(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            story_id=story_id,
            chapter_num=chapter_num,
            temperature=0.8,
            max_tokens=8192,
        )
