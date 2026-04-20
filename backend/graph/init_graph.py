from langgraph.graph import END, START, StateGraph

from backend.llm.client import LLMClient
from backend.memory.world_book import WorldBook
from backend.models.graph_state import InitGraphState
from backend.graph.nodes import create_init_nodes


def build_init_graph(
    llm: LLMClient,
    title: str = "",
    world_book: WorldBook | None = None,
) -> StateGraph:
    (
        concept_node,
        world_build_node,
        character_design_node,
        outline_plan_node,
        assemble_bible_node,
        extract_characters_node,
        init_world_node,
        init_world_book_node,
    ) = create_init_nodes(llm, title=title, world_book=world_book)

    graph = StateGraph(InitGraphState)

    graph.add_node("concept", concept_node)
    graph.add_node("world_build", world_build_node)
    graph.add_node("character_design", character_design_node)
    graph.add_node("outline_plan", outline_plan_node)
    graph.add_node("assemble_bible", assemble_bible_node)
    graph.add_node("extract_characters", extract_characters_node)
    graph.add_node("init_world", init_world_node)
    graph.add_node("init_world_book", init_world_book_node)

    graph.add_edge(START, "concept")
    graph.add_edge("concept", "world_build")
    graph.add_edge("world_build", "character_design")
    graph.add_edge("character_design", "outline_plan")
    graph.add_edge("outline_plan", "assemble_bible")
    graph.add_edge("assemble_bible", "extract_characters")
    graph.add_edge("extract_characters", "init_world")
    graph.add_edge("init_world", "init_world_book")
    graph.add_edge("init_world_book", END)

    return graph
