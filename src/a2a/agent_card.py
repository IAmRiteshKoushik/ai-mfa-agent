"""Public discovery metadata. Advertise only implemented skills."""

from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

from src.config import AppConfig


def build_agent_card() -> AgentCard:
    return AgentCard(
        name="AI MFA agent",
        description="Accepts structured MFA journey requests and logs their IDs.",
        version="0.1.0",
        supported_interfaces=[
            AgentInterface(
                url=AppConfig.from_env().a2a_public_url,
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            )
        ],
        capabilities=AgentCapabilities(streaming=False, push_notifications=False),
        default_input_modes=["application/json"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="mfa-journey",
                name="MFA journey intake",
                description="Accepts a user ID and a recognized MFA journey ID.",
                tags=["mfa", "journey"],
                examples=['{"user_id":"user-123","journey_id":"mfa-login"}'],
            )
        ],
    )
