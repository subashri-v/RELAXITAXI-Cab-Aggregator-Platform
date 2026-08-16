"""Customer page for tracking an active cab ride in RelaxiTaxi."""

from typing import Dict, Any, Tuple
import os
import sys
import time
import folium
import streamlit as st
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Ensure module path is set
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import db_utils
from db_utils import get_active_ride_for_rider, ride_to_booking_view, ride_to_distance_data
from session_utils import forget_session, goto, restore_session
from ui_helpers import setup_page


# ====== Core Logic ======

def calculate_fare_for_distance(ride_type: str, distance_km: float) -> float:
    """Compute fare based on ride type and distance."""
    if ride_type == "AC Ride":
        base_fare, per_km = 60, 20
    else:
        base_fare, per_km = 40, 15
    return base_fare + (per_km * distance_km)


def update_route(
    new_start_loc: str,
    new_end_loc: str,
    booking_details: Dict[str, Any],
) -> Dict[str, Any]:
    """Update ride route and fare based on new locations."""
    geolocator = Nominatim(user_agent="relaxitaxi_tracker", timeout=10)
    start_loc = geolocator.geocode(new_start_loc)
    end_loc = geolocator.geocode(new_end_loc)

    if not start_loc or not end_loc:
        raise ValueError("Could not find one or both locations")

    s_coords: Tuple[float, float] = (start_loc.latitude, start_loc.longitude)
    e_coords: Tuple[float, float] = (end_loc.latitude, end_loc.longitude)
    distance_km = geodesic(s_coords, e_coords).kilometers
    fare = calculate_fare_for_distance(booking_details["type"], distance_km)

    return {
        "start_coords": s_coords,
        "end_coords": e_coords,
        "start": new_start_loc,
        "end": new_end_loc,
        "distance_km": distance_km,
        "fare": fare,
    }


def simulate_driver_position(
    start_c: Tuple[float, float],
    end_c: Tuple[float, float],
    ride_progress: float,
) -> Tuple[float, float]:
    """Return the simulated current location of the driver."""
    lat = start_c[0] + ride_progress * (end_c[0] - start_c[0])
    lon = start_c[1] + ride_progress * (end_c[1] - start_c[1])
    return (lat, lon)


# ====== Streamlit UI ======

setup_page("Track Your Ride", "📍")
restore_session()

if st.session_state.get("role") != "customer":
    st.error("You must be logged in as a customer to access this page.")
    if st.button("Go to Login", type="primary"):
        goto("app.py")
    st.stop()

# Header
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.title("📍 Track Your Ride")
with col2:
    if st.button("Sign Out", type="tertiary"):
        st.session_state.role = None
        forget_session()
        goto("app.py")

# Check active ride
rider_id = int(st.session_state.user_id)
active_ride = get_active_ride_for_rider(rider_id)

if active_ride is None:
    goto("pages/payment_ui.py")
    st.stop()

booking_info: Dict[str, Any] = ride_to_booking_view(active_ride)
ride_info: Dict[str, Any] = ride_to_distance_data(active_ride)
start_coords: Tuple[float, float] = ride_info.get("start_coords")
end_coords: Tuple[float, float] = ride_info.get("end_coords")
progress: float = float(active_ride.get("progress") or 0.0)

# Booking status
if booking_info.get("status") in ("pending", "locked_by_driver"):
    st.info("⏳ Waiting for a driver to accept your ride...")
    time.sleep(5)
    st.rerun()

st.info(f"Tracking **{booking_info['type']}** driven by **{booking_info['driver']}** 🚘")

st.markdown(
    f"""
**🧭 Ride Details:**
- **Pickup:** {ride_info['start']}
- **Destination:** {ride_info['end']}
- **Current Fare:** ₹{booking_info['fare']:.2f}
"""
)

# ====== Update Route Section ======
with st.expander("✏️ Change Destination"):
    new_start = st.text_input("Change Start Location:", ride_info["start"])
    new_end = st.text_input("Change Destination:", ride_info["end"])
    if st.button("Update Locations"):
        try:
            updated = update_route(new_start, new_end, booking_info)
            db_utils.update_ride_route(active_ride["id"], updated)
            st.success(
                f"✅ Route updated! New distance: {updated['distance_km']:.2f} km, "
                f"New Fare: ₹{updated['fare']:.2f}"
            )
            st.rerun()
        except ValueError as err:
            st.error(f"❌ {str(err)}")

# ====== Ride Progress Section ======
if progress == 0.0:
    st.markdown("Your driver is on the way to pick you up!")
elif progress < 1.0:
    st.markdown("Ride in progress...")
else:
    st.success("🎉 Ride Completed! Thank you for choosing RelaxiTaxi.")
    st.balloons()
    db_utils.update_ride_status(active_ride["id"], "completed")
    time.sleep(2)
    goto("pages/payment_ui.py")

curr_location = simulate_driver_position(start_coords, end_coords, progress)
st.progress(progress, text=f"Ride Progress: {progress * 100:.0f}%")

# ====== Cancel Ride ======
if progress == 0.0 and st.button("🚫 Cancel Ride"):
    db_utils.update_ride_status(active_ride["id"], "cancelled")
    st.warning("❌ Ride cancelled successfully!")
    st.rerun()

# ====== Map Display ======
map_obj = folium.Map(location=curr_location, zoom_start=13, tiles="CartoDB dark_matter")
folium.Marker(start_coords, tooltip="Start", icon=folium.Icon(color="green")).add_to(map_obj)
folium.Marker(end_coords, tooltip="Destination", icon=folium.Icon(color="red")).add_to(map_obj)
folium.Marker(
    curr_location,
    tooltip="Driver",
    icon=folium.Icon(color="blue", icon="car", prefix="fa"),
).add_to(map_obj)

st_folium(map_obj, width=700, height=500, key="track_ride_map")

time.sleep(5)
st.rerun()
