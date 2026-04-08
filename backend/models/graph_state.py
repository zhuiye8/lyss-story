from typing import TypedDict


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

    # Loaded context
    story_bible: dict
    world_state: dict
    event_history: list[dict]
    character_profiles: list[dict]

    # Stage outputs
    new_events: list[dict]
    plot_structure: dict | None
    camera_decision: dict | None
    chapter_draft: str
    consistency_result: dict | None

    # Control flow
    consistency_pass: bool
    retry_count: int
    max_retries: int
    error_message: str

    # Human-in-the-loop
    human_feedback: str | None
