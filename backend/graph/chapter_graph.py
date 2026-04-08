from langgraph.graph import END, START, StateGraph

from backend.llm.client import LLMClient
from backend.models.graph_state import ChapterGraphState
from backend.graph.nodes import create_chapter_nodes
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
) -> StateGraph:
    (
        load_context,
        world_advance,
        plot_plan,
        camera_decide,
        write_chapter,
        consistency_check,
        save_chapter,
        save_with_warning,
    ) = create_chapter_nodes(llm, sqlite, json_store, vector)

    graph = StateGraph(ChapterGraphState)

    graph.add_node("load_context", load_context)
    graph.add_node("world_advance", world_advance)
    graph.add_node("plot_plan", plot_plan)
    graph.add_node("camera_decide", camera_decide)
    graph.add_node("write_chapter", write_chapter)
    graph.add_node("consistency_check", consistency_check)
    graph.add_node("save_chapter", save_chapter)
    graph.add_node("save_with_warning", save_with_warning)

    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "world_advance")
    graph.add_edge("world_advance", "plot_plan")
    graph.add_edge("plot_plan", "camera_decide")
    graph.add_edge("camera_decide", "write_chapter")
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

    graph.add_edge("save_chapter", END)
    graph.add_edge("save_with_warning", END)

    return graph
