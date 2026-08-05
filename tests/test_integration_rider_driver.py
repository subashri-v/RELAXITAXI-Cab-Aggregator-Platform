import os
import pytest
from src.db_utils import (
    init_db,
    register_user,
    authenticate_user,
    get_connection,
    DB_PATH
)


@pytest.fixture(scope="function", autouse=True)
def clean_db():
    """Reset DB before running integration tests."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    yield


def test_rider_registration_and_login():
    # Register rider
    success = register_user(
        user_type="riders",
        name="RiderTest",
        email="rider@test.com",
        password="rider123"
    )
    assert success is True

    # Login rider
    user = authenticate_user("riders", "rider@test.com", "rider123")
    assert user is not None
    assert user["name"] == "RiderTest"
    assert user["email"] == "rider@test.com"


def test_driver_registration_and_login():
    # Register driver
    success = register_user(
        user_type="drivers",
        name="DriverTest",
        email="driver@test.com",
        password="driver123",
        vehicle_no="KA01AB1234",
        license_no="DL12345"
    )
    assert success is True

    # Login driver
    user = authenticate_user("drivers", "driver@test.com", "driver123")
    assert user is not None
    assert user["name"] == "DriverTest"
    assert user["vehicle_no"] == "KA01AB1234"


def test_duplicate_registration_fails():
    """Ensure registering same email twice fails."""

    success1 = register_user(
        "riders", "R1", "duprider@test.com", "pwd"
    )
    success2 = register_user(
        "riders", "R2", "duprider@test.com", "pwd2"
    )

    assert success1 is True
    assert success2 is False  # UNIQUE constraint prevents duplicate email


def test_login_non_existing_user():
    """Ensure login fails for non-existing user."""
    user = authenticate_user("riders", "nonexistent@test.com", "abc123")
    assert user is None
