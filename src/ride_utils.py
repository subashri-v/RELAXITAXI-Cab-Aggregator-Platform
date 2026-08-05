"""
Utility functions for RelaxiTaxi ride calculations.
Contains helper methods for distance and fare computation.
"""

from geopy.distance import geodesic
from geopy.geocoders import Nominatim


def calculate_distance(start_coords, end_coords):
    """Calculate distance (in km) between two coordinate pairs."""
    try:
        if not start_coords or not end_coords:
            return None
        return round(geodesic(start_coords, end_coords).kilometers, 2)
    except Exception:
        # In case of invalid coordinates or types
        return None


def calculate_fare(distance_km, ac=True):
    """Calculate fare based on distance (in km) and cab type."""
    if not isinstance(distance_km, (int, float)):
        raise TypeError("Distance must be a number")

    if distance_km < 0:
        raise ValueError("Distance cannot be negative")

    base_fare = 60 if ac else 40
    per_km = 20 if ac else 15
    return round(base_fare + (per_km * distance_km), 2)

def get_coordinates(location_name):
    """Return (latitude, longitude) tuple for a given location name."""
    geolocator = Nominatim(user_agent="relaxitaxi_utils", timeout=10)
    location = geolocator.geocode(location_name)
    if location:
        return (location.latitude, location.longitude)
    return None
