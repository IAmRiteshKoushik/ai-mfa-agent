"""Aerospike connection settings."""

import os
from dataclasses import dataclass
from enum import StrEnum


class Environment(StrEnum):
    """Deployment environments supported by the application."""

    LOCAL = "local"
    DEV = "dev"
    SIT = "sit"
    PROD = "prod"


@dataclass(frozen=True, slots=True)
class AerospikeConfig:
    environment: Environment = Environment.LOCAL
    host: str = "127.0.0.1"
    port: int = 3000
    namespace: str = "test"
    agent_skill_set: str = "agent_skills"
    agent_skill_key: str = "mfa-verification"

    @classmethod
    def from_env(cls) -> "AerospikeConfig":
        return cls(
            environment=Environment(os.getenv("ENVIRONMENT", "local").lower()),
            host=os.getenv("AEROSPIKE_HOST", "127.0.0.1"),
            port=int(os.getenv("AEROSPIKE_PORT", "3000")),
            namespace=os.getenv("AEROSPIKE_NAMESPACE", "test"),
            agent_skill_set=os.getenv("AEROSPIKE_AGENT_SKILL_SET", "agent_skills"),
            agent_skill_key=os.getenv("AEROSPIKE_AGENT_SKILL_KEY", "mfa-verification"),
        )
