"""Page-level tests that run the real Streamlit scripts with streamlit.testing's AppTest.

The pages are top-level scripts (not importable functions), so AppTest is the
way to execute them for real: widgets, forms, session_state and st.switch_page
all behave like Streamlit, only without a browser.
"""
import os
import sys
import time
from unittest.mock import patch

import pytest
from streamlit.runtime.scriptrunner import StopException
from streamlit.testing.v1 import AppTest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
PAGES_DIR = os.path.join(SRC_DIR, "pages")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import db_utils  # noqa: E402  (top-level module, as the pages import it)
import session_utils  # noqa: E402


# Raised from a patched time.sleep to end a page's poll-and-rerun loop, exactly
# like st.stop() would: Streamlit swallows it and the script run ends cleanly.
def _stop_sleep(_seconds):
    """time.sleep stand-in: ends the script run when a page calls it, but leaves
    AppTest's own polling sleeps (called from outside src/) alone."""
    caller = sys._getframe(1).f_code.co_filename  # pylint: disable=protected-access
    if os.path.abspath(caller).startswith(SRC_DIR):
        raise StopException


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db_utils, "DB_PATH", str(tmp_path / "pages.db"))
    db_utils.init_db()


@pytest.fixture(autouse=True)
def goto_calls(monkeypatch):
    """st.switch_page can't resolve targets under AppTest, so record goto() calls instead."""
    calls = []
    monkeypatch.setattr(session_utils, "goto", calls.append)
    return calls


def _page(name):
    return AppTest.from_file(os.path.join(PAGES_DIR, name), default_timeout=30)


def _login_as(at, role, user_id, name="Test"):
    at.session_state["role"] = role
    at.session_state["user_id"] = user_id
    at.session_state["user_name"] = name


def _make_rider(email="r@x.com"):
    db_utils.register_user("riders", "Rita", email, "pw")
    return db_utils.authenticate_user("riders", email, "pw")["id"]


def _make_driver(email="d@x.com"):
    db_utils.register_user("drivers", "Dev", email, "pw", vehicle_no="KA01", license_no="L1")
    return db_utils.authenticate_user("drivers", email, "pw")["id"]


def _make_ride(rider_id, **overrides):
    args = dict(
        rider_id=rider_id, start="A", end="B",
        start_coords=(12.9, 77.5), end_coords=(13.0, 77.6),
        distance_km=10.0, fare=250.0, ac=True, driver_id=None,
    )
    args.update(overrides)
    return db_utils.add_ride(**args)


def _texts(elements):
    return " ".join(str(e.value) for e in elements)


# ---------------------------------------------------------------- app.py
def test_landing_page_renders_role_buttons():
    at = AppTest.from_file(os.path.join(SRC_DIR, "app.py"), default_timeout=30).run()
    assert not at.exception
    assert [b.label for b in at.button] == ["I'm a Customer", "I'm a Driver"]


@pytest.mark.parametrize("index,role", [(0, "customer"), (1, "driver")])
def test_landing_page_role_selection(index, role, goto_calls):
    at = AppTest.from_file(os.path.join(SRC_DIR, "app.py"), default_timeout=30).run()
    at.button[index].click().run()
    assert at.session_state["role"] == role
    assert goto_calls[-1] == f"pages/{'rider' if role == 'customer' else 'driver'}_login.py"


# ---------------------------------------------------------- rider login
def test_rider_login_success():
    _make_rider()
    at = _page("rider_login.py").run()
    at.text_input[0].set_value("r@x.com")
    at.text_input[1].set_value("pw")
    at.button[0].click().run()
    assert at.session_state["role"] == "customer"
    assert at.session_state["user_name"] == "Rita"


def test_rider_login_invalid_credentials():
    at = _page("rider_login.py").run()
    at.text_input[0].set_value("nobody@x.com")
    at.text_input[1].set_value("bad")
    at.button[0].click().run()
    assert "Invalid credentials" in _texts(at.error)
    assert at.session_state["role"] is None


