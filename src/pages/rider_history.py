import streamlit as st
from db_utils import get_rider_history

st.title("📝 Your Ride History")

# Security check
if st.session_state.get("role") != "customer" or st.session_state.get("user_id") is None:
    st.error("Please log in as a rider first.")
    st.stop()

user_id = st.session_state["user_id"]
history = get_rider_history(user_id)

if not history:
    st.info("No rides found yet.")
else:
    for ride in history:
        st.markdown(f"**Ride ID:** {ride['id']}")
        st.markdown(f"From: {ride['start_location']} → To: {ride['end_location']}")
        st.markdown(
            f"Distance: {ride['distance_km']:.2f} km | "
            f"Fare: ₹{ride['fare']:.2f} | "
            f"AC: {'Yes' if ride['ac'] else 'No'}"
        )
        st.markdown(f"Driver ID: {ride['driver_id']} | Status: {ride['status']}")
        st.markdown(f"Time: {ride['ride_time']}")
        st.divider()

if st.button("Book a New Ride"):
    st.switch_page("pages/book_ride.py")
