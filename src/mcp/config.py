"""Load and validate named Streamable HTTP MCP server configuration."""

from dataclasses import dataclass
from pathlib import Path

from src.mcp.helpers import (
    parse_server_entry,
    read_server_entries,
    read_yaml,
    validate_unique_names,
)


@dataclass(frozen=True, slots=True)
class MCPServerConfig:
    """Connection details for one named Streamable HTTP MCP server."""

    name: str
    url: str


def load_mcp_config(path: str | Path) -> tuple[MCPServerConfig, ...]:
    """Load and validate server entries from a YAML file.

    Expected format::

        servers:
          - name: weather
            url: https://weather.example.com/mcp
    """
    config_path = Path(path)
    document = read_yaml(config_path)
    entries = read_server_entries(document, config_path)
    configs = tuple(
        MCPServerConfig(*parse_server_entry(entry, index, config_path))
        for index, entry in enumerate(entries)
    )
    validate_unique_names((config.name for config in configs), config_path)
    return configs
