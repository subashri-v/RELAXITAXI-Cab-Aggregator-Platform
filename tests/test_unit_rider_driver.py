import pytest
from src.db_utils import register_user, authenticate_user, hash_password

import os
from src.db_utils import init_db, DB_PATH

@pytest.fixture(scope="function", autouse=True)
def clean_db():
    """Reset DB before running unit tests."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
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
