
"""
SQLite storage for user accounts and refresh sessions.

- Password hashes only; never plaintext passwords.
- Refresh token hashes only; never raw tokens.
- Per-operation database connections.
- Atomic refresh-session rotation.
"""

import hashlib
import sqlite3
import time
from pathlib import Path
from uuid import uuid4

from app.config import settings


class AuthDatabase:
    def __init__(self, db_path: str | None = None):
        self.db_path = str(
            db_path or settings.AUTH_DATABASE_PATH
        )

        Path(self.db_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.db_path,
            timeout=10,
        )

        connection.row_factory = sqlite3.Row

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        connection.execute(
            "PRAGMA busy_timeout = 10000"
        )

        return connection

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS refresh_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    expires_at INTEGER NOT NULL,
                    revoked_at INTEGER,
                    created_at INTEGER NOT NULL,
                    FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE CASCADE
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_refresh_sessions_user
                ON refresh_sessions(user_id)
                """
            )

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _to_dict(
        row: sqlite3.Row | None,
    ) -> dict | None:
        return dict(row) if row else None

    def create_user(
        self,
        email: str,
        password_hash: str,
    ) -> dict | None:
        user_id = str(uuid4())
        normalized_email = email.strip().lower()

        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO users
                        (id, email, password_hash, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        normalized_email,
                        password_hash,
                        int(time.time()),
                    ),
                )

        except sqlite3.IntegrityError:
            return None

        return self.get_user_by_id(user_id)

    def get_user_by_email(
        self,
        email: str,
    ) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, email, password_hash, created_at
                FROM users
                WHERE email = ?
                """,
                (email.strip().lower(),),
            ).fetchone()

        return self._to_dict(row)

    def get_user_by_id(
        self,
        user_id: str,
    ) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, email, password_hash, created_at
                FROM users
                WHERE id = ?
                """,
                (user_id,),
            ).fetchone()

        return self._to_dict(row)

    def create_session(
        self,
        user_id: str,
        refresh_token: str,
        expires_at: int,
    ) -> str:
        session_id = str(uuid4())

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO refresh_sessions
                    (
                        id,
                        user_id,
                        token_hash,
                        expires_at,
                        revoked_at,
                        created_at
                    )
                VALUES (?, ?, ?, ?, NULL, ?)
                """,
                (
                    session_id,
                    user_id,
                    self.hash_token(refresh_token),
                    expires_at,
                    int(time.time()),
                ),
            )

        return session_id

    def get_active_session(
        self,
        refresh_token: str,
    ) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    expires_at,
                    created_at
                FROM refresh_sessions
                WHERE token_hash = ?
                  AND revoked_at IS NULL
                  AND expires_at > ?
                """,
                (
                    self.hash_token(refresh_token),
                    int(time.time()),
                ),
            ).fetchone()

        return self._to_dict(row)

    def rotate_session(
        self,
        old_refresh_token: str,
        new_refresh_token: str,
        user_id: str,
        new_expires_at: int,
    ) -> bool:
        """
        Atomically revoke the old refresh token and
        store its replacement.

        Returns False if the old token was already
        revoked, expired, or belongs to another user.
        """
        now = int(time.time())

        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE refresh_sessions
                SET revoked_at = ?
                WHERE token_hash = ?
                  AND user_id = ?
                  AND revoked_at IS NULL
                  AND expires_at > ?
                """,
                (
                    now,
                    self.hash_token(old_refresh_token),
                    user_id,
                    now,
                ),
            )

            if cursor.rowcount != 1:
                return False

            connection.execute(
                """
                INSERT INTO refresh_sessions
                    (
                        id,
                        user_id,
                        token_hash,
                        expires_at,
                        revoked_at,
                        created_at
                    )
                VALUES (?, ?, ?, ?, NULL, ?)
                """,
                (
                    str(uuid4()),
                    user_id,
                    self.hash_token(new_refresh_token),
                    new_expires_at,
                    now,
                ),
            )

        return True

    def revoke_session(
        self,
        refresh_token: str,
    ) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE refresh_sessions
                SET revoked_at = ?
                WHERE token_hash = ?
                  AND revoked_at IS NULL
                """,
                (
                    int(time.time()),
                    self.hash_token(refresh_token),
                ),
            )

        return cursor.rowcount == 1

    def revoke_all_user_sessions(
        self,
        user_id: str,
    ) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE refresh_sessions
                SET revoked_at = ?
                WHERE user_id = ?
                  AND revoked_at IS NULL
                """,
                (
                    int(time.time()),
                    user_id,
                ),
            )

        return cursor.rowcount
