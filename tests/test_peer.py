import unittest

from google.protobuf import json_format

from src.a2a.peer import mfa_journey_request


class PeerTests(unittest.TestCase):
    def test_mfa_journey_request_uses_structured_data_part(self):
        request = mfa_journey_request("user-123", "mfa-login")
        part = request.message.parts[0]

        self.assertEqual(part.WhichOneof("content"), "data")
        self.assertEqual(part.media_type, "application/json")
        self.assertEqual(
            json_format.MessageToDict(part.data),
            {"user_id": "user-123", "journey_id": "mfa-login"},
        )
