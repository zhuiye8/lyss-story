from backend.agents.base import BaseAgent
from backend.prompts.concept import SYSTEM_PROMPT, build_user_prompt


class ConceptAgent(BaseAgent):
    name = "concept"

    async def run(
        self,
        *,
        user_theme: str,
        user_requirements: str = "",
        title: str = "",
        story_id: str | None = None,
    ) -> dict:
        user_prompt = build_user_prompt(user_theme, user_requirements, title=title)
        return await self._call_json(
            SYSTEM_PROMPT,
            user_prompt,
            story_id=story_id,
            max_tokens=4096,
            temperature=0.7,
        )
