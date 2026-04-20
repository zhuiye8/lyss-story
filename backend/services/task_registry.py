"""In-memory registry of running generation tasks, keyed by story_id.

Used to support cooperative cancellation. Each story can have at most one
active generation task at a time; starting a new one replaces the prior
entry (which should be done/cancelled by the time the new task starts).
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RunningTask:
    story_id: str
    chapter_num: int
    task: asyncio.Task
    started_at: float = field(default_factory=time.time)
    kind: str = "chapter"  # "chapter" | "init" | "import"


class TaskRegistry:
    def __init__(self):
        self._tasks: dict[str, RunningTask] = {}

    def register(
        self,
        story_id: str,
        chapter_num: int,
        task: asyncio.Task,
        kind: str = "chapter",
    ) -> None:
        # If there's already one running, cancel it first (defensive)
        existing = self._tasks.get(story_id)
        if existing and not existing.task.done():
            logger.warning(
                f"[TaskRegistry] Replacing running task for {story_id} "
                f"(ch{existing.chapter_num}) — cancelling old one"
            )
            existing.task.cancel()
        self._tasks[story_id] = RunningTask(
            story_id=story_id,
            chapter_num=chapter_num,
            task=task,
            started_at=time.time(),
            kind=kind,
        )

    def get(self, story_id: str) -> Optional[RunningTask]:
        return self._tasks.get(story_id)

    def cancel(self, story_id: str) -> bool:
        """Cancel the running task for a story. Returns True if cancelled, False if nothing was running."""
        rt = self._tasks.get(story_id)
        if not rt:
            return False
        if rt.task.done():
            self._tasks.pop(story_id, None)
            return False
        logger.info(f"[TaskRegistry] Cancelling {rt.kind} task for {story_id} ch{rt.chapter_num}")
        rt.task.cancel()
        return True

    def cleanup_done(self) -> int:
        """Remove done tasks from registry. Returns count removed."""
        done_ids = [sid for sid, rt in self._tasks.items() if rt.task.done()]
        for sid in done_ids:
            self._tasks.pop(sid, None)
        return len(done_ids)

    def is_running(self, story_id: str) -> bool:
        rt = self._tasks.get(story_id)
        return bool(rt and not rt.task.done())
