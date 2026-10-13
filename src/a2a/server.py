"""ASGI application factory for the A2A service."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from starlette.applications import Starlette

from src.a2a.agent_card import build_agent_card
from src.a2a.executor import LangGraphExecutor
from src.prepare import prepare


def create_app() -> Starlette:
    @asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with prepare() as prepared:
            app.state.graph = prepared.graph
            app.state.mcp = prepared.mcp
            try:
                yield
            finally:
                del app.state.graph
                del app.state.mcp

    app = Starlette(lifespan=lifespan)
    card = build_agent_card()
    handler = DefaultRequestHandler(
        agent_executor=LangGraphExecutor(lambda: app.state.graph),
        task_store=InMemoryTaskStore(),
        agent_card=card,
        validate_input_modes=True,
    )
    app.routes.extend(create_agent_card_routes(card))
    app.routes.extend(create_jsonrpc_routes(handler, "/"))
    return app
