"""Manage named connections to one or more MCP servers."""

from collections.abc import Iterable, Mapping
from contextlib import AsyncExitStack
from pathlib import Path
from types import MappingProxyType
from typing import Self

from mcp import Client
from src.config import AppConfig
from src.mcp.config import MCPServerConfig, load_mcp_config


class MCPClientManager:
    """Own the lifecycle of multiple named MCP client sessions.

    Use as an async context manager so every connection is closed when the
    manager exits. Nodes can receive this manager and select a server by name.
    """

    def __init__(self) -> None:
        self._stack: AsyncExitStack | None = None
        self._clients: dict[str, Client] = {}

    async def __aenter__(self) -> Self:
        if self._stack is not None:
            raise RuntimeError("MCPClientManager is already open")
        self._stack = AsyncExitStack()
        await self._stack.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> bool | None:
        if self._stack is None:
            return None
        stack, self._stack = self._stack, None
        self._clients.clear()
        return await stack.__aexit__(exc_type, exc, traceback)

    @property
    def clients(self) -> Mapping[str, Client]:
        """Connected clients, indexed by their configured names."""
        return MappingProxyType(self._clients)

    def get(self, name: str) -> Client:
        """Return a connected client or raise ``KeyError`` for an unknown name."""
        if self._stack is None:
            raise RuntimeError("MCPClientManager must be used inside 'async with'")
        return self._clients[name]

    async def connect(self, config: MCPServerConfig) -> Client:
        """Connect to one server and register its client by name."""
        if self._stack is None:
            raise RuntimeError("MCPClientManager must be used inside 'async with'")
        if config.name in self._clients:
            raise ValueError(
                f"An MCP server named {config.name!r} is already connected"
            )

        client = await self._stack.enter_async_context(Client(config.url))
        self._clients[config.name] = client
        return client

    async def connect_all(
        self, configs: Iterable[MCPServerConfig]
    ) -> Mapping[str, Client]:
        """Connect to each configured server, closing all if any connection fails."""
        if self._stack is None:
            raise RuntimeError("MCPClientManager must be used inside 'async with'")

        try:
            for config in configs:
                await self.connect(config)
        except BaseException:
            # A partially connected set is rarely useful to graph nodes.
            await self.__aexit__(None, None, None)
            raise
        return self.clients

    async def connect_from_yaml(
        self, path: str | Path | None = None
    ) -> Mapping[str, Client]:
        """Load server definitions and connect to them.

        If ``path`` is omitted, read it from the centralized MCP config.
        """
        if path is None:
            path = AppConfig.from_env().mcp.config_path
        return await self.connect_all(load_mcp_config(path))
