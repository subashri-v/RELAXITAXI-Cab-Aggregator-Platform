"""
Driver Ride History Page for RelaxiTaxi

This page displays completed rides for the logged-in driver.
It requires the driver to be authenticated.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from db_utils import get_driver_history
from shared_state import get_app_state


def check_driver_auth() -> None:
    """Check authentication state and redirect if not a driver."""
    role = st.session_state.get("role")
    if role != "driver":
        st.error("You must be logged in as a driver to view ride history.")
        if st.button("Go to Login"):
            st.switch_page("pages/driver_login.py")
        st.stop()


def render_navigation() -> None:
    """Render sign-out and navigation buttons."""
    if st.button("Sign Out"):
        st.session_state.role = None
        st.switch_page("app.py")

    if st.button("Back To Driver View"):
        st.switch_page("pages/driver_view.py")


def format_driver_history(rides: list[dict]) -> pd.DataFrame:
    """
    Convert ride dict list into a clean display DataFrame.

    Args:
        rides: Raw ride history list of dictionaries.

    Returns:
        A formatted pandas DataFrame for UI display.
    """
    df = pd.DataFrame(rides)

    # Handle missing AC column safely
    df["ac"] = df.get("ac", pd.Series(["Unknown"] * len(df)))
    df["ac"] = df["ac"].apply(lambda value: "AC" if value else "Non-AC")

    df_display = df[[
        "id", "rider_id", "start_location", "end_location",
        "distance_km", "fare", "ac", "status", "ride_time"
    ]]

    df_display = df_display.rename(columns={
        "id": "Ride ID",
        "rider_id": "Rider ID",
        "start_location": "Start",
        "end_location": "End",
        "distance_km": "Distance (km)",
        "fare": "Fare (₹)",
        "ac": "Type",
        "status": "Status",
        "ride_time": "Booked At"
    })

    return df_display


def show_driver_history() -> None:
    """Fetch and display ride history for logged-in driver."""
    driver_id = int(st.session_state.get("user_id"))

    rides = get_driver_history(driver_id)

    if not rides:
        st.info("No rides found yet.")
        return

    df_display = format_driver_history(rides)
    st.dataframe(df_display, use_container_width=True)


def main() -> None:
    """Main entry point for driver history page."""
    get_app_state()  # Ensure shared state loads
    check_driver_auth()
    st.title("👨‍✈️ Driver Ride History")
    render_navigation()
    show_driver_history()


if __name__ == "__main__":
    main()
