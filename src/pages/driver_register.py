"""Driver Registration Page for RelaxiTaxi."""
import streamlit as st
from db_utils import register_user, init_db

st.set_page_config(page_title="Driver Registration", layout="centered")

# Initialize DB
init_db()

st.title("🚖 Driver Registration - RelaxiTaxi")


def validate_registration(name: str, email: str, password: str, vehicle_no: str, license_no: str) -> bool:
    """Check if all required fields are provided."""
    return all([name, email, password, vehicle_no, license_no])


def attempt_registration(name: str, email: str, password: str, vehicle_no: str, license_no: str) -> bool:
    """Try to register a new driver using the database utility."""
    return register_user(
        "drivers",
        name,
        email,
        password,
        vehicle_no=vehicle_no,
        license_no=license_no
    )

# 1. Initialize session state to track success
if "registration_success" not in st.session_state:
    st.session_state.registration_success = False

# 2. Check the session state flag
if st.session_state.registration_success:
    # If successful, show message and login button
    st.success("✅ Registration successful! Please log in.")
    if st.button("Go to Login"):
        # Reset flag before switching
        st.session_state.registration_success = False
        st.switch_page("pages/driver_login.py")
else:
    with st.form("register_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        vehicle_no = st.text_input("Vehicle Number")
        license_no = st.text_input("License Number")

        submitted = st.form_submit_button("Register")

    if submitted:
        if not validate_registration(name, email, password, vehicle_no, license_no):
            st.warning("Please fill in all fields.")
        else:
            success = attempt_registration(name, email, password, vehicle_no, license_no)
            if success:
                st.success("✅ Registration successful! Please log in.")
                if st.button("Go to Login"):
                    st.switch_page("pages/driver_login.py")
            else:
                st.error("Registration failed. Email may already be registered.")
