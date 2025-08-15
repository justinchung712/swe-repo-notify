import sqlite3, time
from persistence.lock import acquire_lock, init_lock_table


def test_lock_acquire_and_release():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_lock_table(conn)

    with acquire_lock(conn, "X", "owner1", ttl_seconds=2) as ok1:
        assert ok1
        with acquire_lock(conn,
                          "X",
                          "owner2",
                          ttl_seconds=2,
                          max_wait_seconds=0.5) as ok2:
            assert not ok2  # Cannot get while held

    # After release, can acquire
    with acquire_lock(conn, "X", "owner2", ttl_seconds=2) as ok3:
        assert ok3


def test_lock_expires_and_is_stolen():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_lock_table(conn)
    with acquire_lock(conn, "Y", "owner1", ttl_seconds=1) as ok1:
        assert ok1
        time.sleep(1.2)
        with acquire_lock(conn,
                          "Y",
                          "owner2",
                          ttl_seconds=1,
                          max_wait_seconds=0.2) as ok2:
            assert ok2  # Stolen after expiry
