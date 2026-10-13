"""Insert an Agent Card skill record into Aerospike."""

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass

import aerospike

from src.config.aerospike import AerospikeConfig
from src.config.agent_skill import AgentSkillConfig
from src.infra.aerospike import open_aerospike_client


@dataclass(frozen=True, slots=True)
class SkillArguments:
    """Validated CLI values for one skill record."""

    skill: AgentSkillConfig
    record_key: str | None


def _non_empty(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise argparse.ArgumentTypeError("value must not be empty")
    return normalized


def parse_args(argv: Sequence[str] | None = None) -> SkillArguments:
    """Parse a skill definition and optional Aerospike record key."""
    parser = argparse.ArgumentParser(
        description="Insert one skill record for the MFA agent into Aerospike."
    )
    parser.add_argument("--id", required=True, type=_non_empty, dest="skill_id")
    parser.add_argument("--name", required=True, type=_non_empty)
    parser.add_argument("--description", required=True, type=_non_empty)
    parser.add_argument(
        "--tag",
        required=True,
        action="append",
        type=_non_empty,
        dest="tags",
        help="Skill tag. Repeat this option for each tag.",
    )
    parser.add_argument(
        "--key",
        type=_non_empty,
        help="Aerospike record key. Defaults to AEROSPIKE_AGENT_SKILL_KEY.",
    )
    args = parser.parse_args(argv)
    return SkillArguments(
        skill=AgentSkillConfig(
            id=args.skill_id,
            name=args.name,
            description=args.description,
            tags=tuple(args.tags),
        ),
        record_key=args.key,
    )


def insert_skill(
    config: AerospikeConfig,
    skill: AgentSkillConfig,
    record_key: str | None = None,
) -> tuple[str, str, str]:
    """Create a skill record without replacing a record that already exists."""
    key: tuple[str, str, str] = (
        config.namespace,
        config.agent_skill_set,
        record_key or config.agent_skill_key,
    )
    bins: dict[str, str | list[str]] = {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description,
        "tags": list(skill.tags),
    }
    with open_aerospike_client(config) as client:
        client.put(key, bins, policy={"exists": aerospike.POLICY_EXISTS_CREATE})
    return key


def main(argv: Sequence[str] | None = None) -> int:
    """Insert a skill using Aerospike settings from the environment."""
    arguments = parse_args(argv)
    config = AerospikeConfig.from_env()
    try:
        namespace, set_name, record_key = insert_skill(
            config,
            arguments.skill,
            arguments.record_key,
        )
    except aerospike.exception.RecordExists:
        print(
            "Skill record already exists. Choose another --key or remove the "
            "existing record before inserting it again.",
            file=sys.stderr,
        )
        return 1

    print(
        f"Inserted skill {arguments.skill.id!r} at {namespace}.{set_name}/{record_key}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
