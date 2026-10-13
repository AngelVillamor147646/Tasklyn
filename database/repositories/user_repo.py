"""User repository."""
from __future__ import annotations
import sqlite3
from typing import Optional
from database.repositories.base import BaseRepository
from models import User


class UserRepository(BaseRepository[User]):
    TABLE = "users"

    def _row_to_model(self, row: sqlite3.Row) -> User:
        return User(
            id=row["id"],
            name=row["name"],
            avatar_id=row["avatar_id"],
            gender=row["gender"],
            password=row["password"] if "password" in row.keys() else None,
            recovery_key_hash=row["recovery_key_hash"] if "recovery_key_hash" in row.keys() else None,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def set_password(self, user_id: int, password: Optional[str]) -> bool:
        cur = self._execute(
            "UPDATE users SET password=?, updated_at=datetime('now','localtime') WHERE id=?",
            (password, user_id),
        )
        self._commit()
        return cur.rowcount > 0

    def set_recovery_key_hash(self, user_id: int, key_hash: str) -> bool:
        cur = self._execute(
            "UPDATE users SET recovery_key_hash=?, updated_at=datetime('now','localtime') WHERE id=?",
            (key_hash, user_id),
        )
        self._commit()
        return cur.rowcount > 0

    def create(self, name: str, avatar_id: str = "boy_neutral", gender: str = "boy", password: Optional[str] = None) -> User:
        row_id = self._insert({"name": name, "avatar_id": avatar_id, "gender": gender, "password": password})
        return self.get_by_id(row_id)  # type: ignore[return-value]

    def update_profile(self, user_id: int, name: str, avatar_id: str, gender: str) -> bool:
        cur = self._execute(
            """UPDATE users SET name=?, avatar_id=?, gender=?,
               updated_at=datetime('now','localtime') WHERE id=?""",
            (name, avatar_id, gender, user_id),
        )
        self._commit()
        return cur.rowcount > 0

    def get_first(self) -> Optional[User]:
        row = self._fetchone("SELECT * FROM users ORDER BY id LIMIT 1")
        return self._row_to_model(row) if row else None
