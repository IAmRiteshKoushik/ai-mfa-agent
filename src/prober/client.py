"""Interactive Root Agent prober for greeting users and routing MFA journeys."""

import asyncio
import os
import re

import httpx
from a2a.client import A2AClientError, AgentCardResolutionError
from a2a.types import StreamResponse, TaskState

from src.a2a.peer import send_mfa_journey

JOURNEY_IDS = (
    "subgraph_otp",
    "subgraph_mpin",
    "subgraph_split_otp",
    "subgraph_nb_password",
)


def greet() -> str:
    return (
        "👋 Hello! I am the Root Agent.\n"
        "I can help with general requests and route MFA journeys.\n"
        "To start one, say something like 'Authenticate with subgraph_otp'."
    )


def _is_mfa_request(text: str) -> bool:
    return bool(
        re.search(
            r"\b(?:authenticate|mfa|transaction|verify|auth)\b|\btxn-",
            text,
            re.IGNORECASE,
        )
    )


def _response_text(response: StreamResponse) -> str | None:
    """Extract the immediate agent message used by this service."""
    if response.HasField("message"):
        parts = response.message.parts
        return "\n".join(
            part.text for part in parts if part.WhichOneof("content") == "text"
        )
    if response.HasField("task") and response.task.HasField("status"):
        status = response.task.status
        if status.HasField("message"):
            return "\n".join(
                part.text
                for part in status.message.parts
                if part.WhichOneof("content") == "text"
            )
    if response.HasField("status_update"):
        status = response.status_update.status
        if status.HasField("message"):
            return "\n".join(
                part.text
                for part in status.message.parts
                if part.WhichOneof("content") == "text"
            )
    return None


async def _prompt(label: str) -> str:
    return await asyncio.to_thread(input, label)


async def _run_mfa_journey(url: str, request_text: str) -> str:
    """Collect the structured fields required by the current MFA agent."""
    user_match = re.search(r"\buser-[a-z0-9][a-z0-9_-]*\b", request_text, re.IGNORECASE)
    journey_id = next(
        (
            candidate
            for candidate in JOURNEY_IDS
            if candidate in request_text.casefold()
        ),
        None,
    )
    user_id = user_match.group(0) if user_match else ""
    if not user_id:
        user_id = (await _prompt("User ID: ")).strip()
    if not journey_id:
        print("Available journeys: " + ", ".join(JOURNEY_IDS))
        journey_id = (await _prompt("Journey ID: ")).strip()

    if not user_id or not journey_id:
        return "MFA journey cancelled because a user ID or journey ID was missing."
    if journey_id not in JOURNEY_IDS:
        return (
            f"Unknown journey '{journey_id}'. Choose one of: {', '.join(JOURNEY_IDS)}."
        )

    replies: list[str] = []
    async for response in send_mfa_journey(url, user_id, journey_id):
        message = _response_text(response)
        if message:
            replies.append(message)
        if (
            response.HasField("task")
            and response.task.HasField("status")
            and response.task.status.state == TaskState.TASK_STATE_FAILED
        ):
            break
        if (
            response.HasField("status_update")
            and response.status_update.status.state == TaskState.TASK_STATE_FAILED
        ):
            break
    return "\n".join(replies) if replies else "The MFA agent returned no message."


async def _repl(url: str) -> None:
    print(f"Connected to A2A agent at {url}")
    print("Enter a message and press Enter to send it. Use Ctrl-D or Ctrl-C to exit.")
    print(greet())

    while True:
        try:
            message = await asyncio.to_thread(input, "you> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if not message.strip():
            continue

        try:
            if _is_mfa_request(message):
                response = await _run_mfa_journey(url, message)
            else:
                response = (
                    f"{greet()}\n\nYou said: '{message}'. "
                    "If you need an MFA journey, include a user ID and journey ID, "
                    "such as 'Authenticate user-123 with subgraph_otp'."
                )
            print(f"agent> {response}")
        except (A2AClientError, AgentCardResolutionError, httpx.HTTPError) as exc:
            print(f"A2A request failed: {exc}")


def main() -> None:
    url = os.getenv("MFA_AGENT_URL", "http://localhost:8000/")
    try:
        asyncio.run(_repl(url))
    except KeyboardInterrupt:
        print()
