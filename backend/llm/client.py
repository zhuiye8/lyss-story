import json
import logging
import time

import litellm

from backend.config import Settings
from backend.llm.logger import LLMLogger
from backend.llm.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(
        self,
        settings: Settings,
        registry: ModelRegistry | None = None,
        llm_logger: LLMLogger | None = None,
    ):
        self.default_model = settings.litellm_model
        self.default_api_key = settings.litellm_api_key
        self.default_api_base = settings.litellm_api_base
        self.registry = registry
        self.llm_logger = llm_logger

    async def _resolve_model(self, agent_name: str) -> dict:
        """Resolve model config for an agent. Returns dict with model, api_key, api_base, temperature, max_tokens."""
        if self.registry and agent_name != "unknown":
            config = await self.registry.get_model_for_agent(agent_name)
            if config:
                return {
                    "model": config["litellm_model"],
                    "api_key": config["api_key"] or self.default_api_key,
                    "api_base": config.get("api_base") or self.default_api_base,
                    "model_config_id": config["id"],
                    "cost_per_million_input": config.get("cost_per_million_input", 0),
                    "cost_per_million_output": config.get("cost_per_million_output", 0),
                    "currency": config.get("currency", "CNY"),
                }
        return {
            "model": self.default_model,
            "api_key": self.default_api_key,
            "api_base": self.default_api_base,
            "model_config_id": "default",
            "cost_per_million_input": 0,
            "cost_per_million_output": 0,
            "currency": "CNY",
        }

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        agent_name: str = "unknown",
        story_id: str | None = None,
        chapter_num: int | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: dict | None = None,
    ) -> str:
        resolved = await self._resolve_model(agent_name)

        kwargs: dict = {
            "model": resolved["model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "api_key": resolved["api_key"],
        }
        if resolved["api_base"]:
            kwargs["api_base"] = resolved["api_base"]
        if response_format:
            kwargs["response_format"] = response_format

        start_time = time.time()
        status = "success"
        error_msg = None
        content = ""
        input_tokens = output_tokens = total_tokens = 0

        try:
            response = await litellm.acompletion(**kwargs)
            content = response.choices[0].message.content

            # Extract token usage
            usage = getattr(response, "usage", None)
            if usage:
                input_tokens = getattr(usage, "prompt_tokens", 0) or 0
                output_tokens = getattr(usage, "completion_tokens", 0) or 0
                total_tokens = getattr(usage, "total_tokens", 0) or 0
        except Exception as e:
            status = "error"
            error_msg = str(e)[:500]
            raise
        finally:
            latency_ms = int((time.time() - start_time) * 1000)

            # Calculate cost (per million tokens)
            cost = (
                input_tokens / 1_000_000 * resolved["cost_per_million_input"]
                + output_tokens / 1_000_000 * resolved["cost_per_million_output"]
            )
            currency = resolved.get("currency", "CNY")

            # Log asynchronously (don't block on logging failure)
            if self.llm_logger:
                try:
                    await self.llm_logger.log_call(
                        agent_name=agent_name,
                        model_config_id=resolved["model_config_id"],
                        litellm_model=resolved["model"],
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        response=content,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total_tokens,
                        cost_estimate=cost,
                        latency_ms=latency_ms,
                        story_id=story_id,
                        chapter_num=chapter_num,
                        status=status,
                        error_message=error_msg,
                    )
                except Exception as log_err:
                    logger.error(f"Failed to log LLM call: {log_err}")

            cost_symbol = "¥" if currency == "CNY" else "$"
            logger.info(
                f"[LLM] agent={agent_name} model={resolved['model']} "
                f"tokens={total_tokens} latency={latency_ms}ms cost={cost_symbol}{cost:.4f} status={status}"
            )

        return content

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        agent_name: str = "unknown",
        story_id: str | None = None,
        chapter_num: int | None = None,
        temperature: float = 0.4,
        max_tokens: int = 4096,
    ) -> dict:
        raw = await self.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            agent_name=agent_name,
            story_id=story_id,
            chapter_num=chapter_num,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)
        return json.loads(text)
