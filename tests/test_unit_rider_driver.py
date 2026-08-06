import pytest
from src import db_utils
from src.db_utils import register_user, authenticate_user

@pytest.fixture(scope="function", autouse=True)
def clean_db(tmp_path, monkeypatch):
    """Point DB_PATH at an isolated temp file so tests never touch the real relaxitaxi.db."""
    monkeypatch.setattr(db_utils, "DB_PATH", str(tmp_path / "test_relaxitaxi.db"))
    db_utils.init_db()
    yield

def test_register_rider_success():
    result = register_user(
        user_type="riders",
        name="Test Rider",
        email="test_rider@example.com",
        password="12345"
    )
    assert result is True

def test_register_driver_success():
    result = register_user(
        user_type="drivers",
        name="Test Driver",
        email="driver@example.com",
        password="12345",
        vehicle_no="KA01AB1234",
        license_no="LIC123"
    )
    assert result is True

def test_register_invalid_user_type():
    with pytest.raises(ValueError):
        register_user("invalid", "name", "email", "pass")

def test_authentication_success():
    register_user("riders", "Auth User", "auth@example.com", "pass123")
    user = authenticate_user("riders", "auth@example.com", "pass123")
    assert user is not None
    assert user["email"] == "auth@example.com"

def test_authentication_fail():
    user = authenticate_user("riders", "doesnotexist@example.com", "wrongpass")
    assert user is None
