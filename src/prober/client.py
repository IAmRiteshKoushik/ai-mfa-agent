"""Interactive REPL for sending messages to an A2A agent."""

import asyncio
import os

from src.a2a.peer import send_to_peer


async def _repl(url: str) -> None:
    print(f"Connected to A2A agent at {url}")
    print("Enter a message and press Enter to send it. Use Ctrl-D or Ctrl-C to exit.")

    while True:
        try:
            message = await asyncio.to_thread(input, "you> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if not message.strip():
            continue

        try:
            async for response in send_to_peer(url, message):
                print(f"agent> {response}")
        except Exception as exc:
            print(f"A2A request failed: {exc}")


def main() -> None:
    url = os.getenv("MFA_AGENT_URL", "http://localhost:8000/")
    try:
        asyncio.run(_repl(url))
    except KeyboardInterrupt:
        print()
