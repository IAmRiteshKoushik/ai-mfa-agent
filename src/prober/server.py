"""A controllable A2A peer for exercising client and task behavior."""

import asyncio
import os
from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Message,
    Part,
    Role,
    Task,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from starlette.applications import Starlette


class ProbeExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        text = context.get_user_input()
        command = text.strip().lower()

        if command.startswith("timeout"):
            seconds = float(os.getenv("PROBE_TIMEOUT_SECONDS", "60"))
            await asyncio.sleep(seconds)
            text = f"Timeout probe finished after {seconds:g} seconds."
        elif command == "error":
            raise RuntimeError("Probe agent requested an intentional task failure.")
        elif command == "task":
            task_id = context.task_id or str(uuid4())
            context_id = context.context_id or str(uuid4())
            await event_queue.enqueue_event(
                Task(
                    id=task_id,
                    context_id=context_id,
                    status=TaskStatus(state=TaskState.TASK_STATE_SUBMITTED),
                )
            )
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task_id,
                    context_id=context_id,
                    status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
                )
            )
            await asyncio.sleep(0.25)
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task_id,
                    context_id=context_id,
                    status=TaskStatus(
                        state=TaskState.TASK_STATE_COMPLETED,
                        message=Message(
                            message_id=str(uuid4()),
                            context_id=context_id,
                            task_id=task_id,
                            role=Role.ROLE_AGENT,
                            parts=[Part(text="Probe task completed.")],
                        ),
                    ),
                )
            )
            return
        else:
            text = f"Probe received: {text}"

        await event_queue.enqueue_event(
            Message(
                message_id=str(uuid4()),
                context_id=context.context_id,
                role=Role.ROLE_AGENT,
                parts=[Part(text=text)],
            )
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.task_id and context.context_id:
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=context.task_id,
                    context_id=context.context_id,
                    status=TaskStatus(state=TaskState.TASK_STATE_CANCELED),
                )
            )


def create_probe_app() -> Starlette:
    url = os.getenv("PROBE_PUBLIC_URL", "http://localhost:8001/")
    card = AgentCard(
        name="probe-agent",
        description="A controllable A2A peer for communication, task, error, and timeout probes.",
        version="0.1.0",
        supported_interfaces=[
            AgentInterface(url=url, protocol_binding="JSONRPC", protocol_version="1.0")
        ],
        capabilities=AgentCapabilities(streaming=False, push_notifications=False),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="probe",
                name="A2A probe",
                description="Send text, task, error, or timeout to exercise A2A behavior.",
                tags=["probe", "testing"],
                examples=["hello", "task", "error", "timeout"],
            )
        ],
    )
    handler = DefaultRequestHandler(
        agent_executor=ProbeExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=card,
        validate_input_modes=True,
    )
    app = Starlette()
    app.routes.extend(create_agent_card_routes(card))
    app.routes.extend(create_jsonrpc_routes(handler, "/"))
    return app


app = create_probe_app()


def main() -> None:
    import uvicorn

    uvicorn.run(
        "src.prober.server:app",
        host=os.getenv("PROBE_HOST", "127.0.0.1"),
        port=int(os.getenv("PROBE_PORT", "8001")),
    )
