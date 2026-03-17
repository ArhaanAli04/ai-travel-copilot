from datetime import datetime
from typing import List, Optional
from serpapi import GoogleSearch
from app.schemas.flight import FlightSearchResponse
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# 

def search_flights_serpapi(
    origin: str,
    destination: str,
    departure_date: str,
    cabin_class: str = "economy",
    max_stops: Optional[int] = None,
    passengers: int = 1,
    return_date: Optional[str] = None,
    trip_type: str = "one_way",
    currency: str = "USD", 
) -> List[FlightSearchResponse]:
    """
    Search real flights using SerpAPI Google Flights API
    For round trips, searches both directions separately
    """
    
    if not settings.SERPAPI_KEY:
        logger.error("❌ SERPAPI_KEY not configured")
        raise ValueError("SerpAPI key not configured. Add SERPAPI_KEY to .env file")
    
    # For round trips, search both directions
    if trip_type == "round_trip" and return_date:
        logger.info(f"🔍 Searching round-trip: {origin} ⇄ {destination}")
        
        # Search outbound flights
        outbound_flights = _search_one_way_flights(
            origin, destination, departure_date, 
            cabin_class, max_stops, passengers, "outbound",
            currency=currency,
        )
        
        # Search return flights
        return_flights = _search_one_way_flights(
            destination, origin, return_date,
            cabin_class, max_stops, passengers, "return",
            currency=currency,
        )
        
        # Combine both
        all_flights = outbound_flights + return_flights
        logger.info(f"✅ Found {len(outbound_flights)} outbound + {len(return_flights)} return flights")
        return all_flights
    
    else:
        # One-way flight search
        return _search_one_way_flights(
            origin, destination, departure_date,
            cabin_class, max_stops, passengers, "one_way",
            currency=currency,
        )


def _search_one_way_flights(
    origin: str,
    destination: str, 
    departure_date: str,
    cabin_class: str,
    max_stops: Optional[int],
    passengers: int,
    flight_direction: str = "one_way",  # "outbound", "return", or "one_way"
    currency: str = "USD",
) -> List[FlightSearchResponse]:
    """Internal function to search one-way flights"""
    
    travel_class_map = {
        "economy": "1",
        "premium_economy": "2",
        "business": "3",
        "first": "4"
    }
    
    # ✅ FIX: Handle City IDs (/m/...) vs IATA Codes
    # Only uppercase if it looks like a standard 3-letter IATA code
    dep_id = origin.upper() if len(origin) == 3 else origin
    arr_id = destination.upper() if len(destination) == 3 else destination

    params = {
        "engine": "google_flights",
        "departure_id": dep_id,
        "arrival_id": arr_id,
        "outbound_date": departure_date,
        "currency": currency,
        "hl": "en",
        "adults": passengers,
        "type": "2",  # Always one-way for this search
        "travel_class": travel_class_map.get(cabin_class, "1"),
        "api_key": settings.SERPAPI_KEY
    }
    
    if max_stops is not None:
        params["stops"] = max_stops
    
    logger.info(f"🔍 Searching {flight_direction} flights: {dep_id} → {arr_id} on {departure_date}")
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "error" in results:
            logger.error(f"❌ SerpAPI error: {results['error']}")
            raise Exception(f"SerpAPI error: {results['error']}")
        
        best_flights = results.get("best_flights", [])
        other_flights = results.get("other_flights", [])
        
        all_flights = best_flights + other_flights
        all_flights = all_flights[:5]  # Limit to 5 flights per direction
        
        if not all_flights:
            logger.warning(f"⚠️ No flights found")
            return []
        
        parsed_flights = []
        for flight_data in all_flights:
            try:
                # parsed_flight handles the extraction of specific airports from the result
                parsed_flight = parse_serpapi_flight(flight_data,currency=currency)
                if parsed_flight:
                    # Add direction indicator
                    parsed_flight.flight_direction = flight_direction
                    parsed_flights.append(parsed_flight)
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse flight: {e}")
                continue
        
        return parsed_flights
        
    except Exception as e:
        logger.error(f"❌ Failed to search flights: {e}")
        raise Exception(f"Failed to search flights: {str(e)}")


