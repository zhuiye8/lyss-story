"""Phase 4: SceneSplitter agent - aggregate plot beats into scenes."""
from backend.agents.base import BaseAgent
from backend.prompts.scene_splitter import SYSTEM_PROMPT, build_user_prompt


class SceneSplitterAgent(BaseAgent):
    name = "scene_splitter"

    def _default_scene_count(self, target_word_count: int) -> int:
        if target_word_count <= 1500:
            return 2
        if target_word_count <= 2500:
            return 3
        if target_word_count <= 3500:
            return 4
        return 5

    async def run(
        self,
        chapter_num: int,
        plot_structure: dict,
        target_word_count: int,
        character_profiles: list[dict],
        previous_chapter_tail: str = "",
        story_id: str | None = None,
    ) -> list[dict]:
        user = build_user_prompt(
            chapter_num=chapter_num,
            plot_structure=plot_structure or {},
            target_word_count=target_word_count,
            character_profiles=character_profiles or [],
            previous_chapter_tail=previous_chapter_tail,
        )
        resp = await self._call_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user,
            story_id=story_id,
            chapter_num=chapter_num,
            max_tokens=3000,
            temperature=0.4,
        )
        scenes = resp.get("scenes") or []
        if not isinstance(scenes, list):
            return []

        # Sanitize: ensure scene_idx, scene_id, target_words
        cleaned: list[dict] = []
        expected_count = self._default_scene_count(target_word_count)
        per_scene = max(400, target_word_count // max(1, len(scenes) or expected_count))
        for idx, s in enumerate(scenes):
            if not isinstance(s, dict):
                continue
            scene_idx = s.get("scene_idx") or (idx + 1)
            scene_id = s.get("scene_id") or f"ch{chapter_num}_s{scene_idx}"
            target_words = s.get("target_words") or per_scene
            try:
                target_words = int(target_words)
            except Exception:
                target_words = per_scene
            target_words = max(300, min(1500, target_words))

            cleaned.append({
                "scene_idx": scene_idx,
                "scene_id": scene_id,
                "pov_character_id": s.get("pov_character_id") or "",
                "location": s.get("location") or "",
                "characters_present": s.get("characters_present") or [],
                "time_marker": s.get("time_marker") or "",
                "beats": s.get("beats") or [],
                "purpose": s.get("purpose") or "",
                "target_words": target_words,
                "opening_hook": s.get("opening_hook") or "",
                "closing_hook": s.get("closing_hook") or "",
            })

        if not cleaned:
            # Fallback: one synthetic scene covering the whole chapter
            cleaned = [{
                "scene_idx": 1,
                "scene_id": f"ch{chapter_num}_s1",
                "pov_character_id": "",
                "location": "",
                "characters_present": [],
                "time_marker": "",
                "beats": (plot_structure or {}).get("beats", []),
                "purpose": (plot_structure or {}).get("chapter_goal", ""),
                "target_words": target_word_count,
                "opening_hook": "",
                "closing_hook": "",
            }]

        return cleaned
