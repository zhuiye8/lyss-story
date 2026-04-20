"""Phase 4: SceneWriter agent - generates a single scene."""
from backend.agents.base import BaseAgent
from backend.prompts.scene_writer import SYSTEM_PROMPT, build_user_prompt


class SceneWriterAgent(BaseAgent):
    name = "scene_writer"

    async def run(
        self,
        scene: dict,
        chapter_num: int,
        context_block: str,
        previous_scene_tail: str = "",
        human_feedback: str = "",
        story_id: str | None = None,
    ) -> str:
        user = build_user_prompt(
            scene=scene,
            chapter_num=chapter_num,
            context_block=context_block,
            previous_scene_tail=previous_scene_tail,
            human_feedback=human_feedback,
        )
        # target_words is char-count in Chinese context.
        # Chinese text ≈ 1.5 tokens/char. Use 1.7× as a hard ceiling —
        # this is the only real control over output length (prompt alone won't work).
        target_words = scene.get("target_words", 800)
        max_tokens = max(800, int(target_words * 1.7))
        text = await self._call_text(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user,
            story_id=story_id,
            chapter_num=chapter_num,
            max_tokens=max_tokens,
            temperature=0.75,
        )
        return (text or "").strip()
