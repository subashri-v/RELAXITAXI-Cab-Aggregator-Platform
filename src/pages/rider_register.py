import streamlit as st
from db_utils import register_user, init_db
from session_utils import goto
from ui_helpers import setup_page

setup_page("Rider Registration", "📝")

init_db()

st.title("🚕 Rider Registration - RelaxiTaxi")

with st.form("register_form"):
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Register", type="primary", use_container_width=True)

if submitted:
    if name and email and password:
        try:
            register_user("riders", name, email, password)
            st.success("✅ Registration successful! Please log in now.")
        except Exception as error:
            st.error(f"Error: {error}")
    else:
        st.warning("Please fill in all fields.")

if st.button("Login", type="tertiary"):
    goto("pages/rider_login.py")
