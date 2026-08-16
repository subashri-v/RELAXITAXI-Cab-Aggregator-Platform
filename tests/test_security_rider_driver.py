import bcrypt
import pytest
from src import db_utils
from src.db_utils import (
    authenticate_user,
    register_user,
    hash_password,
)


@pytest.fixture(scope="function", autouse=True)
def clean_db(tmp_path, monkeypatch):
    """Point DB_PATH at an isolated temp file so tests never touch the real relaxitaxi.db."""
    monkeypatch.setattr(db_utils, "DB_PATH", str(tmp_path / "test_relaxitaxi.db"))
    db_utils.init_db()
    yield


def test_password_hashing_not_plain_text():
    password = "secret123"
    hashed = hash_password(password)

    assert hashed != password  # must not store plaintext
    assert hashed.startswith("$2b$")  # bcrypt hash prefix


def test_password_hash_is_consistent():
    # bcrypt salts each hash differently, so equal passwords produce
    # different hashes -- what must stay consistent is verification.
    p1 = hash_password("mypassword")
    p2 = hash_password("mypassword")
    assert p1 != p2  # salted, so not equal
    assert bcrypt.checkpw(b"mypassword", p1.encode())
    assert bcrypt.checkpw(b"mypassword", p2.encode())


def test_correct_login_security():
    register_user("riders", "Alice", "alice@rt.com", "pass123")

    user = authenticate_user("riders", "alice@rt.com", "pass123")
    assert user is not None
    assert user["email"] == "alice@rt.com"


def test_wrong_password_fails_login():
    register_user("drivers", "Bob", "bob@rt.com", "driver123")

    user = authenticate_user("drivers", "bob@rt.com", "wrongpass")
    assert user is None  # must not log in


def test_sql_injection_attempt_blocked():
    """Ensure SQL injection does not bypass login."""

    register_user("riders", "Eve", "eve@rt.com", "mypwd")

    malicious_input = "' OR 1=1 --"

    user = authenticate_user("riders", "eve@rt.com", malicious_input)
    assert user is None  # should NOT log in
