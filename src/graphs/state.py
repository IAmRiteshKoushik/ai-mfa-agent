"""State shared by the agent graph and its nodes."""

from typing import TypedDict


class AgentState(TypedDict):
    user_id: str
    journey_id: str
    output: str
