from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

import asyncio

from backend.api.stories import _run_chapter
from backend.config import Settings
from backend.deps import (
    get_chapter_extractor, get_context_builder, get_json_store,
    get_knowledge_graph, get_layered_memory, get_llm, get_plot_dedup,
    get_progress_store, get_settings, get_sqlite, get_task_registry, get_vector,
)
from backend.llm.client import LLMClient
from backend.memory.chapter_extractor import ChapterExtractor
from backend.memory.context_builder import ContextBuilder
from backend.memory.knowledge_graph import KnowledgeGraph
from backend.memory.layered_memory import LayeredMemory
from backend.memory.plot_dedup import PlotDedupStore
from backend.services.task_registry import TaskRegistry
from backend.progress import ProgressStore
from backend.services.regeneration import RegenerationPlanner
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
    # Phase 2: cascade options. If chapters_to_invalidate is empty, all downstream are invalidated.
    # If None, no cascade (legacy behaviour). Prefer passing an explicit list from UI.
    chapters_to_invalidate: list[int] | None = None


class AffectedChapterInfo(BaseModel):
    chapter_num: int
    source_version_id: int
    dep_chapters: list[int]
    memory_count: int
    triple_count: int
    state_count: int
    summary_exists: bool
    brief: str


class RegeneratePlanResponse(BaseModel):
    target_chapter: int
    target_current_version_id: int | None
    affected_chapters: list[AffectedChapterInfo]


class ChapterVersionSummary(BaseModel):
    id: int
    version_num: int
    title: str
    pov: str
    word_count: int
    feedback: str
    is_live: bool = False
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


@router.get("/{chapter_num}/regenerate/plan", response_model=RegeneratePlanResponse)
async def regenerate_plan(
    story_id: str,
    chapter_num: int,
    sqlite: SQLiteStore = Depends(get_sqlite),
    vector: VectorStore = Depends(get_vector),
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
):
    """Preview the cascade impact of regenerating a chapter."""
    planner = RegenerationPlanner(sqlite, vector, kg)
    plan = await planner.plan(story_id, chapter_num)
    return RegeneratePlanResponse(
        target_chapter=plan.target_chapter,
        target_current_version_id=plan.target_current_version_id,
        affected_chapters=[
            AffectedChapterInfo(
                chapter_num=a.chapter_num,
                source_version_id=a.source_version_id,
                dep_chapters=a.dep_chapters,
                memory_count=a.memory_count,
                triple_count=a.triple_count,
                state_count=a.state_count,
                summary_exists=a.summary_exists,
                brief=a.brief,
            )
            for a in plan.affected_chapters
        ],
    )


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
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
    progress_store: ProgressStore = Depends(get_progress_store),
    layered_memory: LayeredMemory = Depends(get_layered_memory),
    chapter_extractor: ChapterExtractor = Depends(get_chapter_extractor),
    plot_dedup: PlotDedupStore = Depends(get_plot_dedup),
    context_builder: ContextBuilder = Depends(get_context_builder),
    task_registry: TaskRegistry = Depends(get_task_registry),
):
    """Regenerate a chapter with optional human feedback + cascade control.

    Steps:
    1. Snapshot the current live version (so the regen itself is reversible)
    2. Deactivate the old version's memories (so downstream context won't see old facts)
    3. Optionally cascade-invalidate downstream chapters' memories per UI selection
    4. Run the chapter pipeline → produces a new is_live=1 version
    """
    story = await sqlite.get_story(story_id)
    if not story:
        raise HTTPException(404, "Story not found")
    if story["status"] not in ("bible_ready", "completed") and not story["status"].startswith("error"):
        raise HTTPException(400, f"Story is in state '{story['status']}', cannot regenerate")

    current = await sqlite.get_chapter(story_id, chapter_num)
    if not current:
        raise HTTPException(404, "Chapter not found")

    # 1. Snapshot current live version (without flipping it, so we have a pointer before demotion)
    old_version_id = await sqlite.get_live_version_id(story_id, chapter_num)
    if old_version_id is None:
        # Defensive: create a snapshot now
        old_version_id = await sqlite.snapshot_only_version(
            story_id=story_id,
            chapter_num=chapter_num,
            title=current.get("title", ""),
            pov=current.get("pov", ""),
            content=current.get("content", ""),
            events=current.get("events_covered", []),
            metadata=current.get("metadata", {}),
            feedback=req.feedback or "",
        )
    else:
        # Add a feedback-tagged snapshot copy so the regen itself is reviewable
        await sqlite.snapshot_only_version(
            story_id=story_id,
            chapter_num=chapter_num,
            title=current.get("title", ""),
            pov=current.get("pov", ""),
            content=current.get("content", ""),
            events=current.get("events_covered", []),
            metadata=current.get("metadata", {}),
            feedback=f"[pre-regen snapshot] {req.feedback or ''}".strip(),
        )

    # 2. Deactivate old version's memories
    planner = RegenerationPlanner(sqlite, vector, kg)
    await planner.invalidate_old_live_memories(story_id, chapter_num, old_version_id)

    # 3. Cascade invalidation per UI selection
    if req.chapters_to_invalidate is not None:
        await planner.apply_invalidation(
            story_id, chapter_num, req.chapters_to_invalidate
        )

    if task_registry.is_running(story_id):
        raise HTTPException(409, "该小说已有生成任务在运行，请先停止再重新生成")

    # 4. Kick off pipeline as a tracked asyncio task
    task = asyncio.create_task(
        _run_chapter(
            story_id, chapter_num, llm, settings, sqlite, json_store, vector,
            progress_store, layered_memory, chapter_extractor, req.feedback or None,
            plot_dedup, None, context_builder,
        )
    )
    task_registry.register(story_id, chapter_num, task, kind="chapter")
    return {
        "message": f"Regenerating chapter {chapter_num}",
        "chapter_num": chapter_num,
        "cascade_invalidated": req.chapters_to_invalidate or [],
    }


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
            is_live=bool(r.get("is_live", 0)),
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
    vector: VectorStore = Depends(get_vector),
    kg: KnowledgeGraph = Depends(get_knowledge_graph),
):
    """Restore an older version as live.

    Also toggles memory activation: deactivate current live's memories,
    reactivate the restored version's memories.
    """
    target = await sqlite.get_chapter_version(version_id)
    if not target or target["story_id"] != story_id or target["chapter_num"] != chapter_num:
        raise HTTPException(404, "Version not found")

    planner = RegenerationPlanner(sqlite, vector, kg)
    # Deactivate current live
    current_live_id = await sqlite.get_live_version_id(story_id, chapter_num)
    if current_live_id is not None and current_live_id != version_id:
        await planner.cascade_invalidate(story_id, chapter_num, current_live_id, active=False)

    # Flip live + update chapters materialized view
    restored = await sqlite.restore_chapter_version(version_id)
    if not restored:
        raise HTTPException(404, "Restore failed")

    # Reactivate restored version's memories
    await planner.reactivate_version(story_id, chapter_num, version_id)

    return {
        "message": f"Chapter {chapter_num} restored to version {restored['version_num']}",
        "version_num": restored["version_num"],
    }
