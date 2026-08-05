"""Driver Login Page for RelaxiTaxi."""
import os
import sys
import streamlit as st

from db_utils import authenticate_user, init_db

# Ensure src directory in import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(page_title="Driver Login", layout="centered")

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
    return True


with st.form("login_form"):
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login")

if submitted:
    if not email or not password:
        st.warning("Please enter both email and password.")
    else:
        if login_driver(email, password):
            st.success("Login successful!")
            st.switch_page("pages/driver_view.py")
            st.stop()
        else:
            st.error("Invalid credentials. Please try again.")

if st.button("Don't have an account? Register"):
    st.switch_page("pages/driver_register.py")
