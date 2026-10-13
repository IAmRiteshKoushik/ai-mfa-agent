from src.graphs.journeys import JOURNEY_SUBGRAPHS
from src.graphs.state import AgentState


def decision_node(state: AgentState) -> dict[str, list[str]]:
    journey_id = state["journey_id"]
    try:
        subgraphs = JOURNEY_SUBGRAPHS[journey_id]
    except KeyError as exc:
        raise ValueError(f"Unknown journey_id: {journey_id}") from exc
    return {"selected_subgraphs": list(dict.fromkeys(subgraphs))}
