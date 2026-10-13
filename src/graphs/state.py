"""State shared by the agent graph and its nodes."""

from typing import NotRequired, TypedDict


class AgentState(TypedDict):
    user_id: str
    journey_id: str | list[str]
    selected_subgraphs: NotRequired[list[str]]
    output: NotRequired[str]
