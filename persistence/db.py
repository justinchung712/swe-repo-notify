import sqlite3
from typing import Optional

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT,
  phone TEXT,
  is_verified INTEGER NOT NULL DEFAULT 0,
  notify_email INTEGER NOT NULL DEFAULT 0,
  notify_sms INTEGER NOT NULL DEFAULT 0,
  subscribe_new_grad INTEGER NOT NULL DEFAULT 0,
  subscribe_internship INTEGER NOT NULL DEFAULT 0,
  receive_all INTEGER NOT NULL DEFAULT 0,
  tech_keywords TEXT NOT NULL DEFAULT '',
  role_keywords TEXT NOT NULL DEFAULT '',
  location_keywords TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS repo_state (
  repo_name TEXT PRIMARY KEY,
  last_sha TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sent_notifications (
  user_id TEXT NOT NULL,
  job_id TEXT NOT NULL,
  sent_at TEXT NOT NULL,
  PRIMARY KEY (user_id, job_id)
);
"""


def get_conn(path: Optional[str] = None) -> sqlite3.Connection:
    """
    Returns a sqlite3 connection. If path is None, uses in-memory DB.
    Use check_same_thread=False so FastAPI handlers (thread pool) can share it.
    """
    conn = sqlite3.connect(path or ":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()
