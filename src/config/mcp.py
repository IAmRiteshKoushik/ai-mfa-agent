"""MCP server configuration source and parsed server definitions."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.mcp.config import MCPServerConfig


@dataclass(frozen=True, slots=True)
class McpConfig:
    config_path: Path = Path("src/mcp/servers.yaml")

    @classmethod
    def from_env(cls) -> "McpConfig":
        return cls(
            config_path=Path(os.getenv("MCP_CONFIG_PATH", "src/mcp/servers.yaml"))
        )

    def load_servers(self) -> tuple["MCPServerConfig", ...]:
        from src.mcp.config import load_mcp_config

        return load_mcp_config(self.config_path)
