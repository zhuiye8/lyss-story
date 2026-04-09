"""Public read-only API for the reader/preview frontend."""

from fastapi import APIRouter, Depends, HTTPException

from backend.deps import get_json_store, get_sqlite
from backend.storage.json_store import JSONStore
from backend.storage.sqlite_store import SQLiteStore

router = APIRouter()


@router.get("/books")
async def list_books(sqlite: SQLiteStore = Depends(get_sqlite)):
    stories = await sqlite.list_published_stories()
    return [
        {
            "id": s["id"],
            "title": s.get("title", ""),
            "theme": s.get("theme", ""),
            "chapter_count": s.get("published_chapter_count", 0),
            "updated_at": s.get("updated_at", ""),
        }
        for s in stories
    ]


@router.get("/books/{book_id}")
async def get_book(
    book_id: str,
    sqlite: SQLiteStore = Depends(get_sqlite),
    json_store: JSONStore = Depends(get_json_store),
):
    story = await sqlite.get_story(book_id)
    if not story or not story.get("is_published"):
        raise HTTPException(404, "Book not found")

    bible = json_store.load_story_bible(book_id)
    chapters = await sqlite.list_published_chapters(book_id)

    return {
        "id": story["id"],
        "title": story.get("title", ""),
        "theme": story.get("theme", ""),
        "genre": bible.get("genre", "") if bible else "",
        "setting": bible.get("setting", "") if bible else "",
        "characters": [
            {"name": c.get("name", ""), "role": c.get("role", "")}
            for c in (bible.get("characters", []) if bible else [])
        ],
        "chapters": [
            {
                "chapter_num": ch["chapter_num"],
                "title": ch.get("title", ""),
                "pov": ch.get("pov", ""),
                "word_count": ch.get("word_count", 0),
            }
            for ch in chapters
        ],
    }


@router.get("/books/{book_id}/chapters/{chapter_num}")
async def read_chapter(
    book_id: str,
    chapter_num: int,
    sqlite: SQLiteStore = Depends(get_sqlite),
):
    # Verify book is published
    story = await sqlite.get_story(book_id)
    if not story or not story.get("is_published"):
        raise HTTPException(404, "Book not found")

    ch = await sqlite.get_published_chapter(book_id, chapter_num)
    if not ch:
        raise HTTPException(404, "Chapter not found or not published")

    # Get total published chapters for navigation
    all_chapters = await sqlite.list_published_chapters(book_id)
    chapter_nums = [c["chapter_num"] for c in all_chapters]
    current_idx = chapter_nums.index(chapter_num) if chapter_num in chapter_nums else -1

    return {
        "story_id": book_id,
        "story_title": story.get("title", ""),
        "chapter_num": ch["chapter_num"],
        "title": ch.get("title", ""),
        "pov": ch.get("pov", ""),
        "content": ch.get("content", ""),
        "word_count": len(ch.get("content", "")),
        "prev_chapter": chapter_nums[current_idx - 1] if current_idx > 0 else None,
        "next_chapter": chapter_nums[current_idx + 1] if current_idx < len(chapter_nums) - 1 else None,
    }
