from pathlib import Path

import streamlit as st

ASSETS_DIR = Path(__file__).parent

st.set_page_config(
    page_title="Welcome to RelaxiTaxi",
    layout="centered",
)

# --- NEW CSS FIX ---
st.markdown(
    """
<style>
    [data-testid="stSidebar"] {
        display: none;
    }

    /* 1. Target the cards (the bordered containers) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        /* Set a taller fixed height as requested */
        min-height: 280px; 
        
        /* Use flexbox to align contents */
        display: flex;
        flex-direction: column;
        /* Push image to top, button to bottom */
        justify-content: space-between; 
    }

    /* 2. Target the image *itself* */
    [data-testid="stVerticalBlockBorderWrapper"] img {
        /* Force both images to be the same size */
        width: 150px;
        height: 150px; /* <-- This is the new part */
        
        /* Scale image nicely, don't stretch */
        object-fit: contain; 
        
        /* Center the image horizontally */
        display: block;
        margin-left: auto;
        margin-right: auto;
        
        /* Add some space above the image */
        margin-top: 1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)
# --- END NEW CSS FIX ---


# Initialize session state for role
if "role" not in st.session_state:
    st.session_state.role = None

def set_role(role):
    st.session_state.role = role

st.title("🚕 Welcome to RelaxiTaxi")
st.markdown("Please select your role to continue.")

col1, col2 = st.columns(2)

with col1:
    st.image(str(ASSETS_DIR / "customer.jpg"), width=150)
    if st.button("I'm a Customer", use_container_width=True):
        set_role("customer")
        st.switch_page("pages/rider_login.py")

with col2:
    st.image(str(ASSETS_DIR / "driver.jpg"), width=150)
    if st.button("I'm a Driver", use_container_width=True):
        set_role("driver")
        st.switch_page("pages/driver_login.py")
