"""Send a structured MFA journey request to the agent under test."""

import argparse
import asyncio
import os

from src.a2a.peer import send_mfa_journey


async def _send(url: str, user_id: str, journey_id: str) -> None:
    async for response in send_mfa_journey(url, user_id, journey_id):
        print(response)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url", default=os.getenv("MFA_AGENT_URL", "http://localhost:8000/")
    )
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--journey-id", required=True)
    args = parser.parse_args()
    asyncio.run(_send(args.url, args.user_id, args.journey_id))
