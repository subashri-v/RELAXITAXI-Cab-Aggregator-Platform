# tests/test_payment_ui.py
import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
from src.pages import payment_ui

@pytest.fixture
def mock_ride_details():
    return {
        "driver": "Arun",
        "type": "Mini",
        "fare": 230.0,
        "status": "completed"
    }

# --- Test UPI payment path ---
@patch("streamlit.image")  # mock QR code display
@patch("streamlit.switch_page")  # prevent actual page switch
def test_payment_ui_upi(mock_switch_page, mock_image, mock_ride_details):
    # Set fake session state
    st.session_state["ride_details"] = mock_ride_details

    with patch("streamlit.radio", return_value="📱 UPI"):
        with patch("streamlit.button", return_value=True):
            with patch("qrcode.make", return_value=MagicMock(save=lambda buf: None)):
                try:
                    payment_ui.main()
                except Exception as e:
                    pytest.fail(f"Payment UI crashed on UPI path: {e}")

# --- Test Card payment path ---
@patch("streamlit.switch_page")
def test_payment_ui_card(mock_switch_page, mock_ride_details):
    st.session_state["ride_details"] = mock_ride_details

    with patch("streamlit.radio", return_value="💳 Card"):
        with patch("streamlit.text_input", side_effect=["1234567890123456", "12/34", "123"]):
            with patch("streamlit.button", return_value=True):
                try:
                    payment_ui.main()
                except Exception as e:
                    pytest.fail(f"Payment UI crashed on Card path: {e}")

# --- Test Cash payment path ---
@patch("streamlit.switch_page")
def test_payment_ui_cash(mock_switch_page, mock_ride_details):
    st.session_state["ride_details"] = mock_ride_details

    with patch("streamlit.radio", return_value="💵 Cash"):
        with patch("streamlit.button", return_value=True):
            try:
                payment_ui.main()
            except Exception as e:
                pytest.fail(f"Payment UI crashed on Cash path: {e}")
