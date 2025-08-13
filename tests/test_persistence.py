import uuid
import sqlite3
import pytest
from datetime import datetime, timezone

from persistence.db import init_db, get_conn
from persistence.repositories import (UserRepository, RepoStateRepository,
                                      SentNotificationsRepository)
from common.models import UserPreferences


@pytest.fixture
def conn():
    # In-memory DB for tests
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    yield conn
    conn.close()


def test_init_db_creates_tables(conn):
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r["name"] for r in cur.fetchall()}
    assert {"users", "repo_state", "sent_notifications"} <= tables


def test_user_crud_roundtrip(conn):
    repo = UserRepository(conn)
    user_id = str(uuid.uuid4())
    prefs = UserPreferences(subscribe_new_grad=True,
                            subscribe_internship=False,
                            receive_all=False,
                            tech_keywords=["spring boot", "postgres"],
                            role_keywords=["backend"],
                            location_keywords=["remote"])
    repo.create_user(user_id=user_id,
                     email="a@b.com",
                     phone=None,
                     is_verified=False,
                     prefs=prefs,
                     notify_email=True,
                     notify_sms=False)

    got = repo.get_user(user_id)
    assert got["email"] == "a@b.com"
    assert got["is_verified"] == 0
    assert got["prefs"].tech_keywords == ["spring boot", "postgres"]
    assert got["prefs"].location_keywords == ["remote"]

    # Update preferences + verification
    new_prefs = UserPreferences(subscribe_new_grad=False,
                                subscribe_internship=True,
                                receive_all=True,
                                tech_keywords=[],
                                role_keywords=[],
                                location_keywords=[])
    repo.update_user(user_id,
                     email=None,
                     phone="123",
                     is_verified=True,
                     prefs=new_prefs)

    got2 = repo.get_user(user_id)
    assert got2["phone"] == "123"
    assert got2["is_verified"] == 1
    assert got2["prefs"].receive_all is True
    assert got2["prefs"].subscribe_internship is True
    assert got2["prefs"].subscribe_new_grad is False


def test_repo_state_upsert(conn):
    repo_state = RepoStateRepository(conn)
    repo_name = "SimplifyJobs/New-Grad-Positions"
    repo_state.upsert_last_sha(repo_name, "sha1")
    assert repo_state.get_last_sha(repo_name) == "sha1"
    repo_state.upsert_last_sha(repo_name, "sha2")
    assert repo_state.get_last_sha(repo_name) == "sha2"


def test_sent_notifications_dedup(conn):
    sent = SentNotificationsRepository(conn)
    uid = "u1"
    jid = "j1"
    assert sent.was_sent(uid, jid) is False
    sent.mark_sent(uid, jid)
    assert sent.was_sent(uid, jid) is True
