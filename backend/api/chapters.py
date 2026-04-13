from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from backend.api.stories import _run_chapter
from backend.config import Settings
from backend.deps import (
    get_chapter_extractor, get_json_store, get_layered_memory, get_llm,
    get_plot_dedup, get_progress_store, get_settings, get_sqlite, get_vector,
)
from backend.llm.client import LLMClient
from backend.memory.chapter_extractor import ChapterExtractor
from backend.memory.layered_memory import LayeredMemory
from backend.memory.plot_dedup import PlotDedupStore
from backend.progress import ProgressStore
from backend.storage.json_store import JSONStore
from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore

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


class RegenerateRequest(BaseModel):
    feedback: str = ""


class ChapterVersionSummary(BaseModel):
    id: int
    version_num: int
    title: str
    pov: str
    word_count: int
    feedback: str
    created_at: str


class ChapterVersionDetail(BaseModel):
    id: int
    story_id: str
    chapter_num: int
    version_num: int
    title: str
    pov: str
    content: str
    word_count: int
    feedback: str
    created_at: str


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


@router.post("/{chapter_num}/regenerate")
async def regenerate_chapter(
    story_id: str,
    chapter_num: int,
    req: RegenerateRequest,
    background: BackgroundTasks,
    llm: LLMClient = Depends(get_llm),
    settings: Settings = Depends(get_settings),
    sqlite: SQLiteStore = Depends(get_sqlite),
    json_store: JSONStore = Depends(get_json_store),
    vector: VectorStore = Depends(get_vector),
    progress_store: ProgressStore = Depends(get_progress_store),
    layered_memory: LayeredMemory = Depends(get_layered_memory),
    chapter_extractor: ChapterExtractor = Depends(get_chapter_extractor),
    plot_dedup: PlotDedupStore = Depends(get_plot_dedup),
):
    """Regenerate a chapter with optional human feedback.

    The existing live chapter is snapshotted into chapter_versions first,
    then the pipeline is re-run to produce a new version that overwrites
    the live chapter.
    """
    story = await sqlite.get_story(story_id)
    if not story:
        raise HTTPException(404, "Story not found")
    if story["status"] not in ("bible_ready", "completed") and not story["status"].startswith("error"):
        raise HTTPException(400, f"Story is in state '{story['status']}', cannot regenerate")

    current = await sqlite.get_chapter(story_id, chapter_num)
    if not current:
        raise HTTPException(404, "Chapter not found")

    # Snapshot current version before regenerating
    await sqlite.save_chapter_version(
        story_id=story_id,
        chapter_num=chapter_num,
        title=current.get("title", ""),
        pov=current.get("pov", ""),
        content=current.get("content", ""),
        events=current.get("events_covered", []),
        metadata=current.get("metadata", {}),
        feedback=req.feedback,
    )

    background.add_task(
        _run_chapter, story_id, chapter_num, llm, settings, sqlite, json_store, vector,
        progress_store, layered_memory, chapter_extractor, req.feedback or None,
        plot_dedup,
    )
    return {"message": f"Regenerating chapter {chapter_num}", "chapter_num": chapter_num}


@router.get("/{chapter_num}/versions", response_model=list[ChapterVersionSummary])
async def list_versions(
    story_id: str,
    chapter_num: int,
    sqlite: SQLiteStore = Depends(get_sqlite),
):
    rows = await sqlite.list_chapter_versions(story_id, chapter_num)
    return [
        ChapterVersionSummary(
            id=r["id"],
            version_num=r["version_num"],
            title=r.get("title", ""),
            pov=r.get("pov", ""),
            word_count=r.get("word_count", 0),
            feedback=r.get("feedback", ""),
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.get("/{chapter_num}/versions/{version_id}", response_model=ChapterVersionDetail)
async def get_version(
    story_id: str,
    chapter_num: int,
    version_id: int,
    sqlite: SQLiteStore = Depends(get_sqlite),
):
    v = await sqlite.get_chapter_version(version_id)
    if not v or v["story_id"] != story_id or v["chapter_num"] != chapter_num:
        raise HTTPException(404, "Version not found")
    return ChapterVersionDetail(
        id=v["id"],
        story_id=v["story_id"],
        chapter_num=v["chapter_num"],
        version_num=v["version_num"],
        title=v.get("title", ""),
        pov=v.get("pov", ""),
        content=v.get("content", ""),
        word_count=len(v.get("content", "")),
        feedback=v.get("feedback", ""),
        created_at=v["created_at"],
    )


@router.post("/{chapter_num}/restore/{version_id}")
async def restore_version(
    story_id: str,
    chapter_num: int,
    version_id: int,
    sqlite: SQLiteStore = Depends(get_sqlite),
):
    restored = await sqlite.restore_chapter_version(version_id)
    if not restored or restored["story_id"] != story_id or restored["chapter_num"] != chapter_num:
        raise HTTPException(404, "Version not found")
    return {
        "message": f"Chapter {chapter_num} restored to version {restored['version_num']}",
        "version_num": restored["version_num"],
    }
