"""Extra db_utils coverage: ride lookup helpers, stale-lock reclaiming, user lookups."""
import pytest

from src import db_utils


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db_utils, "DB_PATH", str(tmp_path / "extra.db"))
    db_utils.init_db()


def _rider_and_driver():
    db_utils.register_user("riders", "Rita", "r@x.com", "pw")
    db_utils.register_user("drivers", "Dev", "d@x.com", "pw", vehicle_no="KA01", license_no="L1")
    return (db_utils.get_user_by_email("riders", "r@x.com")["id"],
            db_utils.get_user_by_email("drivers", "d@x.com")["id"])


def _ride(rider_id):
    return db_utils.add_ride(rider_id, "A", "B", (12.9, 77.5), (13.0, 77.6), 10.0, 250.0, True)


def test_get_pending_ride_returns_oldest_first():
    rider, _ = _rider_and_driver()
    first, _second = _ride(rider), _ride(rider)
    assert db_utils.get_pending_ride()["id"] == first


def test_get_pending_ride_none_when_queue_empty():
    assert db_utils.get_pending_ride() is None


def test_stale_lock_is_reclaimed_to_pending(monkeypatch):
    rider, _ = _rider_and_driver()
    ride_id = _ride(rider)
    assert db_utils.try_lock_ride(ride_id) is True
    assert db_utils.get_ride_by_id(ride_id)["status"] == "locked_by_driver"

    monkeypatch.setattr(db_utils, "LOCK_TIMEOUT_SECONDS", -1)  # every lock is now stale
    assert db_utils.get_pending_ride()["id"] == ride_id
    assert db_utils.get_ride_by_id(ride_id)["status"] == "pending"


def test_fresh_lock_is_not_reclaimed():
    rider, _ = _rider_and_driver()
    ride_id = _ride(rider)
    db_utils.try_lock_ride(ride_id)
    assert db_utils.get_pending_ride() is None
    assert db_utils.get_ride_by_id(ride_id)["status"] == "locked_by_driver"


def test_get_active_ride_for_driver():
    rider, driver = _rider_and_driver()
    assert db_utils.get_active_ride_for_driver(driver) is None
    ride_id = _ride(rider)
    db_utils.accept_ride(ride_id, driver, "Dev")
    assert db_utils.get_active_ride_for_driver(driver)["id"] == ride_id


def test_get_ride_by_id_missing_returns_none():
    assert db_utils.get_ride_by_id(9999) is None


def test_user_lookup_by_email_and_id():
    rider, _ = _rider_and_driver()
    assert db_utils.get_user_by_email("riders", "nobody@x.com") is None
    assert db_utils.get_user_by_id("riders", rider)["email"] == "r@x.com"
    assert db_utils.get_user_by_id("riders", 9999) is None


@pytest.mark.parametrize("func,args", [
    (db_utils.get_user_by_email, ("admins", "a@x.com")),
    (db_utils.get_user_by_id, ("admins", 1)),
])
def test_user_lookup_rejects_unknown_table(func, args):
    with pytest.raises(ValueError):
        func(*args)
