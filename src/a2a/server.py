"""ASGI application factory for the A2A service."""

import os
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
            card = build_agent_card(prepared.a2a_public_url, prepared.agent_skill)
            handler = DefaultRequestHandler(
                agent_executor=LangGraphExecutor(lambda: app.state.graph),
                task_store=InMemoryTaskStore(),
                agent_card=card,
                validate_input_modes=True,
            )
            app.state.graph = prepared.graph
            app.state.mcp = prepared.mcp
            app.state.agent_card = card
            app.state.request_handler = handler
            runtime_routes = [
                *create_agent_card_routes(card),
                *create_jsonrpc_routes(handler, "/"),
            ]
            app.routes.extend(runtime_routes)
            try:
                yield
            finally:
                app.routes = [
                    route for route in app.routes if route not in runtime_routes
                ]
                del app.state.graph
                del app.state.mcp
                del app.state.agent_card
                del app.state.request_handler

    app = Starlette(lifespan=lifespan)
    return app


def main() -> None:
    import uvicorn

    uvicorn.run(
        "src.a2a.server:create_app",
        factory=True,
        host=os.getenv("A2A_HOST", "0.0.0.0"),
        port=int(os.getenv("A2A_PORT", "8000")),
    )
