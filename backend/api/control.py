from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.deps import get_progress_store, get_sqlite, get_task_registry
from backend.progress import ProgressStore
from backend.services.task_registry import TaskRegistry
from backend.storage.sqlite_store import SQLiteStore

router = APIRouter()


class GenerationStatusResponse(BaseModel):
    story_id: str
    status: str
    current_chapter: int | None = None
    error_message: str | None = None
    is_task_running: bool = False


@router.get("/status", response_model=GenerationStatusResponse)
async def get_status(
    story_id: str,
    sqlite: SQLiteStore = Depends(get_sqlite),
    task_registry: TaskRegistry = Depends(get_task_registry),
):
    story = await sqlite.get_story(story_id)
    if not story:
        raise HTTPException(404, "Story not found")

    chapter_count = await sqlite.get_chapter_count(story_id)
    status = story["status"]
    error_msg = None
    if status.startswith("error:"):
        error_msg = status[6:].strip()
        status = "error"

    return GenerationStatusResponse(
        story_id=story_id,
        status=status,
        current_chapter=chapter_count + 1 if status == "generating" else chapter_count,
        error_message=error_msg,
        is_task_running=task_registry.is_running(story_id),
    )


@router.get("/progress")
async def get_progress(
    story_id: str,
    progress_store: ProgressStore = Depends(get_progress_store),
):
    progress = progress_store.get(story_id)
    if not progress:
        return {"story_id": story_id, "stages": [], "current_stage": None}
    return progress


@router.post("/cancel")
async def cancel_generation(
    story_id: str,
    sqlite: SQLiteStore = Depends(get_sqlite),
    task_registry: TaskRegistry = Depends(get_task_registry),
    progress_store: ProgressStore = Depends(get_progress_store),
):
    """Request cancellation of the running generation task for a story.

    If no task is running, the story status is still reset to a
    recoverable state (bible_ready) so the UI unblocks.
    """
    story = await sqlite.get_story(story_id)
    if not story:
        raise HTTPException(404, "Story not found")

    cancelled = task_registry.cancel(story_id)

    # Force status reset so the UI doesn't stay stuck on "generating"
    current_status = story["status"]
    if current_status in ("generating", "initializing") or current_status.startswith("error"):
        await sqlite.update_story(story_id, status="bible_ready")

    if progress_store:
        progress_store.set_error(story_id, "用户已停止")

    return {
        "story_id": story_id,
        "cancelled": cancelled,
        "message": "已停止生成" if cancelled else "没有正在运行的任务，已重置状态",
    }
