import sys
import os
# Ensure the source directory is on the path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.ride_utils import calculate_distance, calculate_fare, get_coordinates

def test_end_to_end_distance_and_fare():
    """Test successful distance calculation and AC fare."""
    start = (12.9716, 77.5946)
    end = (13.0827, 80.2707)
    distance = calculate_distance(start, end)
    fare = calculate_fare(distance, ac=True)
    
    assert distance == 290.54
    assert fare == 5870.8


def test_calculate_distance_with_none_input():
    """Test distance calculation with None input."""
    assert calculate_distance(None, (1, 1)) is None
    assert calculate_distance((1, 1), None) is None
    assert calculate_distance(None, None) is None

def test_calculate_distance_invalid_coords_exception():
    """Test distance calculation with invalid coordinate types (exception block)."""
    # This should trigger the 'except Exception' block
    assert calculate_distance("invalid", "coords") is None

def test_calculate_fare_non_ac():
    """Test fare calculation for Non-AC ride (Lines 35-39)."""
    # Base fare 40 + (15 * 10 km) = 190.00
    fare = calculate_fare(10.0, ac=False)
    assert fare == 190.00

def test_calculate_fare_type_error():
    """Test fare calculation with non-numeric distance (Line 24)."""
    with pytest.raises(TypeError, match="Distance must be a number"):
        calculate_fare("ten", ac=True)

def test_calculate_fare_value_error():
    """Test fare calculation with negative distance (Line 27)."""
    with pytest.raises(ValueError, match="Distance cannot be negative"):
        calculate_fare(-5.0, ac=True)

def test_get_coordinates_location_not_found():
    """Test get_coordinates when location is not found (Line 39)."""
    # Use a highly improbable location name
    coords = get_coordinates("asdfjklghjqwertyuiop-nonexistent-location-12345")
    assert coords is None
