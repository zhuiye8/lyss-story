from langgraph.graph import END, START, StateGraph

from backend.llm.client import LLMClient
from backend.memory.chapter_extractor import ChapterExtractor
from backend.memory.context_builder import ContextBuilder
from backend.memory.layered_memory import LayeredMemory
from backend.memory.plot_dedup import PlotDedupStore
from backend.models.graph_state import ChapterGraphState
from backend.graph.nodes import create_chapter_nodes
from backend.progress import ProgressStore
from backend.storage.json_store import JSONStore
from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore


def route_after_consistency(state: ChapterGraphState) -> str:
    if state.get("consistency_pass"):
        return "pass"
    if state.get("retry_count", 0) < state.get("max_retries", 2):
        return "retry"
    return "give_up"


def build_chapter_graph(
    llm: LLMClient,
    sqlite: SQLiteStore,
    json_store: JSONStore,
    vector: VectorStore,
    progress_store: ProgressStore | None = None,
    layered_memory: LayeredMemory | None = None,
    chapter_extractor: ChapterExtractor | None = None,
    plot_dedup: PlotDedupStore | None = None,
    context_builder: ContextBuilder | None = None,
    chapter_consistency_threshold: int = 70,
    chapter_max_critical: int = 0,
    chapter_max_warnings: int = 3,
    scene_consistency_threshold: float = 0.7,
) -> StateGraph:
    (
        load_context,
        world_advance,
        plot_plan,
        camera_decide,
        build_context,
        load_memories,
        scene_split,
        write_scenes,
        assemble_chapter,
        consistency_check,
        save_chapter,
        save_with_warning,
        extract_memories,
    ) = create_chapter_nodes(
        llm, sqlite, json_store, vector,
        progress_store, layered_memory, chapter_extractor,
        plot_dedup, context_builder,
        chapter_consistency_threshold, chapter_max_critical,
        chapter_max_warnings, scene_consistency_threshold,
    )

    graph = StateGraph(ChapterGraphState)

    # Nodes
    graph.add_node("load_context", load_context)
    graph.add_node("world_advance", world_advance)
    graph.add_node("plot_plan", plot_plan)
    graph.add_node("camera_decide", camera_decide)
    graph.add_node("build_context", build_context)
    graph.add_node("load_memories", load_memories)
    graph.add_node("scene_split", scene_split)
    graph.add_node("write_scenes", write_scenes)
    graph.add_node("assemble_chapter", assemble_chapter)
    graph.add_node("consistency_check", consistency_check)
    graph.add_node("save_chapter", save_chapter)
    graph.add_node("save_with_warning", save_with_warning)
    graph.add_node("extract_memories", extract_memories)

    # Pipeline:
    # load → world → plot → camera → build_context → load_memories
    # → scene_split → write_scenes (internal retry loop) → assemble
    # → consistency (chapter-level) → save/retry/give_up → extract
    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "world_advance")
    graph.add_edge("world_advance", "plot_plan")
    graph.add_edge("plot_plan", "camera_decide")
    graph.add_edge("camera_decide", "build_context")
    graph.add_edge("build_context", "load_memories")
    graph.add_edge("load_memories", "scene_split")
    graph.add_edge("scene_split", "write_scenes")
    graph.add_edge("write_scenes", "assemble_chapter")
    graph.add_edge("assemble_chapter", "consistency_check")

    graph.add_conditional_edges(
        "consistency_check",
        route_after_consistency,
        {
            "pass": "save_chapter",
            "retry": "write_scenes",  # re-run scene loop (scenes are already split)
            "give_up": "save_with_warning",
        },
    )

    graph.add_edge("save_chapter", "extract_memories")
    graph.add_edge("save_with_warning", "extract_memories")
    graph.add_edge("extract_memories", END)

    return graph
