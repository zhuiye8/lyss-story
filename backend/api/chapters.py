from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.deps import get_sqlite
from backend.storage.sqlite_store import SQLiteStore

router = APIRouter()


class ChapterSummary(BaseModel):
    chapter_num: int
    title: str
    pov: str
    word_count: int
    has_warnings: bool
    is_published: bool = False


class ChapterDetail(BaseModel):
    story_id: str
    chapter_num: int
    title: str
    pov: str
    content: str
    word_count: int
    events_covered: list[str]
    consistency_warnings: list[str]


@router.get("", response_model=list[ChapterSummary])
async def list_chapters(story_id: str, sqlite: SQLiteStore = Depends(get_sqlite)):
    rows = await sqlite.list_chapters(story_id)
    return [
        ChapterSummary(
            chapter_num=r["chapter_num"],
            title=r.get("title", ""),
            pov=r.get("pov", ""),
            word_count=r.get("word_count", 0),
            has_warnings=r.get("has_warnings", False),
            is_published=bool(r.get("is_published", 0)),
        )
        for r in rows
    ]


@router.get("/{chapter_num}", response_model=ChapterDetail)
async def get_chapter(
    story_id: str, chapter_num: int, sqlite: SQLiteStore = Depends(get_sqlite)
):
    ch = await sqlite.get_chapter(story_id, chapter_num)
    if not ch:
        raise HTTPException(404, "Chapter not found")
    return ChapterDetail(
        story_id=ch["story_id"],
        chapter_num=ch["chapter_num"],
        title=ch.get("title", ""),
        pov=ch.get("pov", ""),
        content=ch.get("content", ""),
        word_count=len(ch.get("content", "")),
        events_covered=ch.get("events_covered", []),
        consistency_warnings=ch.get("metadata", {}).get("consistency_warnings", []),
    )


@router.put("/{chapter_num}/publish")
async def publish_chapter(
    story_id: str,
    chapter_num: int,
    req: dict,
    sqlite: SQLiteStore = Depends(get_sqlite),
):
    ch = await sqlite.get_chapter(story_id, chapter_num)
    if not ch:
        raise HTTPException(404, "Chapter not found")
    publish = bool(req.get("publish", False))
    await sqlite.publish_chapter(story_id, chapter_num, publish)
    return {"message": f"Chapter {chapter_num} {'published' if publish else 'unpublished'}", "is_published": publish}
