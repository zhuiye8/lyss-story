from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.deps import get_progress_store, get_sqlite
from backend.progress import ProgressStore
from backend.storage.sqlite_store import SQLiteStore

router = APIRouter()


class GenerationStatusResponse(BaseModel):
    story_id: str
    status: str
    current_chapter: int | None = None
    error_message: str | None = None


@router.get("/status", response_model=GenerationStatusResponse)
async def get_status(story_id: str, sqlite: SQLiteStore = Depends(get_sqlite)):
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
