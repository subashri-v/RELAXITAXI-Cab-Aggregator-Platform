# tests/integration/integration_test.py
import importlib
import pytest
# import mock_streamlit  <-- DELETE THIS LINE

# -------------------------------------------------------
# Mock Streamlit setup used in all integration tests
# -------------------------------------------------------
@pytest.fixture(autouse=True)
def setup_mocks(monkeypatch, mock_streamlit):  # <-- ADD the fixture as an argument
    """
    This autouse fixture now activates the 'mock_streamlit' fixture
    from conftest.py for every test in this file.

    That fixture handles patching 'sys.modules' with a *fresh*
    mock object for each test, which solves the mock state leakage.
    """
    # The 'mock_streamlit' fixture from conftest.py already handles
    # all the patching, so we can just 'pass' here.
    pass


# -------------------------------------------------------
# Test 1: No active ride requests
# -------------------------------------------------------
def test_no_active_request(monkeypatch):
    import streamlit as st
    st.session_state.clear()
    st.session_state["role"] = "driver"
    st.session_state["booking"] = None

    # Act
    from src.pages import driver_view
    importlib.reload(driver_view)
    driver_view.render_driver_view()  # ✅ trigger UI

    # Assert
    st.info.assert_called_once_with("No active ride requests. Waiting for a customer...")


# -------------------------------------------------------
# Test 2: Pending booking shown properly
# -------------------------------------------------------
def test_pending_booking(monkeypatch):
    import streamlit as st
    st.session_state.clear()
    st.session_state["role"] = "driver"
    st.session_state["booking"] = {"status": "pending", "fare": 210}
    st.session_state["distance_data"] = {
        "start_coords": [12.9716, 77.5946],
        "end_coords": [12.9352, 77.6245],
        "start": "MG Road",
        "end": "Koramangala",
    }

    # Act
    from src.pages import driver_view
    importlib.reload(driver_view)
    driver_view.render_driver_view()  # ✅ trigger UI

    # Assert
    st.subheader.assert_called_once_with("New Ride Request!")
    st.write.assert_called_once_with("Estimated Fare: ₹210.00")


# -------------------------------------------------------
# Test 3: Accepted booking with progress = 0.0
# -------------------------------------------------------
def test_active_booking(monkeypatch):
    import streamlit as st
    st.session_state.clear()
    st.session_state["role"] = "driver"
    st.session_state["booking"] = {"status": "accepted"}
    st.session_state["ride_progress"] = 0.0
    st.session_state["distance_data"] = {
        "start_coords": [12.9716, 77.5946],
        "end_coords": [12.9352, 77.6245],
        "start": "MG Road",
        "end": "Koramangala",
    }

    # Act
    from src.pages import driver_view
    importlib.reload(driver_view)
    driver_view.render_driver_view()  # ✅ trigger UI

    # Assert
    st.subheader.assert_called_once_with("On-going Ride to Koramangala")


# -------------------------------------------------------
# Test 4: Ride already in progress (>0 progress)
# -------------------------------------------------------
def test_ride_in_progress(monkeypatch):
    import streamlit as st
    st.session_state.clear()
    st.session_state["role"] = "driver"
    st.session_state["booking"] = {"status": "accepted"}
    st.session_state["ride_progress"] = 0.5
    st.session_state["distance_data"] = {
        "start_coords": [12.9716, 77.5946],
        "end_coords": [12.9352, 77.6245],
        "start": "MG Road",
        "end": "Koramangala",
    }

    # Act
    from src.pages import driver_view
    importlib.reload(driver_view)
    driver_view.render_driver_view()  # ✅ trigger UI

    # Assert
    st.info.assert_called_once_with("Ride in progress...")

# Add these 3 new tests to tests/integration/integration_test.py

def test_render_unknown_status(mock_streamlit):
    """
    Tests the fallback case for an unknown booking status.
    """
    import streamlit as st
    import importlib
    from src.pages import driver_view

    st.session_state.clear()
    st.session_state["role"] = "driver"
    st.session_state["booking"] = {"status": "teleporting"} # Unknown status
    st.session_state["distance_data"] = {}
    st.session_state["ride_progress"] = 0.0

    # Act
    importlib.reload(driver_view)
    driver_view.render_driver_view()

    # Assert
    # --- THIS IS THE FIX ---
    st.warning.assert_called_once_with("Unknown booking status: teleporting")

def test_render_accepted_missing_coords(mock_streamlit):
    """
    Tests that a warning is shown if coordinate data is missing
    on an accepted ride.
    """
    import streamlit as st
    st.session_state.clear()
    st.session_state["role"] = "driver"
    st.session_state["booking"] = {"status": "accepted"}
    st.session_state["distance_data"] = {} # Missing coords
    st.session_state["ride_progress"] = 0.5

    # Act
    from src.pages import driver_view
    importlib.reload(driver_view)
    driver_view.render_driver_view()

    # Assert
    # A warning is shown, and st.info is NOT called
    st.warning.assert_called_once_with("Coordinate data missing.")
    st.info.assert_not_called()

def test_render_ride_complete_view(mock_streamlit):
    """
    Tests the view when progress is 1.0 (ride is complete
    but not yet cleared by the main() loop).
    """
    import streamlit as st
    st.session_state.clear()
    st.session_state["role"] = "driver"
    st.session_state["booking"] = {"status": "accepted"}
    st.session_state["ride_progress"] = 1.0 # Ride is complete
    st.session_state["distance_data"] = {
        "start_coords": [12.9716, 77.5946],
        "end_coords": [12.9352, 77.6245],
        "start": "MG Road",
        "end": "Koramangala",
    }

    # Act
    from src.pages import driver_view
    importlib.reload(driver_view)
    driver_view.render_driver_view()

    # Assert
    # No info message should be shown (it hits the `else: pass`)
    st.info.assert_not_called()
    st.progress.assert_called_once_with(1.0) # Progress bar is full

# Add this function to tests/integration/integration_test.py

def test_render_pending_missing_coords(mock_streamlit):
    """
    Tests that st.map() is NOT called if coords are missing
    on the pending screen.
    """
    import streamlit as st
    st.session_state.clear()
    st.session_state["role"] = "driver"
    st.session_state["booking"] = {"status": "pending", "fare": 100}
    st.session_state["distance_data"] = {} # Missing coords
    st.session_state["ride_progress"] = 0.0

    # Act
    from src.pages import driver_view
    importlib.reload(driver_view)
    driver_view.render_driver_view()

    # Assert
    # Page should render, but the map should not
    st.subheader.assert_called_once_with("New Ride Request!")
    st.map.assert_not_called()