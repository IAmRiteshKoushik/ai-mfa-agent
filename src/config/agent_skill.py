"""Typed configuration for the skill advertised by the A2A Agent Card."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AgentSkillConfig:
    """Skill fields stored in an Aerospike record."""

    id: str
    name: str
    description: str
    tags: tuple[str, ...]
