import sqlite3
import time
from contextlib import contextmanager

LOCK_SCHEMA = """
CREATE TABLE IF NOT EXISTS poller_locks (
  name TEXT PRIMARY KEY,
  owner TEXT NOT NULL,
  expires_at REAL NOT NULL
);
"""


def init_lock_table(conn: sqlite3.Connection):
    conn.execute(LOCK_SCHEMA)
    conn.commit()


@contextmanager
def acquire_lock(conn: sqlite3.Connection,
                 name: str,
                 owner: str,
                 ttl_seconds: int = 120,
                 retry_seconds: float = 0.5,
                 max_wait_seconds: float = 10.0):
    """
    Try to acquire a named lock. If the lock is expired, steal it.
    Yields True if acquired, else False (never raises for contention).
    """
    start = time.time()
    init_lock_table(conn)
    got = False
    while time.time() - start < max_wait_seconds:
        now = time.time()
        exp = now + ttl_seconds
        try:
            # Insert if not exists
            conn.execute(
                "INSERT INTO poller_locks(name, owner, expires_at) VALUES (?,?,?)",
                (name, owner, exp))
            conn.commit()
            got = True
            break
        except sqlite3.IntegrityError:
            # Exists -> check expiry
            cur = conn.execute(
                "SELECT owner, expires_at FROM poller_locks WHERE name = ?",
                (name, ))
            row = cur.fetchone()
            if row and row["expires_at"] < now:
                # Steal expired lock
                conn.execute(
                    "UPDATE poller_locks SET owner = ?, expires_at = ? WHERE name = ?",
                    (owner, exp, name))
                conn.commit()
                got = True
                break
        time.sleep(retry_seconds)
    try:
        yield got
    finally:
        if got:
            try:
                conn.execute(
                    "DELETE FROM poller_locks WHERE name = ? AND owner = ?",
                    (name, owner))
                conn.commit()
            except Exception:
                pass
