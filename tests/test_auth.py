from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src import auth


def auth_response(access_token: str, refresh_token: str):
    user = SimpleNamespace(
        id="user-123",
        email="friend@example.com",
        user_metadata={"display_name": "Friend"},
    )
    session = SimpleNamespace(
        access_token=access_token,
        refresh_token=refresh_token,
    )
    return SimpleNamespace(session=session, user=user)


class AuthSessionTests(unittest.TestCase):
    def test_browser_session_round_trip(self) -> None:
        encoded = auth._serialize_browser_session("access", "refresh")

        self.assertEqual(auth._parse_browser_session(encoded), ("access", "refresh"))
        self.assertEqual(json.loads(encoded)["version"], 1)

    def test_browser_session_rejects_missing_tokens(self) -> None:
        with self.assertRaises(ValueError):
            auth._parse_browser_session('{"version":1,"access_token":""}')

    def test_store_auth_response_schedules_browser_persistence(self) -> None:
        state: dict[str, object] = {}
        with patch.object(auth.st, "session_state", state):
            auth._store_auth_response(auth_response("access", "refresh"))

        self.assertEqual(state["access_token"], "access")
        self.assertEqual(state["refresh_token"], "refresh")
        self.assertEqual(state["user"]["display_name"], "Friend")
        action = state[auth._BROWSER_ACTION_STATE_KEY]
        self.assertEqual(action["action"], "store")
        self.assertEqual(
            auth._parse_browser_session(action["session_json"]),
            ("access", "refresh"),
        )

    def test_get_authed_client_persists_rotated_tokens(self) -> None:
        refreshed = auth_response("new-access", "new-refresh")
        fake_auth = SimpleNamespace(set_session=lambda *_: refreshed)
        fake_client = SimpleNamespace(auth=fake_auth)
        state = {
            "access_token": "old-access",
            "refresh_token": "old-refresh",
            "user": {
                "id": "user-123",
                "email": "friend@example.com",
                "display_name": "Friend",
            },
        }

        with (
            patch.object(auth.st, "session_state", state),
            patch.object(auth, "get_client", return_value=fake_client),
        ):
            result = auth.get_authed_client()

        self.assertIs(result, fake_client)
        self.assertEqual(state["access_token"], "new-access")
        self.assertEqual(state["refresh_token"], "new-refresh")
        action = state[auth._BROWSER_ACTION_STATE_KEY]
        self.assertEqual(
            auth._parse_browser_session(action["session_json"]),
            ("new-access", "new-refresh"),
        )

    def test_restore_auth_session_validates_and_restores_browser_tokens(self) -> None:
        stored_session = auth._serialize_browser_session("access", "refresh")
        snapshot = json.dumps({"session_json": stored_session, "error": None})
        refreshed = auth_response("new-access", "new-refresh")
        fake_auth = SimpleNamespace(set_session=lambda *_: refreshed)
        fake_client = SimpleNamespace(auth=fake_auth)
        fake_bridge = lambda **_: SimpleNamespace(snapshot_json=snapshot)
        state: dict[str, object] = {}

        with (
            patch.object(auth.st, "session_state", state),
            patch.object(auth, "get_client", return_value=fake_client),
            patch.object(auth, "_browser_session_bridge", fake_bridge),
            patch.object(auth.st, "rerun") as rerun,
        ):
            auth.restore_auth_session()

        self.assertEqual(state["access_token"], "new-access")
        self.assertEqual(state["refresh_token"], "new-refresh")
        self.assertEqual(state["user"]["id"], "user-123")
        rerun.assert_called_once_with()

    def test_restore_auth_session_clears_invalid_browser_tokens(self) -> None:
        snapshot = json.dumps({"session_json": "not-json", "error": None})
        fake_bridge = lambda **_: SimpleNamespace(snapshot_json=snapshot)
        state: dict[str, object] = {}

        with (
            patch.object(auth.st, "session_state", state),
            patch.object(auth, "_browser_session_bridge", fake_bridge),
            patch.object(auth.st, "rerun") as rerun,
        ):
            auth.restore_auth_session()

        self.assertEqual(
            state[auth._BROWSER_ACTION_STATE_KEY],
            {"action": "clear"},
        )
        rerun.assert_called_once_with()

    def test_browser_store_acknowledgement_clears_pending_action(self) -> None:
        stored_session = auth._serialize_browser_session("access", "refresh")
        snapshot = json.dumps({"session_json": stored_session, "error": None})
        fake_bridge = lambda **_: SimpleNamespace(snapshot_json=snapshot)
        state = {
            auth._BROWSER_ACTION_STATE_KEY: {
                "action": "store",
                "session_json": stored_session,
            }
        }

        with (
            patch.object(auth.st, "session_state", state),
            patch.object(auth, "_browser_session_bridge", fake_bridge),
        ):
            auth.restore_auth_session()

        self.assertNotIn(auth._BROWSER_ACTION_STATE_KEY, state)

    def test_clear_local_auth_schedules_browser_clear(self) -> None:
        state = {
            "access_token": "access",
            "refresh_token": "refresh",
            "user": {"id": "user-123"},
        }
        with patch.object(auth.st, "session_state", state):
            auth._clear_local_auth(clear_browser=True)

        self.assertNotIn("access_token", state)
        self.assertNotIn("refresh_token", state)
        self.assertNotIn("user", state)
        self.assertEqual(
            state[auth._BROWSER_ACTION_STATE_KEY],
            {"action": "clear"},
        )


if __name__ == "__main__":
    unittest.main()
