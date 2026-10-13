import unittest
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import patch

from langgraph.checkpoint.memory import InMemorySaver
from starlette.testclient import TestClient

from src.a2a.server import create_app


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.saver = InMemorySaver()
        self.connection_closed = False

        @asynccontextmanager
        async def prepare():
            try:
                from src.graphs.agent import build_graph

                yield SimpleNamespace(
                    graph=build_graph(self.saver), mcp=SimpleNamespace()
                )
            finally:
                self.connection_closed = True

        self.patch = patch("src.a2a.server.prepare", prepare)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def send(self, client, data=None, context_id="test-context", text=None):
        part = {"text": text} if text is not None else {"data": data}
        return client.post(
            "/",
            headers={"A2A-Version": "1.0"},
            json={
                "jsonrpc": "2.0",
                "id": "1",
                "method": "SendMessage",
                "params": {
                    "message": {
                        "messageId": "test-message",
                        "contextId": context_id,
                        "role": "ROLE_USER",
                        "parts": [part],
                    }
                },
            },
        )

    def test_discovery_execution_checkpoint_and_shutdown(self):
        with patch.dict("os.environ", {"A2A_PUBLIC_URL": "https://agent.example/"}):
            app = create_app()
        with TestClient(app) as client:
            response = client.get("/.well-known/agent-card.json")
            self.assertEqual(response.status_code, 200)
            card = response.json()
            self.assertEqual(
                card["supportedInterfaces"][0]["url"], "https://agent.example/"
            )
            self.assertFalse(card["capabilities"]["streaming"])
            self.assertEqual(card["defaultInputModes"], ["application/json"])
            self.assertEqual(card["skills"][0]["id"], "mfa-journey")

            payload = {"user_id": "user-123", "journey_id": "mfa-login"}
            response = self.send(client, payload)
            self.assertEqual(response.status_code, 200)
            message = response.json()["result"]["message"]
            self.assertEqual(
                message["parts"][0]["text"],
                "MFA journey accepted for user user-123 using journey mfa-login.",
            )
            self.assertEqual(message["contextId"], "test-context")
            state = app.state.graph.get_state(
                {"configurable": {"thread_id": "test-context"}}
            )
            self.assertEqual(state.values["user_id"], "user-123")
            self.assertEqual(state.values["journey_id"], "mfa-login")
        self.assertTrue(self.connection_closed)

    def test_missing_or_empty_fields_are_rejected(self):
        with TestClient(create_app()) as client:
            for payload in (
                {},
                {"user_id": "user-123"},
                {"user_id": " ", "journey_id": "mfa-login"},
                {"user_id": "user-123", "journey_id": ""},
            ):
                with self.subTest(payload=payload):
                    response = self.send(client, payload)
                    self.assertEqual(response.json()["error"]["code"], -32602)

    def test_text_input_is_rejected(self):
        with TestClient(create_app()) as client:
            response = self.send(client, text="user-123 mfa-login")
            self.assertEqual(response.json()["error"]["code"], -32602)

    def test_unknown_journey_is_rejected_before_graph_execution(self):
        app = create_app()
        with TestClient(app) as client:
            response = self.send(
                client,
                {"user_id": "user-123", "journey_id": "unknown"},
            )
            self.assertEqual(response.json()["error"]["code"], -32602)
            self.assertIn("Unknown journey_id", response.json()["error"]["message"])
            self.assertEqual(
                app.state.graph.get_state(
                    {"configurable": {"thread_id": "test-context"}}
                ).values,
                {},
            )
