"""Prepare application dependencies and the LangGraph at startup."""

import logging
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

import aerospike
from langgraph.checkpoint.aerospike import AerospikeSaver
from langgraph.graph.state import CompiledStateGraph

from src.config import AppConfig
from src.config.agent_skill import AgentSkillConfig
from src.graphs.agent import build_graph
from src.infra.aerospike import open_aerospike_client
from src.infra.agent_skill import load_agent_skill
from src.mcp import MCPClientManager
from src.mcp.config import MCPServerConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PreparedApplication:
    """Resources that remain available for the application's lifetime."""

    graph: CompiledStateGraph
    mcp: MCPClientManager
    agent_skill: AgentSkillConfig
    a2a_public_url: str


async def _connect_mcp_servers(
    stack: AsyncExitStack,
    servers: tuple[MCPServerConfig, ...],
) -> MCPClientManager:
    mcp = await stack.enter_async_context(MCPClientManager())
    for server in servers:
        await mcp.connect(server)
        logger.info("Connected to MCP server '%s'", server.name)
    logger.info("MCP setup complete (%d server(s))", len(servers))
    return mcp


def _connect_aerospike(
    stack: AsyncExitStack,
    config: AppConfig,
) -> aerospike.Client:
    client = stack.enter_context(open_aerospike_client(config.aerospike))
    logger.info(
        "Connected to Aerospike at %s:%d (environment=%s)",
        config.aerospike.host,
        config.aerospike.port,
        config.aerospike.environment.value,
    )
    return client


def _build_graph(
    client: aerospike.Client,
    config: AppConfig,
) -> CompiledStateGraph:
    checkpointer = AerospikeSaver(client=client, namespace=config.aerospike.namespace)
    graph = build_graph(checkpointer)
    logger.info("LangGraph initialized with Aerospike checkpointer")
    return graph


@asynccontextmanager
async def prepare(env_file: str | Path = ".env") -> AsyncIterator[PreparedApplication]:
    """Load configuration, connect dependencies, and build the agent graph."""
    try:
        config = AppConfig.from_env(env_file)
        logger.info("Loaded environment configuration from %s", env_file)
        async with AsyncExitStack() as stack:
            mcp = await _connect_mcp_servers(stack, config.mcp.load_servers())
            client = _connect_aerospike(stack, config)
            graph = _build_graph(client, config)
            agent_skill = load_agent_skill(client, config.aerospike)
            logger.info("Loaded Agent Card skill '%s' from Aerospike", agent_skill.id)
            yield PreparedApplication(
                graph=graph,
                mcp=mcp,
                agent_skill=agent_skill,
                a2a_public_url=config.a2a_public_url,
            )

    except Exception:
        logger.exception("Application preparation or shutdown failed")
        raise