def parse_serpapi_flight(flight_data: dict, currency: str = "USD") -> Optional[FlightSearchResponse]:
    """
    Parse SerpAPI flight data into our FlightSearchResponse schema
    """
    try:
        # Get first leg (main flight segment)
        flights = flight_data.get("flights", [])
        if not flights:
            return None
        
        first_leg = flights[0]
        last_leg = flights[-1]
        
        # Extract airline info
        airline = first_leg.get("airline", "Unknown")
        airline_logo = first_leg.get("airline_logo")
        flight_number = first_leg.get("flight_number", "")
        
        # Extract departure info
        # Note: Even if we searched by City ID, the result here will be a specific airport (e.g. LHR)
        departure_airport_code = first_leg.get("departure_airport", {}).get("id")
        departure_airport_name = first_leg.get("departure_airport", {}).get("name", "")
        departure_time_str = first_leg.get("departure_airport", {}).get("time", "")
        departure_time = datetime.fromisoformat(departure_time_str.replace("Z", "+00:00"))

        # Extract arrival info  
        arrival_airport_code = last_leg.get("arrival_airport", {}).get("id")
        arrival_airport_name = last_leg.get("arrival_airport", {}).get("name", "")
        arrival_time_str = last_leg.get("arrival_airport", {}).get("time", "")
        arrival_time = datetime.fromisoformat(arrival_time_str.replace("Z", "+00:00"))

        # Get clean city names
        # We rely on the helper, but if it fails, we fall back to the airport name to avoid empty fields
        departure_city = get_city_name(departure_airport_code)
        if departure_city == departure_airport_code:
             # Fallback: extract city from airport name if possible (e.g. "Heathrow Airport" -> "London")
             # This is a basic heuristic; a real app might use a geocoding DB.
             departure_city = departure_airport_name.split(" ")[0] if departure_airport_name else departure_airport_code

        arrival_city = get_city_name(arrival_airport_code)
        if arrival_city == arrival_airport_code:
             arrival_city = arrival_airport_name.split(" ")[0] if arrival_airport_name else arrival_airport_code

        
        # Calculate duration
        duration_minutes = flight_data.get("total_duration", 0)
        
        # Get number of stops
        stops = len(flights) - 1
        layover_airports = []
        if stops > 0:
            for i in range(1, len(flights)):
                layover_code = flights[i].get("departure_airport", {}).get("id")
                if layover_code:
                    layover_airports.append(layover_code)
        
        # Get price
        price = flight_data.get("price", 0)
        # Skip flights with no price
        if price == 0:
            return None
        # Get travel class
        travel_class = first_leg.get("travel_class", "Economy").lower().replace(" ", "_")
        
        # Extract amenities
        amenities = []
        if first_leg.get("often_delayed_by_over_30_min") is False:
            amenities.append("on_time")
        if stops == 0:
            amenities.append("nonstop")
        
        extensions = flight_data.get("extensions", [])
        for ext in extensions:
            ext_lower = ext.lower()
            if "wifi" in ext_lower:
                amenities.append("wifi")
            if "carbon" in ext_lower:
                amenities.append("low_emissions")
        
        # Baggage (estimate based on class)
        baggage_allowance = {
            "carry_on": "7kg",
            "checked": "23kg" if "business" in travel_class or "first" in travel_class else "20kg"
        }
        
        # Aircraft type
        aircraft_type = first_leg.get("airplane", "Unknown")
        
        # Booking URL (if available)
        booking_url = flight_data.get("booking_url", f"https://www.google.com/travel/flights")
        
        # Create flight response
        return FlightSearchResponse(
            airline=airline,
            airline_code=first_leg.get("airline_code"),
            airline_logo=airline_logo,
            flight_number=flight_number,
            departure_airport=departure_airport_code,
            arrival_airport=arrival_airport_code,
            departure_city=departure_city,
            arrival_city=arrival_city,
            departure_time=departure_time,
            arrival_time=arrival_time,
            duration_minutes=duration_minutes,
            stops=stops,
            layover_airports=layover_airports if layover_airports else None,
            cabin_class=travel_class,
            price_amount=float(price),
            price_currency=currency,
            booking_url=booking_url,
            aircraft_type=aircraft_type,
            baggage_allowance=baggage_allowance,
            amenities=amenities if amenities else None,
            source="serpapi"
        )
        
    except Exception as e:
        logger.error(f"❌ Error parsing flight: {e}")
        return None


def get_city_name(airport_code: str) -> str:
    """
    Map airport codes to city names.
    Expanded slightly, but now serves as a 'best effort' mapper.
    """
    if not airport_code:
        return ""
        
    city_map = {
        "BOM": "Mumbai", "DEL": "Delhi", "BLR": "Bangalore", "MAA": "Chennai",
        "CDG": "Paris", "ORY": "Paris",
        "FCO": "Rome", "CIA": "Rome",
        "LHR": "London", "LGW": "London", "STN": "London", "LCY": "London",
        "JFK": "New York", "EWR": "New York", "LGA": "New York",
        "DXB": "Dubai", "AUH": "Abu Dhabi",
        "SIN": "Singapore",
        "HND": "Tokyo", "NRT": "Tokyo",
        "SYD": "Sydney", "MEL": "Melbourne",
        "LAX": "Los Angeles", "SFO": "San Francisco", "SEA": "Seattle",
        "ORD": "Chicago", "MIA": "Miami", "ATL": "Atlanta"
    }
    return city_map.get(airport_code.upper(), airport_code.upper())

def search_airports(query: str) -> List[dict]:
    """
    Search for airports/cities using SerpAPI Google Flights Autocomplete
    Returns: List of suggestions with id (IATA or Knowledge Graph ID), name, and type
    """
    
    if not settings.SERPAPI_KEY:
        logger.error("❌ SERPAPI_KEY not configured")
        return []
    
    if len(query) < 2:
        return []
    
    params = {
        "engine": "google_flights_autocomplete",
        "q": query,
        "api_key": settings.SERPAPI_KEY,
        "hl": "en",
        "gl": "us"
    }
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # SerpAPI often returns 'suggestions', but sometimes 'airport_suggestions'
        suggestions = results.get("suggestions", results.get("airport_suggestions", []))
        
        formatted = []
        for item in suggestions[:10]:
            # Google Flights Autocomplete returns 'id' (IATA or /m/xxx) and 'name'
            
            # Determine if it is a specific airport or a city (All Airports)
            # Cities usually start with '/m/'
            is_city = item.get("id", "").startswith("/m/")
            
            formatted.append({
                "code": item.get("id"),
                "name": item.get("value", item.get("name")),
                "city": item.get("value", item.get("name")), 
                "country": item.get("country"),
                "type": "City" if is_city else "Airport",
                "display": f"{item.get('value')} ({item.get('id')})"
            })
        
        logger.info(f"✅ Found {len(formatted)} locations for query: {query}")
        return formatted
        
    except Exception as e:
        logger.error(f"❌ Failed to search airports: {e}")
        return []