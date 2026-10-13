"""Top-level application settings."""

import os
from dataclasses import dataclass
from pathlib import Path

from src.config.aerospike import AerospikeConfig
from src.config.env import load_env_file
from src.config.mcp import McpConfig


@dataclass(frozen=True, slots=True)
class AppConfig:
    aerospike: AerospikeConfig
    mcp: McpConfig
    a2a_public_url: str
    a2a_peer_url: str

    @classmethod
    def from_env(cls, env_file: str | Path = ".env") -> "AppConfig":
        load_env_file(env_file)
        return cls(
            aerospike=AerospikeConfig.from_env(),
            mcp=McpConfig.from_env(),
            a2a_public_url=os.getenv("A2A_PUBLIC_URL", "http://localhost:8000/"),
            a2a_peer_url=os.getenv("A2A_PEER_URL", "http://localhost:8001"),
        )
