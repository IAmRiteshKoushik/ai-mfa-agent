"""Build the checkpointed agent graph."""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from src.graphs.state import AgentState
from src.nodes.placeholder import decide_mfa_journey


def build_graph(checkpointer: BaseCheckpointSaver):
    builder = StateGraph(AgentState)
    builder.add_node("decision", decide_mfa_journey)
    builder.add_edge(START, "decision")
    builder.add_edge("decision", END)
    return builder.compile(checkpointer=checkpointer)
