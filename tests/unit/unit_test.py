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
    """Tests that accepting a ride changes the state correctly."""
    # Arrange
    st = mock_streamlit
    st.session_state["booking"] = {'status': 'pending'}

    # 1. Create a fake "public whiteboard" for this test
    mock_public_state = {'booking': {'status': 'pending'}}

    # 2. Tell pytest to intercept the call to get_app_state
    #    and return your fake whiteboard instead.
    mocker.patch(
        'src.pages.driver_view.get_app_state',
        return_value=mock_public_state
    )

    # Act
    handle_accept_ride(st)

    # Assert
    # Check that the private state was updated
    assert st.session_state["booking"]['status'] == 'accepted'
    assert st.session_state["booking"]['driver'] == "You (Driver)"

    # Check that the public state was updated
    assert mock_public_state["booking"]['status'] == 'accepted'

def test_handle_reject_ride(mock_streamlit, mocker):
    """Tests that rejecting a ride clears the state."""
    # Arrange
    st = mock_streamlit
    st.session_state["booking"] = {'status': 'pending'}
    st.session_state["distance_data"] = {'start': 'A', 'end': 'B'}

    # 1. Create a fake "public whiteboard" for this test
    mock_public_state = {
        'booking': {'status': 'pending'},
        'distance_data': {'start': 'A', 'end': 'B'}
    }

    # 2. Tell pytest to intercept the call to get_app_state
    mocker.patch(
        'src.pages.driver_view.get_app_state',
        return_value=mock_public_state
    )

    # Act
    handle_reject_ride(st)

    # Assert
    # Check that the private state was cleared
    assert st.session_state["booking"] is None
    assert st.session_state["distance_data"] is None

    # Check that the public state was cleared
    assert mock_public_state["booking"] is None
    assert mock_public_state["distance_data"] is None

def test_handle_move_forward(mock_streamlit, mocker):
    """Tests that moving forward increments progress."""
    # Arrange
    st = mock_streamlit
    st.session_state["ride_progress"] = 0.25

    # 1. Create a fake "public whiteboard" for this test
    mock_public_state = {'ride_progress': 0.25}

    # 2. Tell pytest to intercept the call to get_app_state
    mocker.patch(
        'src.pages.driver_view.get_app_state',
        return_value=mock_public_state
    )

    # Act
    handle_move_forward(st)

    # Assert
    # Check that the private state was updated
    assert st.session_state["ride_progress"] == 0.50

    # Check that the public state was updated
    assert mock_public_state["ride_progress"] == 0.50

def test_handle_move_forward_clamp(mock_streamlit, mocker):
    """Tests that progress is clamped at 1.0."""
    # Arrange
    st = mock_streamlit
    st.session_state["ride_progress"] = 0.9  # Start close to the end

    # 1. Create a fake "public whiteboard" for this test
    mock_public_state = {'ride_progress': 0.9}

    # 2. Tell pytest to intercept the call to get_app_state
    mocker.patch(
        'src.pages.driver_view.get_app_state',
        return_value=mock_public_state
    )

    # Act
    handle_move_forward(st) # This should increment by 0.25, hitting 1.15

    # Assert
    # Check that the private state was clamped to 1.0
    assert st.session_state["ride_progress"] == 1.0

    # Check that the public state was also clamped to 1.0
    assert mock_public_state["ride_progress"] == 1.0

def test_handle_complete_ride(mock_streamlit, mocker):
    """Tests that completing a ride clears the state."""
    # Arrange
    st = mock_streamlit
    st.session_state["booking"] = {'status': 'accepted'}
    st.session_state["ride_progress"] = 1.0
    st.session_state["distance_data"] = {'start': 'A', 'end': 'B'}
    st.session_state["_completed_ride"] = False

    # 1. Create a fake "public whiteboard"
    mock_public_state = {
        'booking': {'status': 'accepted'},
        'distance_data': {'start': 'A', 'end': 'B'},
        'ride_progress': 1.0
    }

    # 2. Patch get_app_state
    mocker.patch(
        'src.pages.driver_view.get_app_state',
        return_value=mock_public_state
    )

    # Act
    handle_complete_ride(st)

    # Assert
    # Check that private state is cleared
    assert st.session_state["booking"] is None
    assert st.session_state["ride_progress"] == 0.0
    assert st.session_state["distance_data"] is None
    assert st.session_state["_completed_ride"] is True # Temp flag is set
    
    # Check that public state is cleared
    assert mock_public_state["booking"] is None
    assert mock_public_state["distance_data"] is None
    assert mock_public_state["ride_progress"] == 0.0
    
    # Check that UI elements were called
    st.balloons.assert_called_once()
    st.success.assert_called_once_with("Ride Completed!")


def test_handle_cancel_ride(mock_streamlit, mocker):
    """Tests that cancelling a ride clears the state."""
    # Arrange
    st = mock_streamlit
    st.session_state["booking"] = {'status': 'accepted'}

    # 1. Create a fake "public whiteboard"
    mock_public_state = {
        'booking': {'status': 'accepted'},
        'distance_data': {},
        'ride_progress': 0.0
    }

    # 2. Patch get_app_state
    mocker.patch(
        'src.pages.driver_view.get_app_state',
        return_value=mock_public_state
    )

    # Act
    handle_cancel_ride(st)

    # Assert
    # Check that private state is cleared/set
    assert st.session_state["booking"] is None
    assert st.session_state["_cancelled_ride"] is True
    assert "_cancel_time" in st.session_state

    # Check that public state is updated
    assert mock_public_state["booking"]["status"] == "cancelled"
    assert mock_public_state["distance_data"] is None
    assert mock_public_state["ride_progress"] == 0.0

def test_handle_logout(mock_streamlit):
    """Tests that logging out clears the role and switches pages."""
    # Arrange
    st = mock_streamlit
    st.session_state["role"] = "driver" # Set a role to clear
    
    # Act
    handle_logout(st)
    
    # Assert
    assert st.session_state["role"] is None
    st.switch_page.assert_called_once_with("app.py")