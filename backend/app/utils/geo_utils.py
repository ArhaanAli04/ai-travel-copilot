"""
Geospatial utility functions for location-based calculations
"""
from typing import Dict, List, Tuple
import math


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula
    
    Args:
        lat1: Latitude of point 1
        lon1: Longitude of point 1
        lat2: Latitude of point 2
        lon2: Longitude of point 2
    
    Returns:
        Distance in kilometers
    """
    # Earth's radius in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    
    return distance


def get_bounding_box(lat: float, lon: float, radius_km: float) -> Dict[str, float]:
    """
    Calculate bounding box for a given center point and radius
    
    Args:
        lat: Center latitude
        lon: Center longitude
        radius_km: Radius in kilometers
    
    Returns:
        Dictionary with min/max lat/lon
    """
    # Approximate degrees per kilometer
    lat_degree_km = 111.0  # 1 degree latitude ≈ 111 km
    lon_degree_km = 111.0 * math.cos(math.radians(lat))  # Varies by latitude
    
    lat_delta = radius_km / lat_degree_km
    lon_delta = radius_km / lon_degree_km
    
    return {
        "min_lat": lat - lat_delta,
        "max_lat": lat + lat_delta,
        "min_lon": lon - lon_delta,
        "max_lon": lon + lon_delta,
    }


def parse_location_string(location_str: str) -> Tuple[float, float]:
    """
    Parse location string into lat/lon coordinates
    
    Args:
        location_str: Location string in format "lat,lon" or "location_name"
    
    Returns:
        Tuple of (latitude, longitude)
    
    Raises:
        ValueError: If location string is invalid
    """
    try:
        parts = location_str.split(",")
        if len(parts) == 2:
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
            return lat, lon
        else:
            raise ValueError(f"Invalid location format: {location_str}")
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Could not parse location: {location_str}") from e


def format_distance(distance_km: float) -> str:
    """
    Format distance in human-readable format
    
    Args:
        distance_km: Distance in kilometers
    
    Returns:
        Formatted string (e.g., "1.2 km", "500 m")
    """
    if distance_km < 1:
        meters = int(distance_km * 1000)
        return f"{meters} m"
    else:
        return f"{distance_km:.1f} km"


# City center coordinates (for reference)
CITY_COORDINATES = {
    "mumbai": {"lat": 19.0760, "lon": 72.8777, "name": "Mumbai"},
    "delhi": {"lat": 28.7041, "lon": 77.1025, "name": "Delhi"},
    "goa": {"lat": 15.2993, "lon": 74.1240, "name": "Goa"},
    "bangalore": {"lat": 12.9716, "lon": 77.5946, "name": "Bangalore"},
    "kolkata": {"lat": 22.5726, "lon": 88.3639, "name": "Kolkata"},
    "chennai": {"lat": 13.0827, "lon": 80.2707, "name": "Chennai"},
    "hyderabad": {"lat": 17.3850, "lon": 78.4867, "name": "Hyderabad"},
    "pune": {"lat": 18.5204, "lon": 73.8567, "name": "Pune"},
    "jaipur": {"lat": 26.9124, "lon": 75.7873, "name": "Jaipur"},
    "agra": {"lat": 27.1767, "lon": 78.0081, "name": "Agra"},
}


def get_city_coordinates(city: str) -> Dict[str, float]:
    """
    Get coordinates for a known city
    
    Args:
        city: City name (case-insensitive)
    
    Returns:
        Dictionary with lat, lon, and name
    
    Raises:
        ValueError: If city not found
    """
    city_lower = city.lower().strip()
    
    if city_lower in CITY_COORDINATES:
        return CITY_COORDINATES[city_lower]
    else:
        raise ValueError(f"City '{city}' not found in coordinates database")


def is_point_in_radius(
    center_lat: float,
    center_lon: float,
    point_lat: float,
    point_lon: float,
    radius_km: float
) -> bool:
    """
    Check if a point is within a given radius of a center point
    
    Args:
        center_lat: Center latitude
        center_lon: Center longitude
        point_lat: Point latitude
        point_lon: Point longitude
        radius_km: Radius in kilometers
    
    Returns:
        True if point is within radius, False otherwise
    """
    distance = calculate_distance(center_lat, center_lon, point_lat, point_lon)
    return distance <= radius_km
