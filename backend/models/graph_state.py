from typing import Annotated, TypedDict
import operator


def replace(a, b):
    """Always use the new value, ignore the old."""
    return b


class InitGraphState(TypedDict):
    story_id: str
    user_theme: str
    user_requirements: str

    # Intermediate products (filled step by step)
    concept: dict | None              # step 1: ConceptAgent output
    world_setting: dict | None        # step 2: WorldBuilderAgent output
    characters_design: dict | None    # step 3: CharacterDesigner output
    outline: dict | None              # step 4: OutlinePlannerAgent output

    # Final products
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
    storylines: Annotated[list[dict], replace]
    plot_structure: Annotated[dict | None, replace]
    camera_decision: Annotated[dict | None, replace]
    chapter_draft: Annotated[str, replace]
    consistency_result: Annotated[dict | None, replace]

    # Memory context (loaded before writing)
    memory_contexts: Annotated[dict, replace]
    context_bundle: Annotated[dict, replace]   # Phase 3: structured context sections
    upstream_dependencies: Annotated[list[dict], replace]  # Phase 2: chapter deps recorded this run

    # Phase 4: scene-level generation
    scenes: Annotated[list[dict], replace]           # SceneSplitter output
    current_scene_idx: Annotated[int, replace]
    scene_contents: Annotated[list[str], replace]    # finished scene text in order
    scene_retry_count: Annotated[dict, replace]      # {scene_idx: count}
    scene_consistency_results: Annotated[list[dict], replace]
    scene_context_bundle: Annotated[dict, replace]   # per-scene context for the writer

    # Phase 1: version id of the currently-being-generated chapter
    current_version_id: Annotated[int, replace]

    # Generation parameters
    target_word_count: int

    # Control flow
    consistency_pass: Annotated[bool, replace]
    retry_count: Annotated[int, replace]
    max_retries: int
    error_message: Annotated[str, replace]

    # Human-in-the-loop
    human_feedback: str | None
