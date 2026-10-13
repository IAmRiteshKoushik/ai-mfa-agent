"""Build the checkpointed MFA journey graph."""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from src.graphs.journeys import RECOGNIZED_JOURNEY_IDS
from src.graphs.state import AgentState
from src.nodes.initial import initial_node
from src.nodes.decision import decision_node
from src.nodes.end import end_node
from src.nodes.subgraph_mpin import subgraph_mpin
from src.nodes.subgraph_nb_password import subgraph_nb_password
from src.nodes.subgraph_otp import subgraph_otp
from src.nodes.subgraph_split_otp import subgraph_split_otp

JOURNEY_NODES = {
    "subgraph_otp": subgraph_otp,
    "subgraph_mpin": subgraph_mpin,
    "subgraph_split_otp": subgraph_split_otp,
    "subgraph_nb_password": subgraph_nb_password,
}


def route_journey(state: AgentState) -> list[str]:
    """Return the subgraphs selected by the decision node."""
    return state["selected_subgraphs"]


def build_graph(checkpointer: BaseCheckpointSaver):
    builder = StateGraph(AgentState)
    builder.add_node("initial", initial_node)
    builder.add_node("decision", decision_node)
    builder.add_node("end_node", end_node)
    for name, node in JOURNEY_NODES.items():
        builder.add_node(name, node)
        builder.add_edge(name, "end_node")

    builder.add_edge(START, "initial")
    builder.add_edge("initial", "decision")
    builder.add_conditional_edges(
        "decision", route_journey, {name: name for name in JOURNEY_NODES}
    )
    builder.add_edge("end_node", END)
    return builder.compile(checkpointer=checkpointer)
