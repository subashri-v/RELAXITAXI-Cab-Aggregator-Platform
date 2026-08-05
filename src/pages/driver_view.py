"""
Driver Dashboard Page for RelaxiTaxi.

This module handles the driver's view, allowing them to accept,
manage, and complete ride requests.
"""

# 1. Standard libraries
import os
import sys
import time

# 2. Third-party libraries
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

# 3. Local application imports
# --- FIX: Corrected all imports ---
from shared_state import get_app_state
import db_utils  # <-- ADDED FROM YOUR BRANCH

# ---------------------------------------------------------------------
# 1. HANDLER FUNCTIONS (The "Controller" Logic)
# ---------------------------------------------------------------------

def handle_logout(st_app):
    """Logs the user out and returns to the login page."""
    st_app.session_state["role"] = None
    st_app.switch_page("app.py")


def handle_accept_ride(st_app):
    """Accepts the pending ride request."""
    state = get_app_state()

    # Update private state
    st_app.session_state["booking"]['status'] = 'accepted'
    # --- MERGED: Use user_name from your branch ---
    st_app.session_state["booking"]['driver'] = st_app.session_state.get("user_name", "You (Driver)")

    # Update public state so customer sees it
    state["booking"] = st_app.session_state["booking"]

    # --- ADDED FROM YOUR BRANCH: Persist acceptance in DB ---
    booking = st_app.session_state["booking"]
    if "ride_id" in booking:
        db_utils.accept_ride(ride_id=booking["ride_id"], driver_id=int(st_app.session_state.user_id))


def handle_reject_ride(st_app):
    """Rejects the ride and clears the booking."""
    state = get_app_state()

    # Clear public state
    state["booking"] = None
    state["distance_data"] = None

    # Clear private state
    st_app.session_state["booking"] = None
    st_app.session_state["distance_data"] = None


def handle_move_forward(st_app):
    """Moves the ride progress forward by 25%."""
    state = get_app_state()

    # Update private state
    progress = st_app.session_state.get("ride_progress", 0.0)
    new_progress = min(1.0, progress + 0.25)
    st_app.session_state["ride_progress"] = new_progress

    # Update public state so customer sees it
    state["ride_progress"] = new_progress


def handle_complete_ride(st_app):
    """Completes the ride, shows balloons, and clears state."""
    state = get_app_state()
    st_app.balloons()
    st_app.success("Ride Completed!")

    # --- ADDED FROM YOUR BRANCH: Update DB before clearing state ---
    booking = st_app.session_state.get("booking")
    if booking and "ride_id" in booking:
        db_utils.update_ride_status(ride_id=booking["ride_id"], status="completed")

    # Clear public state
    state["booking"] = None
    state["distance_data"] = None
    state["ride_progress"] = 0.0

    # Clear private state
    st_app.session_state["booking"] = None
    st_app.session_state["ride_progress"] = 0.0
    st_app.session_state["distance_data"] = None

    # Store data in a temporary key for a 2-second success message
    st_app.session_state["_completed_ride"] = True


def handle_cancel_ride(st_app):
    """Cancels the ride and sets a flag to show a message."""
    state = get_app_state()

    # Update public state so customer page can react
    state["booking"] = {"status": "cancelled"}
    state["distance_data"] = None
    state["ride_progress"] = 0.0

    # Set private state for temp message
    st_app.session_state["_cancelled_ride"] = True
    st_app.session_state["_cancel_time"] = time.time()
    st_app.session_state["booking"] = None  # Clear private booking

# ---------------------------------------------------------------------
# 2. VIEW HELPER FUNCTIONS
# ---------------------------------------------------------------------

def _render_pending_view(st_app, booking, distance_data):
    """Renders the UI for a 'pending' ride request."""
    st_app.subheader("New Ride Request!")

    start_coords = distance_data.get("start_coords")
    end_coords = distance_data.get("end_coords")

    if start_coords and end_coords:
        # st.map requires a DataFrame with 'lat' and 'lon' columns
        map_data = pd.DataFrame(
            [start_coords, end_coords],
            columns=['lat', 'lon']
        )
        st_app.map(map_data)

    st_app.markdown(f"**From:** {distance_data.get('start', 'N/A')}")
    st_app.markdown(f"**To:** {distance_data.get('end', 'N/A')}")
    st_app.write(f"Estimated Fare: ₹{booking.get('fare', 0):.2f}")

    col1, col2 = st_app.columns(2)
    with col1:
        st_app.button("✅ Accept Ride", on_click=handle_accept_ride,
                      args=(st_app,), use_container_width=True)
    with col2:
        st_app.button("🚫 Reject Ride", on_click=handle_reject_ride,
                      args=(st_app,), use_container_width=True)