def test_rider_login_navigation_buttons(goto_calls):
    at = _page("rider_login.py").run()
    labels = [b.label for b in at.button]
    at.button[labels.index("Logout")].click().run()
    assert goto_calls[-1] == "app.py"
    at = _page("rider_login.py").run()
    at.button[labels.index("Don't have an account? Register")].click().run()
    assert goto_calls[-1] == "pages/rider_register.py"


# ------------------------------------------------------- rider register
def test_rider_register_success_and_duplicate():
    at = _page("rider_register.py").run()
    at.text_input[0].set_value("Rita")
    at.text_input[1].set_value("new@x.com")
    at.text_input[2].set_value("pw")
    at.button[0].click().run()
    assert "Registration successful" in _texts(at.success)
    assert db_utils.authenticate_user("riders", "new@x.com", "pw")


def test_rider_register_missing_fields():
    at = _page("rider_register.py").run()
    at.text_input[0].set_value("Rita")
    at.button[0].click().run()
    assert "fill in all fields" in _texts(at.warning)


def test_rider_register_reports_db_error():
    at = _page("rider_register.py").run()
    for i, val in enumerate(["Rita", "e@x.com", "pw"]):
        at.text_input[i].set_value(val)
    with patch("db_utils.register_user", side_effect=RuntimeError("boom")):
        at.button[0].click().run()
    assert "boom" in _texts(at.error)


def test_rider_register_login_button(goto_calls):
    at = _page("rider_register.py").run()
    at.button[-1].click().run()
    assert goto_calls[-1] == "pages/rider_login.py"


# --------------------------------------------------------- driver login
def test_driver_login_success():
    _make_driver()
    at = _page("driver_login.py").run()
    at.text_input[0].set_value("d@x.com")
    at.text_input[1].set_value("pw")
    at.button[0].click().run()
    assert at.session_state["role"] == "driver"
    assert at.session_state["user_name"] == "Dev"


def test_driver_login_empty_fields_warns():
    at = _page("driver_login.py").run()
    at.button[0].click().run()
    assert "both email and password" in _texts(at.warning)


def test_driver_login_invalid_credentials():
    at = _page("driver_login.py").run()
    at.text_input[0].set_value("x@x.com")
    at.text_input[1].set_value("bad")
    at.button[0].click().run()
    assert "Invalid credentials" in _texts(at.error)


def test_driver_login_register_button(goto_calls):
    at = _page("driver_login.py").run()
    at.button[-1].click().run()
    assert goto_calls[-1] == "pages/driver_register.py"


# ------------------------------------------------------ driver register
def _fill_driver_form(at, values):
    for i, val in enumerate(values):
        at.text_input[i].set_value(val)


def test_driver_register_success_then_go_to_login():
    at = _page("driver_register.py").run()
    _fill_driver_form(at, ["Dev", "dev@x.com", "pw", "KA01", "L1"])
    at.button[0].click().run()
    assert "Registration successful" in _texts(at.success)
    at.button[0].click().run()  # "Go to Login"
    assert at.session_state["registration_success"] is False


def test_driver_register_missing_fields():
    at = _page("driver_register.py").run()
    _fill_driver_form(at, ["Dev", "", "pw", "KA01", "L1"])
    at.button[0].click().run()
    assert "fill in all fields" in _texts(at.warning)


def test_driver_register_duplicate_email_fails():
    _make_driver("dup@x.com")
    at = _page("driver_register.py").run()
    _fill_driver_form(at, ["Dev", "dup@x.com", "pw", "KA02", "L2"])
    at.button[0].click().run()
    assert "Registration failed" in _texts(at.error)


# -------------------------------------------------------- rider history
def test_rider_history_requires_login():
    at = _page("rider_history.py").run()
    assert "log in as a rider" in _texts(at.error)


def test_rider_history_empty():
    at = _page("rider_history.py")
    _login_as(at, "customer", _make_rider())
    at.run()
    assert "No rides found" in _texts(at.info)


def test_rider_history_with_rides_and_book_button(goto_calls):
    rider = _make_rider()
    _make_ride(rider)
    at = _page("rider_history.py")
    _login_as(at, "customer", rider)
    at.run()
    assert len(at.dataframe) == 1
    at.button[0].click().run()
    assert goto_calls[-1] == "pages/book_ride.py"


