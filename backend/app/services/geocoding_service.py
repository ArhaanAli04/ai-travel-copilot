"""
Geocoding Service - Converts location names to coordinates
Uses Mapbox as primary, Nominatim (OSM) as fallback
Dynamic city proximity bias — works for any city worldwide
"""
import httpx
import asyncio
import logging
from typing import Optional, Dict
from urllib.parse import quote

logger = logging.getLogger(__name__)

MAPBOX_GEOCODING_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# In-memory caches
_geocode_cache: Dict[str, Optional[Dict]] = {}
_city_center_cache: Dict[str, Optional[tuple]] = {}


async def _get_city_center(city: str, token: str) -> Optional[tuple]:
    """
    Dynamically get lng/lat center of any city.
    Cached per session — only geocoded once per city.
    Returns (lng, lat) or None.
    """
    key = city.lower().strip()
    if key in _city_center_cache:
        return _city_center_cache[key]

    # Try Mapbox
    if token:
        encoded = quote(city)
        url = f"{MAPBOX_GEOCODING_URL}/{encoded}.json"
        params = {
            "access_token": token,
            "limit": 1,
            "types": "place,locality,region",
            "language": "en",
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, params=params)
                features = response.json().get("features", [])
                if features:
                    lng, lat = features[0]["geometry"]["coordinates"]
                    _city_center_cache[key] = (lng, lat)
                    logger.info(f"🌍 City center for '{city}': ({lng:.4f}, {lat:.4f})")
                    return (lng, lat)
        except Exception as e:
            logger.warning(f"⚠️ Mapbox city center lookup failed for '{city}': {e}")

    # Fallback: Nominatim
    try:
        params = {
            "q": city,
            "format": "json",
            "limit": 1,
            "featuretype": "city",
        }
        headers = {"User-Agent": "AITravelCopilot/1.0 (travel-copilot@example.com)"}
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(NOMINATIM_URL, params=params, headers=headers)
            data = response.json()
            if data:
                lng = float(data[0]["lon"])
                lat = float(data[0]["lat"])
                _city_center_cache[key] = (lng, lat)
                logger.info(f"🌍 City center (Nominatim) for '{city}': ({lng:.4f}, {lat:.4f})")
                return (lng, lat)
    except Exception as e:
        logger.warning(f"⚠️ Nominatim city center fallback failed for '{city}': {e}")

    _city_center_cache[key] = None
    return None


async def geocode_location(
    location: str,
    city: str,
    mapbox_token: str = ""
) -> Optional[Dict[str, float]]:
    """
    Convert a location name + city to lat/lng coordinates.
    Strategy:
    1. Check in-memory cache
    2. Try Mapbox with dynamic city proximity bias (primary)
    3. Fallback to Nominatim
    """
    if not location:
        return None

    cache_key = f"{location.lower()}|{city.lower()}"
    if cache_key in _geocode_cache:
        return _geocode_cache[cache_key]

    result = None

    # Primary: Mapbox
    if mapbox_token:
        result = await _mapbox_geocode(location, city, mapbox_token)

    # Fallback: Nominatim
    if not result:
        result = await _nominatim_geocode(location, city)

    _geocode_cache[cache_key] = result

    if result:
        logger.info(f"📍 Geocoded '{location}' in {city} → {result}")
    else:
        logger.warning(f"⚠️ Could not geocode '{location}' in {city}")

    return result


async def _mapbox_geocode(
    location: str,
    city: str,
    token: str
) -> Optional[Dict[str, float]]:
    """Query Mapbox Geocoding API with dynamic city proximity bias"""
    query = f"{location}, {city}"
    encoded_query = quote(query)
    url = f"{MAPBOX_GEOCODING_URL}/{encoded_query}.json"

    params = {
        "access_token": token,
        "limit": 1,
        "types": "poi,address,place",
        "language": "en",
    }

    # Dynamically fetch city center for proximity bias
    city_center = await _get_city_center(city, token)
    if city_center:
        params["proximity"] = f"{city_center[0]},{city_center[1]}"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params)
            features = response.json().get("features", [])
            if features:
                lng, lat = features[0]["geometry"]["coordinates"]
                return {"lat": lat, "lng": lng}
    except Exception as e:
        logger.warning(f"⚠️ Mapbox geocoding failed for '{location}': {e}")
    return None


async def _nominatim_geocode(
    location: str,
    city: str
) -> Optional[Dict[str, float]]:
    """Query Nominatim OSM geocoding API (fallback)"""
    params = {
        "q": f"{location}, {city}",
        "format": "json",
        "limit": 1,
        "addressdetails": 0,
        "bounded": 1,
    }
    headers = {"User-Agent": "AITravelCopilot/1.0 (travel-copilot@example.com)"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(NOMINATIM_URL, params=params, headers=headers)
            data = response.json()
            if data:
                return {
                    "lat": float(data[0]["lat"]),
                    "lng": float(data[0]["lon"])
                }
    except Exception as e:
        logger.warning(f"⚠️ Nominatim fallback failed for '{location}': {e}")
    return None


async def geocode_activities_batch(
    activities: list,
    mapbox_token: str = "",
    delay_seconds: float = 0.2
) -> None:
    """
    Geocode a batch of (activity, city) tuples in-place.
    Modifies activity.coordinates directly.
    """
    for activity, city in activities:
        if activity.coordinates:
            continue

        if not activity.location:
            continue

        coords = await geocode_location(
            location=activity.location,
            city=city,
            mapbox_token=mapbox_token
        )

        if coords:
            activity.coordinates = coords

        await asyncio.sleep(delay_seconds)
