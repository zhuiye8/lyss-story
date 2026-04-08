from langgraph.graph import END, START, StateGraph

from backend.llm.client import LLMClient
from backend.models.graph_state import InitGraphState
from backend.graph.nodes import create_init_nodes


def build_init_graph(llm: LLMClient) -> StateGraph:
    generate_bible, extract_characters, init_world = create_init_nodes(llm)

    graph = StateGraph(InitGraphState)
    graph.add_node("generate_bible", generate_bible)
    graph.add_node("extract_characters", extract_characters)
    graph.add_node("init_world", init_world)

    graph.add_edge(START, "generate_bible")
    graph.add_edge("generate_bible", "extract_characters")
    graph.add_edge("extract_characters", "init_world")
    graph.add_edge("init_world", END)

    return graph
