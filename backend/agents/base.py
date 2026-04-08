import json
import logging
from abc import ABC, abstractmethod

from backend.llm.client import LLMClient

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    name: str = "base"

    def __init__(self, llm: LLMClient):
        self.llm = llm

    @abstractmethod
    async def run(self, **kwargs) -> dict:
        ...

    async def _call_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        story_id: str | None = None,
        chapter_num: int | None = None,
        retries: int = 2,
        temperature: float = 0.4,
        max_tokens: int = 4096,
    ) -> dict:
        for attempt in range(retries + 1):
            try:
                return await self.llm.complete_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    agent_name=self.name,
                    story_id=story_id,
                    chapter_num=chapter_num,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(
                    f"[{self.name}] JSON parse failed (attempt {attempt+1}/{retries+1}): {e}"
                )
                if attempt == retries:
                    raise

    async def _call_text(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        story_id: str | None = None,
        chapter_num: int | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> str:
        return await self.llm.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            agent_name=self.name,
            story_id=story_id,
            chapter_num=chapter_num,
            temperature=temperature,
            max_tokens=max_tokens,
        )
