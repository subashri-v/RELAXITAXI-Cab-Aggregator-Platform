"""
Unit Tests for `driver_view.py`

These tests focus on the business logic in the 'handle_' functions.
"""

import pytest
import time
from unittest.mock import MagicMock

# Import the functions to test
# We import them directly, NOT the whole file
from src.pages.driver_view import (
    handle_accept_ride,
    handle_reject_ride,
    handle_move_forward,
    handle_complete_ride,
    handle_cancel_ride,
    handle_logout
)

def test_handle_accept_ride(mock_streamlit, mocker):
    """Tests that accepting a ride persists to the DB and updates local state."""
    # Arrange
    st = mock_streamlit
    st.session_state["booking"] = {'status': 'pending', 'ride_id': 42}
    st.session_state["user_id"] = 7
    st.session_state["user_name"] = "You (Driver)"

    mock_accept_ride = mocker.patch('src.pages.driver_view.db_utils.accept_ride')

    # Act
    handle_accept_ride(st)

    # Assert
    # Check that the DB was updated with the right ride/driver info
    mock_accept_ride.assert_called_once_with(ride_id=42, driver_id=7, driver_name="You (Driver)")

    # Check that the local state was updated to match
    assert st.session_state["booking"]['status'] == 'accepted'
    assert st.session_state["booking"]['driver'] == "You (Driver)"

def test_handle_reject_ride(mock_streamlit, mocker):
    """Tests that rejecting a ride persists to the DB and clears local state."""
    # Arrange
    st = mock_streamlit
    st.session_state["booking"] = {'status': 'pending', 'ride_id': 42}
    st.session_state["distance_data"] = {'start': 'A', 'end': 'B'}

    mock_update_status = mocker.patch('src.pages.driver_view.db_utils.update_ride_status')

    # Act
    handle_reject_ride(st)

    # Assert
    mock_update_status.assert_called_once_with(42, "rejected")

    # Check that local state was cleared
    assert st.session_state["booking"] is None
    assert st.session_state["distance_data"] is None

def test_handle_move_forward(mock_streamlit, mocker):
    """Tests that moving forward increments progress and persists it."""
    # Arrange
    st = mock_streamlit
    st.session_state["ride_progress"] = 0.25
    st.session_state["booking"] = {'status': 'accepted', 'ride_id': 42}

    mock_update_progress = mocker.patch('src.pages.driver_view.db_utils.update_ride_progress')

    # Act
    handle_move_forward(st)

    # Assert
    assert st.session_state["ride_progress"] == 0.50
    mock_update_progress.assert_called_once_with(42, 0.50)

def test_handle_move_forward_clamp(mock_streamlit, mocker):
    """Tests that progress is clamped at 1.0."""
    # Arrange
    st = mock_streamlit
    st.session_state["ride_progress"] = 0.9  # Start close to the end
    st.session_state["booking"] = {'status': 'accepted', 'ride_id': 42}

    mock_update_progress = mocker.patch('src.pages.driver_view.db_utils.update_ride_progress')

    # Act
    handle_move_forward(st) # This should increment by 0.25, hitting 1.15

    # Assert
    assert st.session_state["ride_progress"] == 1.0
    mock_update_progress.assert_called_once_with(42, 1.0)

def test_handle_complete_ride(mock_streamlit, mocker):
    """Tests that completing a ride persists to the DB and clears local state."""
    # Arrange
    st = mock_streamlit
    st.session_state["booking"] = {'status': 'accepted', 'ride_id': 42}
    st.session_state["ride_progress"] = 1.0
    st.session_state["distance_data"] = {'start': 'A', 'end': 'B'}
    st.session_state["_completed_ride"] = False

    mock_update_status = mocker.patch('src.pages.driver_view.db_utils.update_ride_status')

    # Act
    handle_complete_ride(st)

    # Assert
    mock_update_status.assert_called_once_with(ride_id=42, status="completed")

    # Check that local state is cleared
    assert st.session_state["booking"] is None
    assert st.session_state["ride_progress"] == 0.0
    assert st.session_state["distance_data"] is None
    assert st.session_state["_completed_ride"] is True # Temp flag is set

    # Check that UI elements were called
    st.balloons.assert_called_once()
    st.success.assert_called_once_with("Ride Completed!")


def test_handle_cancel_ride(mock_streamlit, mocker):
    """Tests that cancelling a ride persists to the DB and clears local state."""
    # Arrange
    st = mock_streamlit
    st.session_state["booking"] = {'status': 'accepted', 'ride_id': 42}

    mock_update_status = mocker.patch('src.pages.driver_view.db_utils.update_ride_status')

    # Act
    handle_cancel_ride(st)

    # Assert
    mock_update_status.assert_called_once_with(42, "cancelled")

    # Check that local state is cleared/set
    assert st.session_state["booking"] is None
    assert st.session_state["_cancelled_ride"] is True
    assert "_cancel_time" in st.session_state

def test_handle_logout(mock_streamlit):
    """Tests that logging out clears the role and defers navigation.

    Streamlit treats st.switch_page (like st.rerun) as a no-op inside an
    on_click callback, so handle_logout can't navigate directly -- it just
    flags the sign-out for main() to act on during the next script run.
    """
    # Arrange
    st = mock_streamlit
    st.session_state["role"] = "driver" # Set a role to clear

    # Act
    handle_logout(st)

    # Assert
    assert st.session_state["role"] is None
    assert st.session_state["_signed_out"] is True
    st.switch_page.assert_not_called()
