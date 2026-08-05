import streamlit as st
from db_utils import authenticate_user, init_db

init_db()

# Hide sidebar
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state
st.session_state.setdefault("role", None)
st.session_state.setdefault("user_id", None)
st.session_state.setdefault("user_name", None)

st.title("🚕 Rider Login")

with st.form("login_form"):
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login")

if submitted:
    user = authenticate_user("riders", email, password)
    if user:
        st.session_state["role"] = "customer"
        st.session_state["user_id"] = user["id"]
        st.session_state["user_name"] = user["name"]
        st.success(f"Welcome, {user['name']}!")
        st.switch_page("pages/book_ride.py")
    else:
        st.error("Invalid credentials. Please try again.")

if st.button("Don't have an account? Register"):
    st.switch_page("pages/rider_register.py")

if st.button("Logout"):
    st.switch_page("app.py")
