"""Small OAuth-style session store."""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class OAuthSession:
    session_id: str
    user_id: str
    scopes: tuple[str, ...]
    created_at: int
    expires_at: int

    @property
    def expired(self) -> bool:
        return int(time.time()) >= self.expires_at


class OAuthSessionStore:
    """Persist user-scoped OAuth sessions without storing raw access tokens."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self._connection = sqlite3.connect(self.path)
        self._connection.row_factory = sqlite3.Row
        self._init_schema()

    def create_state(self) -> str:
        return secrets.token_urlsafe(24)

    def create_session(
        self,
        user_id: str,
        access_token: str,
        scopes: tuple[str, ...],
        ttl_seconds: int = 3600,
    ) -> OAuthSession:
        now = int(time.time())
        session = OAuthSession(
            session_id=secrets.token_urlsafe(24),
            user_id=user_id,
            scopes=tuple(sorted(set(scopes))),
            created_at=now,
            expires_at=now + ttl_seconds,
        )
        self._connection.execute(
            """
            insert into oauth_sessions (
              session_id, user_id, access_token_hash, scopes, created_at, expires_at
            ) values (?, ?, ?, ?, ?, ?)
            """,
            (
                session.session_id,
                user_id,
                self._token_hash(access_token),
                ",".join(session.scopes),
                session.created_at,
                session.expires_at,
            ),
        )
        self._connection.commit()
        return session

    def get_session(self, session_id: str) -> OAuthSession | None:
        row = self._connection.execute(
            "select * from oauth_sessions where session_id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        return OAuthSession(
            session_id=row["session_id"],
            user_id=row["user_id"],
            scopes=tuple(filter(None, row["scopes"].split(","))),
            created_at=row["created_at"],
            expires_at=row["expires_at"],
        )

    def verify_token(self, session_id: str, access_token: str) -> bool:
        row = self._connection.execute(
            "select access_token_hash, expires_at from oauth_sessions where session_id = ?",
            (session_id,),
        ).fetchone()
        if row is None or int(time.time()) >= row["expires_at"]:
            return False
        return secrets.compare_digest(row["access_token_hash"], self._token_hash(access_token))

    def revoke(self, session_id: str) -> None:
        self._connection.execute("delete from oauth_sessions where session_id = ?", (session_id,))
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def _init_schema(self) -> None:
        self._connection.execute(
            """
            create table if not exists oauth_sessions (
              session_id text primary key,
              user_id text not null,
              access_token_hash text not null,
              scopes text not null,
              created_at integer not null,
              expires_at integer not null
            )
            """
        )
        self._connection.commit()

    def _token_hash(self, access_token: str) -> str:
        return hashlib.sha256(access_token.encode("utf-8")).hexdigest()
