import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from common.models import UserPreferences


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _list_to_csv(items: List[str]) -> str:
    return ",".join(s.strip() for s in items if s and s.strip())


def _csv_to_list(s: str) -> List[str]:
    s = s or ""
    return [x.strip() for x in s.split(",") if x.strip()]


class UserRepository:

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create_user(self, user_id: str, email: Optional[str],
                    phone: Optional[str], is_verified: bool,
                    prefs: UserPreferences) -> None:
        now = _now_iso()
        self.conn.execute(
            """
            INSERT INTO users (
              id, email, phone, is_verified,
              subscribe_new_grad, subscribe_internship, receive_all,
              tech_keywords, role_keywords, location_keywords,
              created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, email, phone, int(is_verified),
             int(prefs.subscribe_new_grad), int(prefs.subscribe_internship),
             int(prefs.receive_all), _list_to_csv(
                 prefs.tech_keywords), _list_to_csv(prefs.role_keywords),
             _list_to_csv(prefs.location_keywords), now, now),
        )
        self.conn.commit()

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        cur = self.conn.execute("SELECT * FROM users WHERE id = ?",
                                (user_id, ))
        row = cur.fetchone()
        if not row:
            return None
        prefs = UserPreferences(
            subscribe_new_grad=bool(row["subscribe_new_grad"]),
            subscribe_internship=bool(row["subscribe_internship"]),
            receive_all=bool(row["receive_all"]),
            tech_keywords=_csv_to_list(row["tech_keywords"]),
            role_keywords=_csv_to_list(row["role_keywords"]),
            location_keywords=_csv_to_list(row["location_keywords"]),
        )
        return {
            "id": row["id"],
            "email": row["email"],
            "phone": row["phone"],
            "is_verified": row["is_verified"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "prefs": prefs,
        }

    def update_user(self, user_id: str, email: Optional[str],
                    phone: Optional[str], is_verified: Optional[bool],
                    prefs: Optional[UserPreferences]) -> None:
        # Build dynamic update
        fields = []
        params: List[Any] = []
        if email is not None:
            fields.append("email = ?")
            params.append(email)
        if phone is not None:
            fields.append("phone = ?")
            params.append(phone)
        if is_verified is not None:
            fields.append("is_verified = ?")
            params.append(int(is_verified))
        if prefs is not None:
            fields.extend([
                "subscribe_new_grad = ?",
                "subscribe_internship = ?",
                "receive_all = ?",
                "tech_keywords = ?",
                "role_keywords = ?",
                "location_keywords = ?",
            ])
            params.extend([
                int(prefs.subscribe_new_grad),
                int(prefs.subscribe_internship),
                int(prefs.receive_all),
                _list_to_csv(prefs.tech_keywords),
                _list_to_csv(prefs.role_keywords),
                _list_to_csv(prefs.location_keywords),
            ])
        fields.append("updated_at = ?")
        params.append(_now_iso())
        params.append(user_id)
        sql = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
        self.conn.execute(sql, tuple(params))
        self.conn.commit()


class RepoStateRepository:

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_last_sha(self, repo_name: str) -> Optional[str]:
        cur = self.conn.execute(
            "SELECT last_sha FROM repo_state WHERE repo_name = ?",
            (repo_name, ))
        row = cur.fetchone()
        return row["last_sha"] if row else None

    def upsert_last_sha(self, repo_name: str, sha: str) -> None:
        now = _now_iso()
        self.conn.execute(
            """
            INSERT INTO repo_state (repo_name, last_sha, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(repo_name) DO UPDATE SET last_sha = excluded.last_sha, updated_at = excluded.updated_at
            """, (repo_name, sha, now))
        self.conn.commit()


class SentNotificationsRepository:

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def was_sent(self, user_id: str, job_id: str) -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM sent_notifications WHERE user_id = ? AND job_id = ?",
            (user_id, job_id),
        )
        return cur.fetchone() is not None

    def mark_sent(self, user_id: str, job_id: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO sent_notifications (user_id, job_id, sent_at) VALUES (?, ?, ?)",
            (user_id, job_id, _now_iso()))
        self.conn.commit()
