import logging

from backend.agents.base import BaseAgent
from backend.prompts.outline_parser import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


class OutlineParserAgent(BaseAgent):
    name = "outline_parser"

    async def run(
        self,
        *,
        raw_text: str,
        title_hint: str = "",
        story_id: str | None = None,
    ) -> dict:
        user_prompt = build_user_prompt(raw_text, title_hint)
        result = await self._call_json(
            SYSTEM_PROMPT,
            user_prompt,
            story_id=story_id,
            max_tokens=8192,
            temperature=0.3,
        )
        result["bible_version"] = 2
        logger.info(
            f"[outline_parser] Parsed outline: title={result.get('title', '')}, "
            f"volumes={len(result.get('volumes', []))}, "
            f"characters={len(result.get('characters', []))}"
        )
        return result
