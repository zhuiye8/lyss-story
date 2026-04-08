import json
import logging
from datetime import datetime, timezone

import aiosqlite

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Manages model configurations and agent-model bindings from SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def list_models(self, active_only: bool = False) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM model_configs"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY created_at DESC"
            cursor = await db.execute(query)
            return [dict(row) for row in await cursor.fetchall()]

    async def get_model(self, model_id: str) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM model_configs WHERE id = ?", (model_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def save_model(self, config: dict) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO model_configs
                   (id, display_name, litellm_model, api_key, api_base,
                    max_tokens, default_temperature,
                    cost_per_1k_input, cost_per_1k_output, is_active, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    config["id"],
                    config["display_name"],
                    config["litellm_model"],
                    config.get("api_key", ""),
                    config.get("api_base"),
                    config.get("max_tokens", 4096),
                    config.get("default_temperature", 0.7),
                    config.get("cost_per_1k_input", 0),
                    config.get("cost_per_1k_output", 0),
                    config.get("is_active", True),
                    config.get("created_at", now),
                ),
            )
            await db.commit()

    async def delete_model(self, model_id: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM agent_model_bindings WHERE model_config_id = ?", (model_id,))
            await db.execute("DELETE FROM model_configs WHERE id = ?", (model_id,))
            await db.commit()

    async def get_bindings(self) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT b.*, m.display_name as model_display_name, m.litellm_model
                   FROM agent_model_bindings b
                   LEFT JOIN model_configs m ON b.model_config_id = m.id"""
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def bind_agent(
        self,
        agent_name: str,
        model_config_id: str,
        temperature_override: float | None = None,
        max_tokens_override: int | None = None,
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO agent_model_bindings
                   (agent_name, model_config_id, temperature_override, max_tokens_override)
                   VALUES (?, ?, ?, ?)""",
                (agent_name, model_config_id, temperature_override, max_tokens_override),
            )
            await db.commit()

    async def unbind_agent(self, agent_name: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM agent_model_bindings WHERE agent_name = ?", (agent_name,))
            await db.commit()

    async def get_model_for_agent(self, agent_name: str) -> dict | None:
        """Get the resolved model config for a specific agent.
        Returns dict with model config + any binding overrides, or None if no binding."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT m.*, b.temperature_override, b.max_tokens_override
                   FROM agent_model_bindings b
                   JOIN model_configs m ON b.model_config_id = m.id
                   WHERE b.agent_name = ? AND m.is_active = 1""",
                (agent_name,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            result = dict(row)
            # Apply overrides
            if result.get("temperature_override") is not None:
                result["default_temperature"] = result["temperature_override"]
            if result.get("max_tokens_override") is not None:
                result["max_tokens"] = result["max_tokens_override"]
            return result
