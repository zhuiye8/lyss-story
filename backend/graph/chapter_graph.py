from langgraph.graph import END, START, StateGraph

from backend.llm.client import LLMClient
from backend.memory.chapter_extractor import ChapterExtractor
from backend.memory.layered_memory import LayeredMemory
from backend.models.graph_state import ChapterGraphState
from backend.graph.nodes import create_chapter_nodes
from backend.progress import ProgressStore
from backend.storage.json_store import JSONStore
from backend.storage.sqlite_store import SQLiteStore
from backend.storage.vector_store import VectorStore


def route_after_consistency(state: ChapterGraphState) -> str:
    if state.get("consistency_pass"):
        return "pass"
    if state.get("retry_count", 0) < state.get("max_retries", 3):
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
) -> StateGraph:
    (
        load_context,
        world_advance,
        plot_plan,
        camera_decide,
        load_memories,
        write_chapter,
        consistency_check,
        save_chapter,
        save_with_warning,
        extract_memories,
    ) = create_chapter_nodes(
        llm, sqlite, json_store, vector,
        progress_store, layered_memory, chapter_extractor,
    )

    graph = StateGraph(ChapterGraphState)

    graph.add_node("load_context", load_context)
    graph.add_node("world_advance", world_advance)
    graph.add_node("plot_plan", plot_plan)
    graph.add_node("camera_decide", camera_decide)
    graph.add_node("load_memories", load_memories)
    graph.add_node("write_chapter", write_chapter)
    graph.add_node("consistency_check", consistency_check)
    graph.add_node("save_chapter", save_chapter)
    graph.add_node("save_with_warning", save_with_warning)
    graph.add_node("extract_memories", extract_memories)

    # Pipeline: load → world → plan → camera → memories → write → check → save → extract
    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "world_advance")
    graph.add_edge("world_advance", "plot_plan")
    graph.add_edge("plot_plan", "camera_decide")
    graph.add_edge("camera_decide", "load_memories")
    graph.add_edge("load_memories", "write_chapter")
    graph.add_edge("write_chapter", "consistency_check")

    graph.add_conditional_edges(
        "consistency_check",
        route_after_consistency,
        {
            "pass": "save_chapter",
            "retry": "write_chapter",
            "give_up": "save_with_warning",
        },
    )

    # After save, extract memories
    graph.add_edge("save_chapter", "extract_memories")
    graph.add_edge("save_with_warning", "extract_memories")
    graph.add_edge("extract_memories", END)

    return graph
