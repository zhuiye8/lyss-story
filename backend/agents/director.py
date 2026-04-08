from backend.agents.base import BaseAgent
from backend.prompts.director import SYSTEM_PROMPT, build_user_prompt


class DirectorAgent(BaseAgent):
    name = "director"

    async def run(self, *, user_theme: str, user_requirements: str = "") -> dict:
        user_prompt = build_user_prompt(user_theme, user_requirements)
        return await self._call_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=8192,
        )
