from unittest import TestCase

from arena.oauth import OAuthSessionStore


class OAuthSessionStoreTest(TestCase):
    def test_creates_verifies_and_revokes_session(self) -> None:
        store = OAuthSessionStore()
        session = store.create_session(
            user_id="sergey",
            access_token="temporary-token",
            scopes=("repo:read", "metrics:read"),
        )

        self.assertTrue(store.verify_token(session.session_id, "temporary-token"))
        self.assertFalse(store.verify_token(session.session_id, "wrong-token"))

        loaded = store.get_session(session.session_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.user_id, "sergey")

        store.revoke(session.session_id)
        self.assertIsNone(store.get_session(session.session_id))
        store.close()
