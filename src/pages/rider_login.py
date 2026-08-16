import streamlit as st
from db_utils import authenticate_user, init_db
from session_utils import forget_session, goto, remember_session
from ui_helpers import setup_page

setup_page("Rider Login", "🔑")

init_db()

# Initialize session state
st.session_state.setdefault("role", None)
st.session_state.setdefault("user_id", None)
st.session_state.setdefault("user_name", None)

st.title("🚕 Rider Login")

with st.form("login_form"):
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

if submitted:
    user = authenticate_user("riders", email, password)
    if user:
        st.session_state["role"] = "customer"
        st.session_state["user_id"] = user["id"]
        st.session_state["user_name"] = user["name"]
        remember_session("customer", user["id"])
        st.success(f"Welcome, {user['name']}!")
        goto("pages/book_ride.py")
    else:
        st.error("Invalid credentials. Please try again.")

if st.button("Don't have an account? Register", type="tertiary"):
    goto("pages/rider_register.py")

if st.button("Logout", type="tertiary"):
    forget_session()
    goto("app.py")
