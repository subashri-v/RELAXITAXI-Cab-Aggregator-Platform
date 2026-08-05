import sys
import os

# --- THIS IS THE NEW CODE ---
# Add the project root directory (RelaxiTaxi) to the Python path
# This allows tests to import modules from the 'pages' folder
# __file__ is 'C:\...\RelaxiTaxi\tests\conftest.py'
# os.path.dirname(__file__) is 'C:\...\RelaxiTaxi\tests'
# os.path.dirname(os.path.dirname(__file__)) is 'C:\...\RelaxiTaxi'
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
# --- END OF NEW CODE ---


import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_streamlit():
    """
    Mocks all required Streamlit functions (`st.*`) to prevent them
    from actually running and to allow us to check if they were called.
    """
    
    # Define a custom exception that simulates st.stop()
    class StreamlitStopException(Exception):
        pass

    # --- THIS IS THE NEW, SMARTER FUNCTION ---
    # It checks the arguments passed to st.columns and returns the
    # correct number of mock objects.
    def mock_columns_side_effect(*args, **kwargs):
        arg = args[0] if args else None
        
        if arg == [0.8, 0.2]:
            # Return 2 mocks for the header
            return (MagicMock(), MagicMock())
        elif arg == 3:
            # Return 3 mocks for the driver controls
            return (MagicMock(), MagicMock(), MagicMock())
        else:
            # A fallback just in case
            return (MagicMock(), MagicMock())

    mock_st = MagicMock()
    
    # Make this exception available to tests by attaching it to the mock
    mock_st.StreamlitStopException = StreamlitStopException

    # Mock functions that would stop the test
    mock_st.stop = MagicMock(side_effect=StreamlitStopException)
    mock_st.rerun = MagicMock(side_effect=StreamlitStopException)

    # Mock widgets
    mock_st.button = MagicMock(return_value=False)
    mock_st.progress = MagicMock()
    mock_st.balloons = MagicMock()
    
    # IMPORTANT: Mock session_state as a dictionary
    mock_st.session_state = {} 

    # Mock display elements
    mock_st.markdown = MagicMock()
    mock_st.info = MagicMock()
    mock_st.success = MagicMock()
    mock_st.error = MagicMock()
    mock_st.warning = MagicMock()
    mock_st.title = MagicMock()
    mock_st.subheader = MagicMock()
    
    # --- THIS LINE IS UPDATED ---
    # Instead of a fixed return_value, it now uses our smart function
    mock_st.columns = MagicMock(side_effect=mock_columns_side_effect)

    # Mock external components
    mock_folium = MagicMock()

    with patch.dict('sys.modules', {
        'streamlit': mock_st,
        'folium': mock_folium,
        'streamlit_folium': MagicMock()
    }):
        yield mock_st

@pytest.fixture
def mock_state():
    """
    Provides a simple, empty dictionary for *unit tests*
    to use as a mock state.
    """
    # This is for your unit tests, which just test logic
    return {}