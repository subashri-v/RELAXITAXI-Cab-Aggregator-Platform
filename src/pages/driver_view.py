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
import db_utils
from session_utils import forget_session, goto, restore_session
from ui_helpers import setup_page

# ---------------------------------------------------------------------
# 1. HANDLER FUNCTIONS (The "Controller" Logic)
# ---------------------------------------------------------------------

def handle_logout(st_app):
    """Logs the user out. Navigation can't happen here: Streamlit treats
    st.switch_page (like st.rerun) as a no-op inside an on_click callback,
    so we just flag it and let main() do the actual navigation."""
    st_app.session_state["role"] = None
    st_app.session_state["_signed_out"] = True


def handle_accept_ride(st_app):
    """Accepts the pending ride request."""
    booking = st_app.session_state["booking"]
    driver_name = st_app.session_state.get("user_name", "You (Driver)")

    # Persist acceptance in DB - this is now the single source of truth
    if "ride_id" in booking:
        db_utils.accept_ride(
            ride_id=booking["ride_id"],
            driver_id=int(st_app.session_state.user_id),
            driver_name=driver_name
        )

    # Update private state to match
    booking['status'] = 'accepted'
    booking['driver'] = driver_name
    st_app.session_state["booking"] = booking


def handle_reject_ride(st_app):
    """Rejects the ride and clears the booking."""
    booking = st_app.session_state.get("booking")
    if booking and "ride_id" in booking:
        db_utils.update_ride_status(booking["ride_id"], "rejected")

    st_app.session_state["booking"] = None
    st_app.session_state["distance_data"] = None


def handle_move_forward(st_app):
    """Moves the ride progress forward by 25%."""
    progress = st_app.session_state.get("ride_progress", 0.0)
    new_progress = min(1.0, progress + 0.25)
    st_app.session_state["ride_progress"] = new_progress

    booking = st_app.session_state.get("booking")
    if booking and "ride_id" in booking:
        db_utils.update_ride_progress(booking["ride_id"], new_progress)


def handle_complete_ride(st_app):
    """Completes the ride, shows balloons, and clears state."""
    st_app.balloons()
    st_app.success("Ride Completed!")

    booking = st_app.session_state.get("booking")
    if booking and "ride_id" in booking:
        db_utils.update_ride_status(ride_id=booking["ride_id"], status="completed")

    # Clear private state
    st_app.session_state["booking"] = None
    st_app.session_state["ride_progress"] = 0.0
    st_app.session_state["distance_data"] = None

    # Store data in a temporary key for a 2-second success message
    st_app.session_state["_completed_ride"] = True


def handle_cancel_ride(st_app):
    """Cancels the ride and sets a flag to show a message."""
    booking = st_app.session_state.get("booking")
    if booking and "ride_id" in booking:
        db_utils.update_ride_status(booking["ride_id"], "cancelled")

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
                      args=(st_app,), use_container_width=True, type="primary")
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
                      args=(st_app,), use_container_width=True, type="primary")
    with col2:
        if ride_progress > 0.0:
            st_app.button("🏁 Complete Ride", on_click=handle_complete_ride,
                          args=(st_app,), use_container_width=True, type="primary")
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

    m = folium.Map(location=curr_location, zoom_start=13, tiles="CartoDB dark_matter")
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
        st.button("Sign Out", on_click=handle_logout, args=(st,), type="tertiary")

    if st.button("Driver Ride History", type="tertiary"):
        goto("pages/driver_history.py")
    st.divider()

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

    setup_page("Driver Portal", "🧑‍✈️")
    restore_session()

    # --- Handle deferred sign-out (flagged by handle_logout) ---
    if st.session_state.pop("_signed_out", False):
        forget_session()
        goto("app.py")
        st.stop()

    # --- Security Check ---
    if st.session_state.get("role") != "driver":
        st.error("You must be logged in as a driver to access this page.")
        if st.button("Go to Login", type="primary"):
            goto("app.py")
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

    # --- Auto-refresh logic: poll the DB for a ride to claim ---
    # If this driver's private notebook is empty...
    if not st.session_state.get("booking"):

        # Look for the oldest ride still waiting for a driver
        pending_ride = db_utils.get_pending_ride()

        if pending_ride and db_utils.try_lock_ride(pending_ride["id"]):
            # We won the race to claim this ride. Build our private notebook
            # from the *pre-lock* snapshot, so it still shows status "pending"
            # (the DB row itself is now "locked_by_driver" so no one else grabs it).
            st.session_state["booking"] = db_utils.ride_to_booking_view(pending_ride)
            st.session_state["distance_data"] = db_utils.ride_to_distance_data(pending_ride)
            st.session_state["ride_progress"] = 0.0 # Start progress

            st.rerun() # Rerun immediately to show the "pending" UI

        else:
            # No ride yet, or another driver already claimed it. Check again shortly.
            time.sleep(5)
            st.rerun()

# ---------------------------------------------------------------------
# 5. SCRIPT EXECUTION
# ---------------------------------------------------------------------

if __name__ == "__main__":

    main()
