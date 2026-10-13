from src.graphs.journeys import RECOGNIZED_JOURNEY_IDS
from src.graphs.state import AgentState


def decision_node(state: AgentState) -> dict[str, list[str]]:
    journey_ids = state["journey_id"]
    selected = [journey_ids] if isinstance(journey_ids, str) else journey_ids
    unknown = set(selected) - RECOGNIZED_JOURNEY_IDS
    if unknown:
        raise ValueError(f"Unknown journey_id: {', '.join(sorted(unknown))}")
    return {"selected_subgraphs": list(dict.fromkeys(selected))}
