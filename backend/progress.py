"""In-memory progress tracker for chapter generation pipeline."""

import time
from dataclasses import dataclass, field


@dataclass
class StageInfo:
    name: str
    label: str
    started_at: float = 0.0
    finished_at: float = 0.0
    status: str = "pending"  # pending / running / done / error
    detail: str = ""


@dataclass
class GenerationProgress:
    story_id: str
    chapter_num: int = 0
    started_at: float = field(default_factory=time.time)
    stages: list[StageInfo] = field(default_factory=list)
    current_stage_index: int = -1
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "story_id": self.story_id,
            "chapter_num": self.chapter_num,
            "elapsed_seconds": round(time.time() - self.started_at, 1),
            "current_stage": self.stages[self.current_stage_index].name if 0 <= self.current_stage_index < len(self.stages) else None,
            "current_stage_label": self.stages[self.current_stage_index].label if 0 <= self.current_stage_index < len(self.stages) else None,
            "error": self.error,
            "stages": [
                {
                    "name": s.name,
                    "label": s.label,
                    "status": s.status,
                    "detail": s.detail,
                    "duration_ms": int((s.finished_at - s.started_at) * 1000) if s.finished_at and s.started_at else 0,
                }
                for s in self.stages
            ],
        }


# Default pipeline stages (matches chapter_graph in backend/graph/chapter_graph.py)
CHAPTER_STAGES = [
    ("load_context", "加载上下文"),
    ("world_advance", "推进世界"),
    ("plot_plan", "规划剧情"),
    ("camera_decide", "选择视角"),
    ("build_context", "组装上下文"),
    ("load_memories", "加载记忆"),
    ("scene_split", "拆分场景"),
    ("write_scenes", "撰写场景"),
    ("consistency_check", "一致性检查"),
    ("save_chapter", "保存章节"),
    ("extract_memories", "提取记忆"),
]


class ProgressStore:
    """Thread-safe in-memory store for generation progress."""

    def __init__(self):
        self._progress: dict[str, GenerationProgress] = {}

    def start(self, story_id: str, chapter_num: int) -> GenerationProgress:
        progress = GenerationProgress(
            story_id=story_id,
            chapter_num=chapter_num,
            stages=[StageInfo(name=name, label=label) for name, label in CHAPTER_STAGES],
        )
        self._progress[story_id] = progress
        return progress

    def enter_stage(self, story_id: str, stage_name: str, detail: str = "") -> None:
        progress = self._progress.get(story_id)
        if not progress:
            return
        for i, stage in enumerate(progress.stages):
            if stage.name == stage_name:
                stage.status = "running"
                stage.started_at = time.time()
                stage.detail = detail
                progress.current_stage_index = i
                break

    def finish_stage(self, story_id: str, stage_name: str, detail: str = "") -> None:
        progress = self._progress.get(story_id)
        if not progress:
            return
        for stage in progress.stages:
            if stage.name == stage_name:
                stage.status = "done"
                stage.finished_at = time.time()
                if detail:
                    stage.detail = detail
                break

    def set_error(self, story_id: str, error: str) -> None:
        progress = self._progress.get(story_id)
        if not progress:
            return
        progress.error = error
        if 0 <= progress.current_stage_index < len(progress.stages):
            progress.stages[progress.current_stage_index].status = "error"

    def get(self, story_id: str) -> dict | None:
        progress = self._progress.get(story_id)
        return progress.to_dict() if progress else None

    def clear(self, story_id: str) -> None:
        self._progress.pop(story_id, None)
