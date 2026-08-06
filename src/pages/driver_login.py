"""Driver Login Page for RelaxiTaxi."""
import os
import sys
import streamlit as st

from db_utils import authenticate_user, init_db
from session_utils import goto, remember_session
from ui_helpers import setup_page

# Ensure src directory in import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

setup_page("Driver Login", "🧑‍✈️")

# Initialize DB if not present
init_db()

st.title("🧑‍✈️ Driver Login - RelaxiTaxi")

def login_driver(email: str, password: str):
    """Authenticate driver and set session state."""
    driver = authenticate_user("drivers", email, password)
    if not driver:
        return False

    st.session_state["user_id"] = driver["id"]
    st.session_state["user_name"] = driver["name"]
    st.session_state["role"] = "driver"
    remember_session("driver", driver["id"])
    return True


with st.form("login_form"):
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

if submitted:
    if not email or not password:
        st.warning("Please enter both email and password.")
    else:
        if login_driver(email, password):
            st.success("Login successful!")
            goto("pages/driver_view.py")
            st.stop()
        else:
            st.error("Invalid credentials. Please try again.")

if st.button("Don't have an account? Register", type="tertiary"):
    goto("pages/driver_register.py")
