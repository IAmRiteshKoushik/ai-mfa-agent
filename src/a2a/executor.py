"""Bridge incoming A2A messages to the checkpointed LangGraph graph."""

import asyncio
from collections.abc import Callable
from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Message, Part, Role
from a2a.utils.errors import InvalidParamsError, UnsupportedOperationError
from google.protobuf import json_format
from langgraph.graph.state import CompiledStateGraph

from src.graphs.journeys import RECOGNIZED_JOURNEY_IDS


class LangGraphExecutor(AgentExecutor):
    def __init__(self, get_graph: Callable[[], CompiledStateGraph]) -> None:
        self.get_graph = get_graph

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        message = context.message
        if message is None or len(message.parts) != 1:
            raise InvalidParamsError(
                message="Exactly one structured MFA journey input is required."
            )
        part = message.parts[0]
        if part.WhichOneof("content") != "data":
            raise InvalidParamsError(
                message="MFA journey input must be a structured data object."
            )
        payload = json_format.MessageToDict(part.data)
        if not isinstance(payload, dict):
            raise InvalidParamsError(message="MFA journey input must be a JSON object.")
        user_id = payload.get("user_id")
        journey_id = payload.get("journey_id")
        if not isinstance(user_id, str) or not user_id.strip():
            raise InvalidParamsError(message="A non-empty string user_id is required.")
        if isinstance(journey_id, str):
            journey_ids = [journey_id]
        elif isinstance(journey_id, list) and all(
            isinstance(value, str) for value in journey_id
        ):
            journey_ids = journey_id
        else:
            raise InvalidParamsError(
                message="journey_id must be a journey name or a list of journey names."
            )
        if not journey_ids or any(not value.strip() for value in journey_ids):
            raise InvalidParamsError(
                message="At least one non-empty journey_id is required."
            )
        unknown = set(journey_ids) - RECOGNIZED_JOURNEY_IDS
        if unknown:
            raise InvalidParamsError(
                message=f"Unknown journey_id: {', '.join(sorted(unknown))}"
            )
        if not context.context_id:
            raise InvalidParamsError(message="A context ID is required.")

        # The Aerospike saver is synchronous. Keep database I/O off the event loop.
        result = await asyncio.to_thread(
            self.get_graph().invoke,
            {"user_id": user_id, "journey_id": journey_ids},
            config={"configurable": {"thread_id": context.context_id}},
        )
        await event_queue.enqueue_event(
            Message(
                message_id=str(uuid4()),
                context_id=context.context_id,
                role=Role.ROLE_AGENT,
                parts=[Part(text=result["output"])],
            )
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise UnsupportedOperationError(
            message="This agent returns immediate messages and does not create tasks."
        )
