import pandas as pd
import streamlit as st
from db_utils import get_rider_history
from session_utils import goto, restore_session
from ui_helpers import setup_page

setup_page("Ride History", "📜")
restore_session()

st.title("📜 Your Ride History")

# Security check
if st.session_state.get("role") != "customer" or st.session_state.get("user_id") is None:
    st.error("Please log in as a rider first.")
    st.stop()

user_id = st.session_state["user_id"]
history = get_rider_history(user_id)

if not history:
    st.info("No rides found yet.")
else:
    df = pd.DataFrame(history)
    df["ac"] = df["ac"].apply(lambda value: "AC" if value else "Non-AC")
    df = df[[
        "id", "start_location", "end_location",
        "distance_km", "fare", "ac", "status", "ride_time"
    ]].rename(columns={
        "id": "Ride ID",
        "start_location": "Start",
        "end_location": "End",
        "distance_km": "Distance (km)",
        "fare": "Fare (₹)",
        "ac": "Type",
        "status": "Status",
        "ride_time": "Booked At",
    })
    st.dataframe(df, use_container_width=True, hide_index=True)

if st.button("Book a New Ride", use_container_width=True, type="primary"):
    goto("pages/book_ride.py")
