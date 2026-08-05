# shared_state.py
import streamlit as st

# This function uses a cache to return a SINGLE dictionary object.
# This means every user session will get the exact same dictionary.
@st.cache_resource
def get_app_state():
    return {
        "booking": None,
        "distance_data": None,
        "ride_progress": 0.0
    }