# ------------------------------------------------------- driver history
def test_driver_history_requires_driver_role(goto_calls):
    at = _page("driver_history.py").run()
    assert "logged in as a driver" in _texts(at.error)
    at.button[0].click().run()  # "Go to Login"
    assert goto_calls[-1] == "pages/driver_login.py"


def test_driver_history_empty_and_navigation(goto_calls):
    at = _page("driver_history.py")
    _login_as(at, "driver", _make_driver())
    at.run()
    assert "No rides found" in _texts(at.info)
    labels = [b.label for b in at.button]
    at.button[labels.index("Back To Driver View")].click().run()
    assert goto_calls[-1] == "pages/driver_view.py"


def test_driver_history_lists_rides_and_sign_out():
    rider, driver = _make_rider(), _make_driver()
    ride_id = _make_ride(rider)
    db_utils.accept_ride(ride_id, driver, "Dev")
    at = _page("driver_history.py")
    _login_as(at, "driver", driver)
    at.run()
    assert len(at.dataframe) == 1
    labels = [b.label for b in at.button]
    at.button[labels.index("Sign Out")].click().run()
    assert at.session_state["role"] is None


# ------------------------------------------------------------ book_ride
def test_book_ride_requires_customer_login(goto_calls):
    at = _page("book_ride.py").run()
    assert "log in as a customer" in _texts(at.error)
    at.button[0].click().run()  # "Go to Login"
    assert goto_calls[-1] == "app.py"


def test_book_ride_navigation_buttons(goto_calls):
    at = _page("book_ride.py")
    _login_as(at, "customer", _make_rider())
    at.run()
    labels = [b.label for b in at.button]
    at.button[labels.index("Ride History")].click().run()
    assert goto_calls[-1] == "pages/rider_history.py"
    at = _page("book_ride.py")
    _login_as(at, "customer", 1)
    at.run()
    at.button[labels.index("Sign Out")].click().run()
    assert at.session_state["role"] is None


def test_book_ride_search_shows_fares_and_books_ac():
    rider = _make_rider()
    at = _page("book_ride.py")
    _login_as(at, "customer", rider)
    at.run()
    with patch("ride_utils.get_coordinates", side_effect=[(12.9, 77.5), (13.0, 77.6)]), \
            patch("time.sleep", _stop_sleep):
        labels = [b.label for b in at.button]
        at.button[labels.index("Search Rides")].click().run()
        assert "Distance between" in _texts(at.success)
        labels = [b.label for b in at.button]
        at.button[labels.index("Book AC")].click().run()
    ride = db_utils.get_active_ride_for_rider(rider)
    assert ride is not None and ride["ac"]


def test_book_ride_books_non_ac():
    rider = _make_rider()
    at = _page("book_ride.py")
    _login_as(at, "customer", rider)
    at.run()
    with patch("ride_utils.get_coordinates", side_effect=[(12.9, 77.5), (13.0, 77.6)]), \
            patch("time.sleep", _stop_sleep):
        labels = [b.label for b in at.button]
        at.button[labels.index("Search Rides")].click().run()
        labels = [b.label for b in at.button]
        at.button[labels.index("Book Non-AC")].click().run()
    ride = db_utils.get_active_ride_for_rider(rider)
    assert ride is not None and not ride["ac"]


def test_book_ride_search_bad_location_shows_error():
    at = _page("book_ride.py")
    _login_as(at, "customer", _make_rider())
    at.run()
    with patch("ride_utils.get_coordinates", side_effect=ValueError("Location not found")):
        labels = [b.label for b in at.button]
        at.button[labels.index("Search Rides")].click().run()
    assert "Location not found" in _texts(at.error)


def test_book_ride_shows_waiting_message_for_pending_ride():
    rider = _make_rider()
    _make_ride(rider)
    at = _page("book_ride.py")
    _login_as(at, "customer", rider)
    with patch("time.sleep", _stop_sleep):
        at.run()
    assert "Waiting for a driver" in _texts(at.info)


