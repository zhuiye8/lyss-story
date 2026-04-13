from backend.agents.base import BaseAgent
from backend.prompts.director import SYSTEM_PROMPT, build_user_prompt


class DirectorAgent(BaseAgent):
    name = "director"

    async def run(
        self,
        *,
        user_theme: str,
        user_requirements: str = "",
        title: str = "",
        story_id: str | None = None,
    ) -> dict:
        user_prompt = build_user_prompt(user_theme, user_requirements, title=title)
        result = await self._call_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            story_id=story_id,
            max_tokens=12288,
        )
        result.setdefault("bible_version", 2)
        return result
