from typing import Annotated, TypedDict
import operator


def replace(a, b):
    """Always use the new value, ignore the old."""
    return b


class InitGraphState(TypedDict):
    story_id: str
    user_theme: str
    user_requirements: str
    story_bible: dict | None
    characters: list[dict]
    initial_world_state: dict | None


class ChapterGraphState(TypedDict):
    story_id: str
    chapter_num: int

    # Loaded context (replace on update)
    story_bible: Annotated[dict, replace]
    world_state: Annotated[dict, replace]
    event_history: Annotated[list[dict], replace]
    character_profiles: Annotated[list[dict], replace]

    # Stage outputs (replace on update)
    new_events: Annotated[list[dict], replace]
    plot_structure: Annotated[dict | None, replace]
    camera_decision: Annotated[dict | None, replace]
    chapter_draft: Annotated[str, replace]
    consistency_result: Annotated[dict | None, replace]

    # Control flow
    consistency_pass: Annotated[bool, replace]
    retry_count: Annotated[int, replace]
    max_retries: int
    error_message: Annotated[str, replace]

    # Human-in-the-loop
    human_feedback: str | None
