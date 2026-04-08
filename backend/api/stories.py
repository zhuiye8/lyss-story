import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from backend.config import Settings
from backend.deps import get_json_store, get_llm, get_settings, get_sqlite, get_vector
from backend.graph.chapter_graph import build_chapter_graph
from backend.graph.init_graph import build_init_graph
from backend.llm.client import LLMClient
from backend.storage.json_store import JSONStore
from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore

router = APIRouter()


class CreateStoryRequest(BaseModel):
    theme: str
    requirements: str = ""


class StoryResponse(BaseModel):
    story_id: str
    title: str
    theme: str
    status: str
    chapter_count: int = 0


async def _run_init(
    story_id: str,
    theme: str,
    requirements: str,
    llm: LLMClient,
    sqlite: SQLiteStore,
    json_store: JSONStore,
):
    """Background task: initialize a story."""
    try:
        graph = build_init_graph(llm)
        compiled = graph.compile()
        result = await compiled.ainvoke({
            "story_id": story_id,
            "user_theme": theme,
            "user_requirements": requirements,
            "story_bible": None,
            "characters": [],
            "initial_world_state": None,
        })

        bible = result.get("story_bible", {})
        characters = result.get("characters", [])
        world_state = result.get("initial_world_state", {})

        # Persist
        json_store.save_story_bible(story_id, bible)
        json_store.save_characters(story_id, characters)
        json_store.save_event_graph(story_id, [])
        await sqlite.save_world_state(story_id, world_state, 0)
        await sqlite.update_story(story_id, title=bible.get("title", ""), status="bible_ready")
    except Exception as e:
        await sqlite.update_story(story_id, status=f"error: {str(e)[:200]}")


async def _run_chapter(
    story_id: str,
    chapter_num: int,
    llm: LLMClient,
    settings: Settings,
    sqlite: SQLiteStore,
    json_store: JSONStore,
    vector: VectorStore,
):
    """Background task: generate one chapter."""
    try:
        await sqlite.update_story(story_id, status="generating")
        graph = build_chapter_graph(llm, sqlite, json_store, vector)
        compiled = graph.compile()

        await compiled.ainvoke({
            "story_id": story_id,
            "chapter_num": chapter_num,
            "story_bible": {},
            "world_state": {},
            "event_history": [],
            "character_profiles": [],
            "new_events": [],
            "plot_structure": None,
            "camera_decision": None,
            "chapter_draft": "",
            "consistency_result": None,
            "consistency_pass": False,
            "retry_count": 0,
            "max_retries": settings.max_consistency_retries,
            "error_message": "",
            "human_feedback": None,
        })

        await sqlite.update_story(story_id, status="bible_ready")
    except Exception as e:
        await sqlite.update_story(story_id, status=f"error: {str(e)[:200]}")


@router.post("", response_model=StoryResponse)
async def create_story(
    req: CreateStoryRequest,
    background: BackgroundTasks,
    llm: LLMClient = Depends(get_llm),
    sqlite: SQLiteStore = Depends(get_sqlite),
    json_store: JSONStore = Depends(get_json_store),
):
    story_id = str(uuid.uuid4())[:8]
    await sqlite.create_story(story_id, "", req.theme)
    background.add_task(_run_init, story_id, req.theme, req.requirements, llm, sqlite, json_store)
    return StoryResponse(
        story_id=story_id,
        title="",
        theme=req.theme,
        status="initializing",
        chapter_count=0,
    )


@router.get("", response_model=list[StoryResponse])
async def list_stories(sqlite: SQLiteStore = Depends(get_sqlite)):
    rows = await sqlite.list_stories()
    result = []
    for r in rows:
        count = await sqlite.get_chapter_count(r["id"])
        result.append(StoryResponse(
            story_id=r["id"],
            title=r.get("title", ""),
            theme=r["theme"],
            status=r["status"],
            chapter_count=count,
        ))
    return result


@router.get("/{story_id}", response_model=StoryResponse)
async def get_story(story_id: str, sqlite: SQLiteStore = Depends(get_sqlite)):
    row = await sqlite.get_story(story_id)
    if not row:
        raise HTTPException(404, "Story not found")
    count = await sqlite.get_chapter_count(story_id)
    return StoryResponse(
        story_id=row["id"],
        title=row.get("title", ""),
        theme=row["theme"],
        status=row["status"],
        chapter_count=count,
    )


@router.get("/{story_id}/bible")
async def get_bible(story_id: str, json_store: JSONStore = Depends(get_json_store)):
    bible = json_store.load_story_bible(story_id)
    if not bible:
        raise HTTPException(404, "Story Bible not found")
    return bible


@router.post("/{story_id}/generate")
async def generate_chapter(
    story_id: str,
    background: BackgroundTasks,
    llm: LLMClient = Depends(get_llm),
    settings: Settings = Depends(get_settings),
    sqlite: SQLiteStore = Depends(get_sqlite),
    json_store: JSONStore = Depends(get_json_store),
    vector: VectorStore = Depends(get_vector),
):
    story = await sqlite.get_story(story_id)
    if not story:
        raise HTTPException(404, "Story not found")
    # Allow retry from error state
    if story["status"] not in ("bible_ready", "completed") and not story["status"].startswith("error"):
        raise HTTPException(400, f"Story is in state '{story['status']}', cannot generate")

    chapter_num = await sqlite.get_chapter_count(story_id) + 1
    background.add_task(
        _run_chapter, story_id, chapter_num, llm, settings, sqlite, json_store, vector
    )
    return {"message": f"Generating chapter {chapter_num}", "chapter_num": chapter_num}
