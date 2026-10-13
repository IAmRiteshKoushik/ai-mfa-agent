"""A2A Agent Card definition for the MFA Agent."""

from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

from src.config import AppConfig


def build_agent_card() -> AgentCard:
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
                url=AppConfig.from_env().a2a_public_url,
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            )
        ],
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=[
            AgentSkill(
                id="mfa-verification",
                name="MFA Verification",
                description=(
                    "Authenticate a user via multi-factor authentication. "
                    "Supports sequential password and OTP verification. "
                    "Requires a transaction_id to begin the authentication flow."
                ),
                tags=["authentication", "mfa", "security", "password", "otp"],
            )
        ],
    )