def test_book_ride_shows_accepted_ride_and_track_button(goto_calls):
    rider, driver = _make_rider(), _make_driver()
    ride_id = _make_ride(rider)
    db_utils.accept_ride(ride_id, driver, "Dev")
    at = _page("book_ride.py")
    _login_as(at, "customer", rider)
    at.run()
    assert "booked" in _texts(at.success)
    labels = [b.label for b in at.button]
    at.button[labels.index("📍 Track Your Ride")].click().run()
    assert goto_calls[-1] == "pages/track_ride.py"


# ----------------------------------------------------------- track_ride
def _accepted_ride(progress=None):
    rider, driver = _make_rider(), _make_driver()
    ride_id = _make_ride(rider)
    db_utils.accept_ride(ride_id, driver, "Dev")
    if progress is not None:
        db_utils.update_ride_progress(ride_id, progress)
    return rider, ride_id


def test_track_ride_requires_customer_login(goto_calls):
    at = _page("track_ride.py").run()
    assert "logged in as a customer" in _texts(at.error)
    at.button[0].click().run()
    assert goto_calls[-1] == "app.py"


def test_track_ride_without_active_ride_redirects_to_payment(goto_calls):
    at = _page("track_ride.py")
    _login_as(at, "customer", _make_rider())
    at.run()
    assert goto_calls[-1] == "pages/payment_ui.py"


def test_track_ride_pending_shows_waiting():
    rider = _make_rider()
    _make_ride(rider)
    at = _page("track_ride.py")
    _login_as(at, "customer", rider)
    with patch("time.sleep", _stop_sleep):
        at.run()
    assert "Waiting for a driver" in _texts(at.info)


def test_track_ride_at_pickup_shows_details_and_can_cancel():
    rider, ride_id = _accepted_ride()
    at = _page("track_ride.py")
    _login_as(at, "customer", rider)
    with patch("time.sleep", _stop_sleep):
        at.run()
    assert "Tracking" in _texts(at.info)
    assert "on the way to pick you up" in _texts(at.markdown)
    labels = [b.label for b in at.button]
    with patch("time.sleep", _stop_sleep):
        at.button[labels.index("🚫 Cancel Ride")].click().run()
    assert db_utils.get_ride_by_id(ride_id)["status"] == "cancelled"


def test_track_ride_in_progress_message():
    rider, _ = _accepted_ride(progress=0.5)
    at = _page("track_ride.py")
    _login_as(at, "customer", rider)
    with patch("time.sleep", _stop_sleep):
        at.run()
    assert "Ride in progress" in _texts(at.markdown)


def test_track_ride_completion_marks_ride_completed():
    rider, ride_id = _accepted_ride(progress=1.0)
    at = _page("track_ride.py")
    _login_as(at, "customer", rider)
    with patch("time.sleep", _stop_sleep):
        at.run()
    assert "Ride Completed" in _texts(at.success)
    assert db_utils.get_ride_by_id(ride_id)["status"] == "completed"


def test_track_ride_update_route_success():
    rider, ride_id = _accepted_ride()
    at = _page("track_ride.py")
    _login_as(at, "customer", rider)
    with patch("time.sleep", _stop_sleep):
        at.run()
    fake = type("Loc", (), {"latitude": 12.95, "longitude": 77.55})
    with patch("geopy.geocoders.Nominatim.geocode", return_value=fake), \
            patch("time.sleep", _stop_sleep):
        labels = [b.label for b in at.button]
        at.button[labels.index("Update Locations")].click().run()
    ride = db_utils.get_ride_by_id(ride_id)
    assert (ride["start_lat"], ride["start_lon"]) == (12.95, 77.55)
    assert ride["fare"] != 250.0


def test_track_ride_update_route_unknown_location_shows_error():
    rider, _ = _accepted_ride()
    at = _page("track_ride.py")
    _login_as(at, "customer", rider)
    with patch("time.sleep", _stop_sleep):
        at.run()
    with patch("geopy.geocoders.Nominatim.geocode", return_value=None), \
            patch("time.sleep", _stop_sleep):
        labels = [b.label for b in at.button]
        at.button[labels.index("Update Locations")].click().run()
    assert "Could not find" in _texts(at.error)


