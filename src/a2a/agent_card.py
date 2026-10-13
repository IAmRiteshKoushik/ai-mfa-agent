"""A2A Agent Card definition for the MFA Agent."""

from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

from src.config.agent_skill import AgentSkillConfig


def build_agent_card(public_url: str, skill_config: AgentSkillConfig) -> AgentCard:
    return AgentCard(
        name="MFA Agent",
        description=(
            "Multi-Factor Authentication agent that guides users through "
            "sequential authentication steps (password, OTP) to verify identity "
            "before executing a pending transaction."
        ),
        version="0.1.0",
        supported_interfaces=[
            AgentInterface(
                url=public_url,
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            )
        ],
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=[
            AgentSkill(
                id=skill_config.id,
                name=skill_config.name,
                description=skill_config.description,
                tags=list(skill_config.tags),
            )
        ],
    )
