"""Load and validate the Agent Card skill record from Aerospike."""

from collections.abc import Mapping

import aerospike

from src.config.aerospike import AerospikeConfig
from src.config.agent_skill import AgentSkillConfig


class AgentSkillRecordError(ValueError):
    """Raised when the configured Aerospike record is not a valid skill."""


def load_agent_skill(
    client: aerospike.Client,
    config: AerospikeConfig,
) -> AgentSkillConfig:
    """Read one configured skill record and validate its bins."""
    key: tuple[str, str, str] = (
        config.namespace,
        config.agent_skill_set,
        config.agent_skill_key,
    )
    try:
        _key, _metadata, bins = client.get(key)
    except aerospike.exception.RecordNotFound as exc:
        raise AgentSkillRecordError(
            "Agent skill record was not found at "
            f"({config.namespace!r}, {config.agent_skill_set!r}, "
            f"{config.agent_skill_key!r})"
        ) from exc

    if not isinstance(bins, Mapping):
        raise AgentSkillRecordError("Agent skill record bins must be a map")

    skill_id = _required_string(bins, "id", key)
    name = _required_string(bins, "name", key)
    description = _required_string(bins, "description", key)
    tags_value = bins.get("tags")
    if not isinstance(tags_value, list) or not all(
        isinstance(tag, str) and tag.strip() for tag in tags_value
    ):
        raise AgentSkillRecordError(
            f"Agent skill record {key!r} bin 'tags' must be a list of non-empty strings"
        )

    return AgentSkillConfig(
        id=skill_id,
        name=name,
        description=description,
        tags=tuple(tags_value),
    )


def _required_string(
    bins: Mapping[str, object],
    bin_name: str,
    key: tuple[str, str, str],
) -> str:
    value = bins.get(bin_name)
    if not isinstance(value, str) or not value.strip():
        raise AgentSkillRecordError(
            f"Agent skill record {key!r} bin {bin_name!r} must be a non-empty string"
        )
    return value
