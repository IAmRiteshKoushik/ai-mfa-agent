"""Discover a peer's Agent Card and send A2A requests."""

from collections.abc import AsyncIterator
from uuid import uuid4

import httpx
from a2a.client import ClientConfig, ClientFactory
from a2a.types import Message, Part, Role, SendMessageRequest, StreamResponse
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value


def text_request(text: str) -> SendMessageRequest:
    return SendMessageRequest(
        message=Message(
            message_id=str(uuid4()),
            role=Role.ROLE_USER,
            parts=[Part(text=text)],
        )
    )


def mfa_journey_request(user_id: str, journey_id: str) -> SendMessageRequest:
    """Build a structured MFA journey request for a peer agent."""
    payload = json_format.ParseDict(
        {"user_id": user_id, "journey_id": journey_id}, Value()
    )
    return SendMessageRequest(
        message=Message(
            message_id=str(uuid4()),
            role=Role.ROLE_USER,
            parts=[Part(data=payload, media_type="application/json")],
        )
    )


async def send_to_peer(url: str, text: str) -> AsyncIterator[StreamResponse]:
    async for response in _send_to_peer(url, text_request(text)):
        yield response


async def send_mfa_journey(
    url: str, user_id: str, journey_id: str
) -> AsyncIterator[StreamResponse]:
    """Send a structured MFA journey request to an A2A agent."""
    async for response in _send_to_peer(url, mfa_journey_request(user_id, journey_id)):
        yield response


async def _send_to_peer(
    url: str, request: SendMessageRequest
) -> AsyncIterator[StreamResponse]:
    async with httpx.AsyncClient(timeout=30.0) as http_client:
        factory = ClientFactory(ClientConfig(httpx_client=http_client, streaming=False))
        client = await factory.create_from_url(url)
        try:
            async for response in client.send_message(request):
                yield response
        finally:
            await client.close()
