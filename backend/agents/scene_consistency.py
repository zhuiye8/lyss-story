"""Phase 4: SceneConsistencyAgent - lightweight per-scene checklist validator."""
from backend.agents.base import BaseAgent
from backend.prompts.scene_consistency import SYSTEM_PROMPT, build_user_prompt


class SceneConsistencyAgent(BaseAgent):
    name = "scene_consistency"

    async def run(
        self,
        scene: dict,
        scene_content: str,
        character_cards_block: str,
        unresolved_threads_block: str = "",
        world_book_block: str = "",
        story_id: str | None = None,
        chapter_num: int | None = None,
    ) -> dict:
        user = build_user_prompt(
            scene=scene,
            scene_content=scene_content,
            character_cards_block=character_cards_block,
            unresolved_threads_block=unresolved_threads_block,
            world_book_block=world_book_block,
        )
        try:
            resp = await self._call_json(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user,
                story_id=story_id,
                chapter_num=chapter_num,
                max_tokens=1500,
                temperature=0.1,
            )
        except Exception:
            # On failure, treat as pass to avoid blocking
            return {"pass": True, "score": 0.5, "failed_items": [], "llm_error": True}

        pass_flag = bool(resp.get("pass", False))
        try:
            score = float(resp.get("score", 0) or 0)
        except Exception:
            score = 0.0
        score = max(0.0, min(1.0, score))

        failed = resp.get("failed_items") or []
        if not isinstance(failed, list):
            failed = []
        cleaned_failed = []
        for item in failed:
            if not isinstance(item, dict):
                continue
            cleaned_failed.append({
                "item": str(item.get("item", "")),
                "severity": str(item.get("severity", "medium")),
                "detail": str(item.get("detail", "")),
                "suggestion": str(item.get("suggestion", "")),
            })

        return {
            "pass": pass_flag,
            "score": score,
            "failed_items": cleaned_failed,
        }

    def format_retry_feedback(self, result: dict) -> str:
        """Format failed items as a single-string feedback for SceneWriter retry."""
        items = result.get("failed_items") or []
        if not items:
            return ""
        lines = ["上次生成存在以下问题，请针对性修正："]
        for i, item in enumerate(items, 1):
            sev = item.get("severity", "medium")
            prefix = "⚠️" if sev == "high" else "·"
            lines.append(
                f"{prefix} [{sev}] {item.get('item', '')}: "
                f"{item.get('detail', '')}"
                f"（建议：{item.get('suggestion', '')}）"
            )
        return "\n".join(lines)