def test_track_ride_sign_out():
    rider, _ = _accepted_ride()
    at = _page("track_ride.py")
    _login_as(at, "customer", rider)
    with patch("time.sleep", _stop_sleep):
        at.run()
        labels = [b.label for b in at.button]
        at.button[labels.index("Sign Out")].click().run()
    assert at.session_state["role"] is None


# ----------------------------------------------------------- driver_view
def test_driver_view_requires_driver_role(goto_calls):
    at = _page("driver_view.py").run()
    assert "logged in as a driver" in _texts(at.error)
    at.button[0].click().run()
    assert goto_calls[-1] == "app.py"


def test_driver_view_deferred_sign_out_redirects_home(goto_calls):
    at = _page("driver_view.py")
    _login_as(at, "driver", _make_driver())
    at.session_state["_signed_out"] = True
    at.run()
    assert goto_calls[-1] == "app.py"


def test_driver_view_waits_when_no_rides():
    at = _page("driver_view.py")
    _login_as(at, "driver", _make_driver())
    with patch("time.sleep", _stop_sleep):
        at.run()
    assert "No active ride requests" in _texts(at.info)


def test_driver_view_claims_pending_ride():
    rider, driver = _make_rider(), _make_driver()
    ride_id = _make_ride(rider)
    at = _page("driver_view.py")
    _login_as(at, "driver", driver)
    with patch("time.sleep", _stop_sleep):
        at.run()
    assert db_utils.get_ride_by_id(ride_id)["status"] == "locked_by_driver"
    assert at.session_state["booking"]["ride_id"] == ride_id


def test_driver_view_resumes_accepted_ride():
    rider, driver = _make_rider(), _make_driver()
    ride_id = _make_ride(rider)
    db_utils.accept_ride(ride_id, driver, "Dev")
    at = _page("driver_view.py")
    _login_as(at, "driver", driver)
    with patch("time.sleep", _stop_sleep):
        at.run()
    assert at.session_state["booking"]["status"] == "accepted"
    assert not at.exception


def test_driver_view_syncs_fare_changed_by_rider():
    rider, driver = _make_rider(), _make_driver()
    ride_id = _make_ride(rider)
    db_utils.accept_ride(ride_id, driver, "Dev")
    at = _page("driver_view.py")
    _login_as(at, "driver", driver)
    with patch("time.sleep", _stop_sleep):
        at.run()
        db_utils.update_ride_route(ride_id, {
            "start": "A", "end": "C", "start_coords": (12.9, 77.5),
            "end_coords": (13.1, 77.7), "distance_km": 20.0, "fare": 480.0,
        })
        at.run()
    assert at.session_state["booking"]["fare"] == 480.0


def test_driver_view_shows_recent_cancel_message():
    at = _page("driver_view.py")
    _login_as(at, "driver", _make_driver())
    at.session_state["_cancelled_ride"] = True
    at.session_state["_cancel_time"] = time.time()
    at.run()
    assert "cancelled successfully" in _texts(at.warning)


def test_driver_view_clears_expired_cancel_message():
    at = _page("driver_view.py")
    _login_as(at, "driver", _make_driver())
    at.session_state["_cancelled_ride"] = True
    at.session_state["_cancel_time"] = time.time() - 60
    with patch("time.sleep", _stop_sleep):
        at.run()
    assert "_cancelled_ride" not in at.session_state


def test_driver_view_completed_ride_message_is_cleared():
    at = _page("driver_view.py")
    _login_as(at, "driver", _make_driver())
    at.session_state["_completed_ride"] = True
    with patch("time.sleep", _stop_sleep):
        at.run()
    assert not at.exception


def test_driver_view_history_button(goto_calls):
    at = _page("driver_view.py")
    _login_as(at, "driver", _make_driver())
    with patch("time.sleep", _stop_sleep):
        at.run()
        labels = [b.label for b in at.button]
        at.button[labels.index("Driver Ride History")].click().run()
    assert goto_calls[-1] == "pages/driver_history.py"