def _render_accepted_view(st_app, distance_data, ride_progress):
    """Renders the UI for an 'accepted' (on-going) ride."""
    st_app.subheader(f"On-going Ride to {distance_data.get('end', 'N/A')}")
    st_app.progress(ride_progress)

    # --- Driver Controls ---
    col1, col2, col3 = st_app.columns(3)
    with col1:
        st_app.button("🚗 Move Forward", on_click=handle_move_forward,
                      args=(st_app,), use_container_width=True)
    with col2:
        if ride_progress > 0.0:
            st_app.button("🏁 Complete Ride", on_click=handle_complete_ride,
                          args=(st_app,), use_container_width=True)
    with col3:
        if ride_progress == 0.0:
            st_app.button("🚫 Cancel Ride", on_click=handle_cancel_ride,
                          args=(st_app,), use_container_width=True)

    start_coords = distance_data.get("start_coords")
    end_coords = distance_data.get("end_coords")

    if not start_coords or not end_coords:
        st_app.warning("Coordinate data missing.")
        return

    if ride_progress == 0.0:
        st_app.info("On the way to pickup...")
    elif ride_progress < 1.0:
        st_app.info("Ride in progress...")

    # --- Map Display ---
    curr_lat = start_coords[0] + \
        ride_progress * (end_coords[0] - start_coords[0])
    curr_lon = start_coords[1] + \
        ride_progress * (end_coords[1] - start_coords[1])
    curr_location = (curr_lat, curr_lon)

    m = folium.Map(location=curr_location, zoom_start=13)
    folium.Marker(start_coords, tooltip="Start",
                  icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(end_coords, tooltip="Destination",
                  icon=folium.Icon(color="red")).add_to(m)
    folium.Marker(curr_location, tooltip="Driver (You)",
                  icon=folium.Icon(color="blue", icon="car",
                                    prefix="fa")).add_to(m)

    st_folium(m, width=700, height=400, returned_objects=[])

# ---------------------------------------------------------------------
# 3. MAIN VIEW FUNCTION (The "Router")
# ---------------------------------------------------------------------

def render_driver_view():
    """
    Render the driver dashboard page UI based on st.session_state.
    """

    # --- Header ---
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("👨‍✈️ Driver Portal")
    with col2:
        st.button("Sign Out", on_click=handle_logout, args=(st,))

    # --- ADDED FROM YOUR BRANCH: Ride History Button ---
    if st.button("Driver Ride History"):
        st.switch_page("pages/driver_history.py")
    st.divider() # Added a divider for cleaner UI
    # --- END ---

    # --- Load states from *private* session_state ---
    booking = st.session_state.get("booking")
    distance_data = st.session_state.get("distance_data", {})
    ride_progress = st.session_state.get("ride_progress", 0.0)

    # --- Case 1: No ride ---
    if not booking:
        st.info("No active ride requests. Waiting for a customer...")
        return

    status = booking.get("status", "").lower()

    # --- Router Logic ---
    if status == "pending":
        _render_pending_view(st, booking, distance_data)
    elif status == "accepted":
        _render_accepted_view(st, distance_data, ride_progress)
    else:
        # Show the status for better debugging
        st.warning(f"Unknown booking status: {status}")

# ---------------------------------------------------------------------
# 4. MAIN SCRIPT (The "Page")
# ---------------------------------------------------------------------

def main():
    """
    This function runs all the "page-level" logic.
    """

    # --- CSS ---
    st.markdown(
        """
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # --- Security Check ---
    if st.session_state.get("role") != "driver":
        st.error("You must be logged in as a driver to access this page.")
        if st.button("Go to Login"):
            st.switch_page("app.py")
        st.stop()

    # --- Handle temporary "cancel" message ---
    if st.session_state.get("_cancelled_ride"):
        st.warning("❌ Ride cancelled successfully!")
        if time.time() - st.session_state.get("_cancel_time", 0) > 3:
            st.session_state.pop("_cancelled_ride")
            st.session_state.pop("_cancel_time")
            st.rerun()
        st.stop()

    # --- Handle temporary "complete" message ---
    if st.session_state.get("_completed_ride"):
        time.sleep(2)
        st.session_state.pop("_completed_ride")
        st.rerun()

    # --- Render the main page view ---
    render_driver_view()

    # --- Auto-refresh logic (from develop, but fixed for pylint) ---
    state = get_app_state()

    # If this driver's private notebook is empty...
    if not st.session_state.get("booking"):

        # Get the booking from the public board first
        booking_on_public_board = state.get("booking")

        # Now check the variable (this is cleaner for pylint)
        if booking_on_public_board and booking_on_public_board["status"] == "pending":

            # A ride is available! Make a *copy* for our private notebook.
            st.session_state["booking"] = booking_on_public_board.copy()
            st.session_state["distance_data"] = state["distance_data"].copy()
            st.session_state["ride_progress"] = 0.0 # Start progress

            # Lock the ride on the public whiteboard so another driver can't take it
            booking_on_public_board["status"] = "locked_by_driver"

            st.rerun() # Rerun immediately to show the "pending" UI

        else:
            # No ride yet. Wait 5 seconds and check again.
            time.sleep(5)
            st.rerun()

# ---------------------------------------------------------------------
# 5. SCRIPT EXECUTION
# ---------------------------------------------------------------------

if __name__ == "__main__":

    main()
