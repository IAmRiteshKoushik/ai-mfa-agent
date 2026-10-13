"""Make the current deterministic MFA journey decision."""

import logging

from src.graphs.state import AgentState

logger = logging.getLogger(__name__)


def decide_mfa_journey(state: AgentState) -> dict[str, str]:
    user_id = state["user_id"]
    journey_id = state["journey_id"]
    logger.info(
        "Received MFA journey for user_id=%s journey_id=%s", user_id, journey_id
    )
    return {
        "output": f"MFA journey accepted for user {user_id} using journey {journey_id}."
    }
