"""Phase 5: CharacterReviewer - post-chapter dynamic state updater per character."""
from backend.agents.base import BaseAgent
from backend.prompts.character_reviewer import SYSTEM_PROMPT, build_user_prompt


class CharacterReviewerAgent(BaseAgent):
    name = "character_reviewer"

    async def run(
        self,
        character_profile: dict,
        chapter_content: str,
        previous_state: dict | None,
        chapter_num: int,
        story_id: str | None = None,
    ) -> dict:
        user = build_user_prompt(
            character_profile=character_profile,
            chapter_content=chapter_content,
            previous_state=previous_state,
            chapter_num=chapter_num,
        )
        try:
            resp = await self._call_json(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user,
                story_id=story_id,
                chapter_num=chapter_num,
                max_tokens=1500,
                temperature=0.2,
            )
        except Exception:
            return {}
        if not isinstance(resp, dict):
            return {}
        return {
            "location": str(resp.get("location", ""))[:80],
            "emotional_state": str(resp.get("emotional_state", ""))[:120],
            "status": str(resp.get("status", "active")),
            "knowledge_summary": str(resp.get("knowledge_summary", ""))[:400],
            "goals_update": str(resp.get("goals_update", ""))[:200],
            "current_intent": str(resp.get("current_intent", ""))[:120],
            "relationship_updates": resp.get("relationship_updates") or [],
            "voice_drift_warning": str(resp.get("voice_drift_warning", ""))[:300],
        }
