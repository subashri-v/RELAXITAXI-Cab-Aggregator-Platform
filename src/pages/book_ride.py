# pylint: disable=E1136, W0621, C0103, E0401
"""Main booking page for RelaxiTaxi rider interface."""

from typing import Any, Dict
import os
import sys
import random
import streamlit as st
from streamlit_folium import st_folium
import folium

# ====== Path and Imports (Kept as-is from branches) ======
from ride_utils import get_coordinates, calculate_distance, calculate_fare
from shared_state import get_app_state

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db_utils import add_ride  # From your 'current' branch

state: Dict[str, Any] = get_app_state()

# ====== Functions (From develop) ======

def compute_distance_data(start: str, end: str) -> Dict[str, Any]:
    """Return distance data between start and end locations."""
    start_coords = get_coordinates(start)
    end_coords = get_coordinates(end)
    distance_km = calculate_distance(start_coords, end_coords)
    return {
        "start": start,
        "end": end,
        "start_coords": start_coords,
        "end_coords": end_coords,
        "distance_km": distance_km,
    }


def create_booking(ride_type: str, distance: float) -> Dict[str, Any]:
    """Return booking details (this does NOT save to DB)."""
    car_numbers = [
        "KA01AB1235", "KA03CD5678", "KA05EF4321",
        "KA09GH8765", "KA02JK9988", "KA07LM4455"
    ]
    drivers = {
        "AC Ride": ["Vikas Rao", "Arjun Patil", "Manoj Kumar", "Suresh Reddy", "Abhinav Singh"],
        "Non-AC Ride": ["Ravi Kumar", "Amit Sharma", "Karan Singh", "Rahul Das", "Deepak Mehta"]
    }

    fare = calculate_fare(distance, ac=(ride_type == "AC Ride"))
    return {
        "type": ride_type,
        "fare": fare,
        "driver": random.choice(drivers[ride_type]),
        "car_number": random.choice(car_numbers),
        "eta": random.randint(3, 10),
        "status": "pending"
    }

# ====== Streamlit UI ======

# Hide sidebar
st.markdown(
    "<style>[data-testid='stSidebar']{display:none;}</style>",
    unsafe_allow_html=True
)

# Security Check
# --- BUG: Kept "customer" role ---
if st.session_state.get("role") != "customer":
    st.error("Please log in as a customer to access this page.")
    if st.button("Go to Login"):
        st.switch_page("app.py")
    st.stop()

# --- ADDED FROM YOUR BRANCH: Ride History Button ---
if st.button("Ride History"):
    st.switch_page("pages/rider_history.py")

# Header
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.title("🚕 RelaxiTaxi")
with col2:
    if st.button("Sign Out"):
        st.session_state.role = None
        st.switch_page("app.py")

# Inputs
start = st.text_input("Enter Start Location:", "PES University, Bangalore")
end = st.text_input("Enter End Location:", "MG Road, Bangalore")

# Search button
if st.button("Search Rides"):
    try:
        state["distance_data"] = compute_distance_data(start, end)
        state["booking"] = None
    except ValueError as e:
        st.error(str(e))

# Display result
if state.get("distance_data"):
    data: Dict[str, Any] = state["distance_data"]
    distance = data["distance_km"]
    st.success(f"📏 Distance between {data['start']} and {data['end']}: {distance:.2f} km")

    # Map
    m = folium.Map(location=data["start_coords"], zoom_start=13)
    folium.Marker(data["start_coords"], tooltip="Start", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(data["end_coords"], tooltip="End", icon=folium.Icon(color='red')).add_to(m)
    st_folium(m, width=700, height=500)

    # Fare display
    total_ac = calculate_fare(distance, ac=True)
    total_non_ac = calculate_fare(distance, ac=False)

    st.markdown("### 🚗 Available Cabs")
    col1, col2 = st.columns(2)

    # --- MERGED: Non-AC Ride (combines develop and current) ---
    with col1:
        st.image("https://icon-library.com/images/cab-icon/cab-icon-16.jpg", width=120)
        st.markdown("**Non-AC Ride**")
        st.markdown(f"💰 Estimated Fare: **₹{total_non_ac:.2f}**")
        if st.button("Book Non-AC"):
            # 1. Create booking details (from develop)
            booking_details = create_booking("Non-AC Ride", distance)

            # 2. Save to DB (from current) and get ride_id
            ride_id = add_ride(
                rider_id=int(st.session_state.user_id),
                start=data["start"],
                end=data["end"],
                start_coords=data["start_coords"],
                end_coords=data["end_coords"],
                distance_km=distance,
                fare=booking_details["fare"],
                ac=False,
                driver_id=None
            )
            
            # 3. Add ride_id to the booking
            booking_details["ride_id"] = ride_id

            # 4. Save to global state
            state["booking"] = booking_details
            state["ride_progress"] = 0.0

    # --- MERGED: AC Ride (combines develop and current) ---
    with col2:
        st.image(
            "https://images.vexels.com/media/users/3/128868/isolated/preview/"
            "b8dd4eaa0e285fcf4248b50916b0cef9-taxi-cab-icon-silhouette.png",
            width=120
        )
        st.markdown("**AC Ride**")
        st.markdown(f"💰 Estimated Fare: **₹{total_ac:.2f}**")
        if st.button("Book AC"):
            # 1. Create booking details (from develop)
            booking_details = create_booking("AC Ride", distance)

            # 2. Save to DB (from current) and get ride_id
            ride_id = add_ride(
                rider_id=int(st.session_state.user_id),
                start=data["start"],
                end=data["end"],
                start_coords=data["start_coords"],
                end_coords=data["end_coords"],
                distance_km=distance,
                fare=booking_details["fare"],
                ac=True,
                driver_id=None
            )
            
            # 3. Add ride_id to the booking
            booking_details["ride_id"] = ride_id

            # 4. Save to global state
            state["booking"] = booking_details
            state["ride_progress"] = 0.0

            st.rerun()

# Booking Confirmation
if state.get("booking"):
    current_booking_data: Dict[str, Any] = state["booking"]
    st.markdown("---")

    if current_booking_data["status"] == "pending":
        st.info("⏳ Waiting for a driver to accept your ride...")
        st.rerun()

    elif current_booking_data["status"] == "accepted":
        st.success(
            f"✅ {current_booking_data['type']} booked!\n\n"
            f"👨‍✈️ Driver: **{current_booking_data['driver']}**\n\n"
            f"🚘 Car Number: **{current_booking_data['car_number']}**\n\n" # <-- Kept from develop
            f"⏱ ETA: **{current_booking_data['eta']} mins**\n\n"
            f"💰 Fare: **₹{current_booking_data['fare']:.2f}**"
        )
        if st.button("📍 Track Your Ride"):

            st.switch_page("pages/track_ride.py")
