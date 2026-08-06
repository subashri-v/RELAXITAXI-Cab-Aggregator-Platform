from datetime import datetime, timedelta

import pytest
from unittest.mock import patch, MagicMock
import src.db_utils as db


# ---- PASSWORD HASHING ----
def test_hash_password():
    hashed = db.hash_password("test123")
    assert hashed != "test123"
    assert hashed.startswith("$2b$")  # bcrypt hash prefix
    assert db.bcrypt.checkpw(b"test123", hashed.encode())


# ---- AUTHENTICATION ----
@patch("src.db_utils.get_connection")
def test_authenticate_user_success(mock_conn):
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur

    # Mock returned row, with a real bcrypt hash for the correct password
    stored_hash = db.hash_password("pass")
    cur.fetchone.return_value = {"id": 1, "email": "a@b.com", "password": stored_hash}

    mock_conn.return_value = conn

    result = db.authenticate_user("riders", "a@b.com", "pass")
    assert result == {"id": 1, "email": "a@b.com", "password": stored_hash}
    cur.execute.assert_called()


@patch("src.db_utils.get_connection")
def test_authenticate_user_failure(mock_conn):
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    cur.fetchone.return_value = None
    mock_conn.return_value = conn

    result = db.authenticate_user("drivers", "x@y.com", "badpass")
    assert result is None


def test_authenticate_invalid_user_type():
    with pytest.raises(ValueError):
        db.authenticate_user("invalid", "a@b.com", "123")


# ---- REGISTER USER ----
@patch("src.db_utils.get_connection")
def test_register_user_rider_success(mock_conn):
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    mock_conn.return_value = conn

    cur.execute.return_value = None

    result = db.register_user("riders", "John", "john@x.com", "123")
    assert result is True
    conn.commit.assert_called()


@patch("src.db_utils.get_connection")
def test_register_user_driver_success(mock_conn):
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    mock_conn.return_value = conn

    result = db.register_user("drivers", "D", "d@x.com", "123", "KA01", "LIC123")
    assert result is True


@patch("src.db_utils.get_connection")
def test_register_user_duplicate_email(mock_conn):
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    mock_conn.return_value = conn

    # Simulate duplicate email
    cur.execute.side_effect = db.sqlite3.IntegrityError()

    result = db.register_user("riders", "John", "john@x.com", "123")
    assert result is False


def test_register_user_invalid_type():
    with pytest.raises(ValueError):
        db.register_user("xx", "N", "e@x.com", "123")


# ---- ADD RIDE ----
@patch("src.db_utils.get_connection")
def test_add_ride(mock_conn):
    conn = MagicMock()
    cur = MagicMock()
    mock_conn.return_value = conn
    conn.cursor.return_value = cur

    cur.lastrowid = 999

    ride_id = db.add_ride(
        rider_id=1,
        start="A",
        end="B",
        start_coords=(12.9, 77.6),
        end_coords=(13.0, 77.7),
        distance_km=10.5,
        fare=200,
        ac=True,
        driver_id=5
    )

    assert ride_id == 999
    cur.execute.assert_called()
    conn.commit.assert_called()


# ---- ACCEPT RIDE ----
@patch("src.db_utils.get_connection")
def test_accept_ride(mock_conn):
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    mock_conn.return_value = conn

    db.accept_ride(1, 10)
    cur.execute.assert_called()


# ---- UPDATE RIDE STATUS ----
@patch("src.db_utils.get_connection")
def test_update_ride_status(mock_conn):
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    mock_conn.return_value = conn

    db.update_ride_status(1, "completed")
    cur.execute.assert_called()


# ---- HISTORY ----
@patch("src.db_utils.get_connection")
def test_get_rider_history(mock_conn):
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    mock_conn.return_value = conn

    # Fake rows
    cur.fetchall.return_value = [
        {"id": 1, "start": "A"},
        {"id": 2, "start": "B"}
    ]

    history = db.get_rider_history(1)
    assert isinstance(history, list)
    assert len(history) == 2


@patch("src.db_utils.get_connection")
def test_get_driver_history(mock_conn):
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    mock_conn.return_value = conn

    cur.fetchall.return_value = [{"id": 11}, {"id": 12}]

    history = db.get_driver_history(5)
    assert len(history) == 2


# ---- GET USER BY EMAIL ----
@patch("src.db_utils.get_connection")
def test_get_user_by_email_success(mock_conn):
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    mock_conn.return_value = conn
    cur.fetchone.return_value = {"email": "test@x.com"}

    user = db.get_user_by_email("riders", "test@x.com")
    assert user == {"email": "test@x.com"}


@patch("src.db_utils.get_connection")
def test_get_user_by_email_none(mock_conn):
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    mock_conn.return_value = conn
    cur.fetchone.return_value = None

    user = db.get_user_by_email("drivers", "no@x.com")
    assert user is None


# ---- RIDE LOCKING (uses a real temp SQLite file: the guarantee being
# tested is SQLite's atomic UPDATE, which a mocked connection can't prove) ----
def _make_pending_ride(tmp_path, monkeypatch, name):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / name))
    db.init_db()
    return db.add_ride(
        rider_id=1, start="A", end="B",
        start_coords=(12.9, 77.6), end_coords=(13.0, 77.7),
        distance_km=5.0, fare=100.0, ac=True,
    )


def test_try_lock_ride_race_condition(tmp_path, monkeypatch):
    """Two drivers claiming the same ride at once: exactly one should win."""
    ride_id = _make_pending_ride(tmp_path, monkeypatch, "race_test.db")

    first_claim = db.try_lock_ride(ride_id)
    second_claim = db.try_lock_ride(ride_id)

    assert first_claim is True
    assert second_claim is False

    conn = db.get_connection()
    row = conn.execute("SELECT status FROM rides WHERE id=?", (ride_id,)).fetchone()
    conn.close()
    assert row["status"] == "locked_by_driver"


def test_reclaim_stale_locks_releases_abandoned_ride(tmp_path, monkeypatch):
    """A lock older than LOCK_TIMEOUT_SECONDS is released back to 'pending'."""
    ride_id = _make_pending_ride(tmp_path, monkeypatch, "stale_test.db")
    assert db.try_lock_ride(ride_id) is True

    stale_time = (datetime.now() - timedelta(seconds=db.LOCK_TIMEOUT_SECONDS + 5)).isoformat()
    conn = db.get_connection()
    conn.execute("UPDATE rides SET locked_at=? WHERE id=?", (stale_time, ride_id))
    conn.commit()
    conn.close()

    db.reclaim_stale_locks()

    conn = db.get_connection()
    row = conn.execute("SELECT status FROM rides WHERE id=?", (ride_id,)).fetchone()
    conn.close()
    assert row["status"] == "pending"


def test_reclaim_stale_locks_keeps_fresh_lock(tmp_path, monkeypatch):
    """A lock claimed just now must NOT be released early."""
    ride_id = _make_pending_ride(tmp_path, monkeypatch, "fresh_test.db")
    assert db.try_lock_ride(ride_id) is True

    db.reclaim_stale_locks()

    conn = db.get_connection()
    row = conn.execute("SELECT status FROM rides WHERE id=?", (ride_id,)).fetchone()
    conn.close()
    assert row["status"] == "locked_by_driver"
