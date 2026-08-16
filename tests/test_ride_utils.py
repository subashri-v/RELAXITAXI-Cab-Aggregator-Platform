import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from src.ride_utils import calculate_distance, calculate_fare, get_coordinates, estimate_eta_minutes

def test_calculate_fare_non_ac():
    assert calculate_fare(10, ac=False) == 40 + 15 * 10

def test_calculate_fare_ac():
    assert calculate_fare(5, ac=True) == 60 + 20 * 5

def test_negative_distance_raises():
    with pytest.raises(ValueError):
        calculate_fare(-5)

def test_calculate_distance():
    d = calculate_distance((12.9716, 77.5946), (13.0827, 80.2707))
    assert abs(d - 291.0) < 1.0  # within 1 km tolerance

def test_calculate_distance_invalid_input():
    """Test distance calculation when invalid coordinates are given."""
    # The function is designed to handle this by returning None due to the try/except block
    d = calculate_distance(("invalid", "coords"), (13.0, 77.0))
    assert d is None

def test_calculate_fare_invalid_type():
    """Test that calculate_fare raises TypeError for invalid distance input."""
    with pytest.raises(TypeError):
        calculate_fare("Luxury", 10)

def test_calculate_distance_empty_coords():
    """Test distance calculation when one or both coordinates are missing."""
    assert calculate_distance(None, (13.0, 77.0)) is None
    assert calculate_distance((12.9, 77.5), None) is None

def test_calculate_distance_exception_handling(monkeypatch):
    """Force an exception inside calculate_distance to cover the except block."""
    from src.ride_utils import calculate_distance # Already imported at the top, but safe to keep

    # Monkeypatch geodesic to raise an exception
    def mock_geodesic(a, b):
        raise Exception("Simulated failure")

    # FIX: Import the module using its correct package path (src.ride_utils)
    import src.ride_utils as ride_utils_module
    
    # Use the alias to monkeypatch the function within the correct module
    monkeypatch.setattr(ride_utils_module, "geodesic", mock_geodesic)

    # Now call it — should handle the exception and return None
    result = calculate_distance((12.9, 77.5), (13.0, 80.2))
    assert result is None

def test_estimate_eta_scales_with_distance():
    assert estimate_eta_minutes(25, avg_speed_kmph=25) == 60
    assert estimate_eta_minutes(50, avg_speed_kmph=25) == 120

def test_estimate_eta_minimum_one_minute():
    assert estimate_eta_minutes(0.01, avg_speed_kmph=25) == 1

def test_estimate_eta_invalid_distance_defaults_to_one():
    assert estimate_eta_minutes(0) == 1
    assert estimate_eta_minutes(-5) == 1
    assert estimate_eta_minutes(None) == 1
    assert estimate_eta_minutes("far") == 1
