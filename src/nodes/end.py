import logging

from src.graphs.state import AgentState

logger = logging.getLogger(__name__)


def end_node(state: AgentState) -> dict[str, str]:
    message = "MFA journey completed"
    logger.info(message)
    return {"output": message}
