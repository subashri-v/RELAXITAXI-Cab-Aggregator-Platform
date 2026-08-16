"""Main booking page for RelaxiTaxi rider interface."""

from typing import Any, Dict
import os
import sys
import time
import streamlit as st
from streamlit_folium import st_folium
import folium

from ride_utils import get_coordinates, calculate_distance, calculate_fare  # pylint: disable=E0401

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Streamlit adds this page's own directory (src/pages) to sys.path at
# runtime, and the sys.path.append above adds src/ itself, so these
# resolve fine at runtime even though pylint can't see that statically.
from db_utils import (  # pylint: disable=E0401
    add_ride,
    get_active_ride_for_rider,
    ride_to_booking_view,
)
from session_utils import forget_session, goto, restore_session  # pylint: disable=E0401
from ui_helpers import setup_page  # pylint: disable=E0401

setup_page("Book a Ride", "🚗")
restore_session()


def compute_distance_data(start_location: str, end_location: str) -> Dict[str, Any]:
    """Return distance data between start and end locations."""
    start_coords = get_coordinates(start_location)
    end_coords = get_coordinates(end_location)
    distance_km = calculate_distance(start_coords, end_coords)
    return {
        "start": start_location,
        "end": end_location,
        "start_coords": start_coords,
        "end_coords": end_coords,
        "distance_km": distance_km,
    }

# ====== Streamlit UI ======

# Security Check
if st.session_state.get("role") != "customer":
    st.error("Please log in as a customer to access this page.")
    if st.button("Go to Login", type="primary"):
        goto("app.py")
    st.stop()

if st.button("Ride History", type="tertiary"):
    goto("pages/rider_history.py")

# Header
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.title("🚕 RelaxiTaxi")
with col2:
    if st.button("Sign Out", type="tertiary"):
        st.session_state.role = None
        forget_session()
        goto("app.py")

# Inputs
start = st.text_input("Enter Start Location:", "PES University, Bangalore")
end = st.text_input("Enter End Location:", "MG Road, Bangalore")

# Search button
if st.button("Search Rides", type="primary"):
    try:
        st.session_state["search_result"] = compute_distance_data(start, end)
    except ValueError as e:
        st.error(str(e))

# Display result
if st.session_state.get("search_result"):
    data: Dict[str, Any] = st.session_state["search_result"]
    distance = data["distance_km"]
    st.success(f"📏 Distance between {data['start']} and {data['end']}: {distance:.2f} km")

    # Map
    m = folium.Map(location=data["start_coords"], zoom_start=13, tiles="CartoDB dark_matter")
    folium.Marker(data["start_coords"], tooltip="Start", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(data["end_coords"], tooltip="End", icon=folium.Icon(color='red')).add_to(m)
    st_folium(m, width=700, height=500)

    # Fare display
    total_ac = calculate_fare(distance, ac=True)
    total_non_ac = calculate_fare(distance, ac=False)

    st.markdown("### 🚗 Available Cabs")
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown(
                "<div style='text-align:center; font-size:56px;'>🚗</div>",
                unsafe_allow_html=True,
            )
            st.markdown("**Non-AC Ride**")
            st.markdown(f"💰 Estimated Fare: **₹{total_non_ac:.2f}**")
            if st.button("Book Non-AC", use_container_width=True, type="primary"):
                add_ride(
                    rider_id=int(st.session_state.user_id),
                    start=data["start"],
                    end=data["end"],
                    start_coords=data["start_coords"],
                    end_coords=data["end_coords"],
                    distance_km=distance,
                    fare=total_non_ac,
                    ac=False,
                    driver_id=None
                )
                st.session_state["search_result"] = None
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown(
                "<div style='text-align:center; font-size:56px;'>🚕</div>",
                unsafe_allow_html=True,
            )
            st.markdown("**AC Ride**")
            st.markdown(f"💰 Estimated Fare: **₹{total_ac:.2f}**")
            if st.button("Book AC", use_container_width=True, type="primary"):
                add_ride(
                    rider_id=int(st.session_state.user_id),
                    start=data["start"],
                    end=data["end"],
                    start_coords=data["start_coords"],
                    end_coords=data["end_coords"],
                    distance_km=distance,
                    fare=total_ac,
                    ac=True,
                    driver_id=None
                )
                st.session_state["search_result"] = None
                st.rerun()

# Booking Confirmation
active_ride = get_active_ride_for_rider(int(st.session_state.user_id))
if active_ride:
    current_booking_data: Dict[str, Any] = ride_to_booking_view(active_ride)
    st.markdown("---")

    if current_booking_data["status"] in ("pending", "locked_by_driver"):
        st.info("⏳ Waiting for a driver to accept your ride...")
        time.sleep(2)
        st.rerun()

    elif current_booking_data["status"] == "accepted":
        st.success(
            f"✅ {current_booking_data['type']} booked!\n\n"
            f"👨‍✈️ Driver: **{current_booking_data['driver']}**\n\n"
            f"🚘 Car Number: **{current_booking_data['car_number']}**\n\n"
            f"⏱ ETA: **{current_booking_data['eta']} mins**\n\n"
            f"💰 Fare: **₹{current_booking_data['fare']:.2f}**"
        )
        if st.button("📍 Track Your Ride", type="primary"):
            goto("pages/track_ride.py")
