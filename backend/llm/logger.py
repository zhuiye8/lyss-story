import logging
from datetime import datetime, timezone

import aiosqlite

logger = logging.getLogger(__name__)


class LLMLogger:
    """Records every LLM call with full prompt/response data for debugging and monitoring."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def log_call(
        self,
        agent_name: str,
        model_config_id: str,
        litellm_model: str,
        system_prompt: str,
        user_prompt: str,
        response: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        cost_estimate: float = 0.0,
        latency_ms: int = 0,
        story_id: str | None = None,
        chapter_num: int | None = None,
        status: str = "success",
        error_message: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """INSERT INTO llm_logs
                       (story_id, chapter_num, agent_name, model_config_id, litellm_model,
                        system_prompt, user_prompt, response,
                        input_tokens, output_tokens, total_tokens,
                        cost_estimate, latency_ms, status, error_message, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        story_id, chapter_num, agent_name, model_config_id, litellm_model,
                        system_prompt, user_prompt, response,
                        input_tokens, output_tokens, total_tokens,
                        cost_estimate, latency_ms, status, error_message, now,
                    ),
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to log LLM call: {e}")

    async def get_logs(
        self,
        agent_name: str | None = None,
        story_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        conditions = []
        params = []
        if agent_name:
            conditions.append("agent_name = ?")
            params.append(agent_name)
        if story_id:
            conditions.append("story_id = ?")
            params.append(story_id)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                f"""SELECT id, story_id, chapter_num, agent_name, model_config_id,
                           litellm_model, input_tokens, output_tokens, total_tokens,
                           cost_estimate, latency_ms, status, error_message, created_at
                    FROM llm_logs {where}
                    ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                params + [limit, offset],
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def get_log_detail(self, log_id: int) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM llm_logs WHERE id = ?", (log_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_usage_stats(
        self, group_by: str = "agent", days: int = 7
    ) -> list[dict]:
        if group_by == "agent":
            group_col = "agent_name"
        elif group_by == "story":
            group_col = "story_id"
        elif group_by == "model":
            group_col = "litellm_model"
        else:
            group_col = "agent_name"

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                f"""SELECT {group_col} as group_key,
                           COUNT(*) as total_calls,
                           SUM(input_tokens) as total_input_tokens,
                           SUM(output_tokens) as total_output_tokens,
                           SUM(total_tokens) as total_tokens,
                           SUM(cost_estimate) as total_cost,
                           AVG(latency_ms) as avg_latency_ms
                    FROM llm_logs
                    WHERE created_at >= datetime('now', '-{days} days')
                      AND status = 'success'
                    GROUP BY {group_col}
                    ORDER BY total_tokens DESC""",
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def get_total_stats(self, days: int = 7) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                f"""SELECT COUNT(*) as total_calls,
                           SUM(input_tokens) as total_input_tokens,
                           SUM(output_tokens) as total_output_tokens,
                           SUM(total_tokens) as total_tokens,
                           SUM(cost_estimate) as total_cost,
                           AVG(latency_ms) as avg_latency_ms
                    FROM llm_logs
                    WHERE created_at >= datetime('now', '-{days} days')
                      AND status = 'success'""",
            )
            row = await cursor.fetchone()
            return dict(row) if row else {}
