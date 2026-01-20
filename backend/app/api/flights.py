from fastapi import APIRouter, Depends, HTTPException,Query
from fastapi import Path as PathParam
from sqlalchemy.orm import Session
from typing import List
from app.core.postgres import get_db
from app.models.trip import Trip
from app.models.flight import Flight
from app.schemas.flight import (
    FlightSearchRequest, 
    FlightSearchResponse, 
    FlightSelect,
    FlightResponse
)
from app.services.flight_service import search_flights_serpapi,search_airports,get_city_name
import logging
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trips", tags=["Flights"])


# Load airports data once at module level
AIRPORTS_DATA = None

def load_airports_data():
    """Load airports data from JSON file (cached)"""
    global AIRPORTS_DATA
    if AIRPORTS_DATA is None:
        airports_file = Path(__file__).parent.parent / "data" / "airports.json"
        with open(airports_file, 'r', encoding='utf-8') as f:
            AIRPORTS_DATA = json.load(f)
    return AIRPORTS_DATA

def get_airport_code(city_or_code: str) -> str:
    """
    Convert city name to IATA airport code or Google Knowledge Graph ID (/m/...)
    Prioritizes SerpAPI for city resolution to handle 'All Airports' correctly.
    """
    if not city_or_code:
        raise HTTPException(status_code=400, detail="City or airport code is required")
    
    city_or_code = city_or_code.strip()
    
    # 1. Fast Path: If it looks like a 3-letter IATA code, use it directly.
    # We assume standard IATA codes are 3 uppercase letters.
    if len(city_or_code) == 3 and city_or_code.isalpha():
        return city_or_code.upper()
    
    # 2. SerpAPI Search: Ask Google what this place is.
    # This returns specific airports (JFK) OR City IDs (/m/02_286)
    try:
        logger.info(f"🔍 Resolving location via SerpAPI: {city_or_code}")
        results = search_airports(city_or_code)
        
        if results:
            # Prefer the first result as it is the most relevant according to Google
            best_match = results[0]
            code = best_match["code"] # This might be "LHR" or "/m/04jpl"
            name = best_match["name"]
            
            logger.info(f"✅ Resolved '{city_or_code}' → {code} ({name})")
            return code
            
    except Exception as e:
        logger.warning(f"⚠️ SerpAPI resolution failed: {e}")

    # 3. Fallback / Error
    # If we couldn't resolve it, we can't search for flights.
    raise HTTPException(
        status_code=400, 
        detail=f"Could not resolve city/airport for '{city_or_code}'"
    )


@router.post("/{trip_id}/flights/search", response_model=List[FlightSearchResponse])
async def search_flights(
    trip_id: int = PathParam(..., description="Trip ID"),
    search_params: FlightSearchRequest = None,
    db: Session = Depends(get_db)
):
    """
    Search for flights using SerpAPI
    Supports one-way and round-trip searches
    """
    try:
        # Verify trip exists
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")
        
        # Use trip data if search params not provided
        if not search_params:
            # Auto-generate search from trip data
            if not trip.destinations or len(trip.destinations) == 0:
                raise HTTPException(status_code=400, detail="Trip has no destinations")
            
            origin_code = get_airport_code(trip.origin)
            dest_code = get_airport_code(trip.destinations[0])
            
            #  Extract trip_type from flight_preferences
            trip_type = "one_way"
            return_date = None
            
            if trip.flight_preferences:
                trip_type = trip.flight_preferences.get("trip_type", "one_way")
                # If round trip, use end_date as return date
                if trip_type == "round_trip":
                    return_date = trip.end_date.strftime("%Y-%m-%d")
            
            search_params = FlightSearchRequest(
                origin=origin_code,
                destination=dest_code,
                departure_date=trip.start_date.strftime("%Y-%m-%d"),
                return_date=return_date,  #  Pass return date
                passengers=trip.traveler_count,
                cabin_class=trip.flight_preferences.get("cabin_class", "economy") if trip.flight_preferences else "economy",
                max_stops=trip.flight_preferences.get("max_stops") if trip.flight_preferences else None
            )
        else:
            search_params.origin = get_airport_code(search_params.origin)
            search_params.destination = get_airport_code(search_params.destination)    
        
        #  Determine trip type from search params
        trip_type = "one_way"
        if search_params.return_date:
            trip_type = "round_trip"
        
        logger.info(f"Searching {trip_type} flights: {search_params.origin} → {search_params.destination}")
        
        # Search flights using SerpAPI
        flights = search_flights_serpapi(
            origin=search_params.origin,
            destination=search_params.destination,
            departure_date=search_params.departure_date,
            cabin_class=search_params.cabin_class,
            max_stops=search_params.max_stops,
            passengers=search_params.passengers,
            return_date=search_params.return_date,  #  Pass return date
            trip_type=trip_type  # Pass trip type
        )
        
        logger.info(f"Found {len(flights)} real flights for trip {trip_id}")
        return flights
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to search flights: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to search flights: {str(e)}")


@router.post("/{trip_id}/flights/select", response_model=FlightResponse, status_code=201)
async def select_flight(
    trip_id: int = PathParam(..., description="Trip ID"),
    flight_select: FlightSelect = None,
    db: Session = Depends(get_db)
):
    """
    Select and save a flight to the trip
    """
    try:
        # Verify trip exists
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")
        
        # Create flight record
        flight_data = flight_select.flight_data
        
        db_flight = Flight(
            trip_id=trip_id,
            airline=flight_data.airline,
            airline_code=flight_data.airline_code,
            flight_number=flight_data.flight_number,
            departure_airport=flight_data.departure_airport,
            arrival_airport=flight_data.arrival_airport,
            departure_city=flight_data.departure_city,
            arrival_city=flight_data.arrival_city,
            departure_time=flight_data.departure_time,
            arrival_time=flight_data.arrival_time,
            duration_minutes=flight_data.duration_minutes,
            stops=flight_data.stops,
            layover_airports=flight_data.layover_airports,
            cabin_class=flight_data.cabin_class,
            price_amount=flight_data.price_amount,
            price_currency=flight_data.price_currency,
            is_selected=True,
            booking_url=flight_data.booking_url,
            aircraft_type=flight_data.aircraft_type,
            baggage_allowance=flight_data.baggage_allowance,
            amenities=flight_data.amenities,
            source=flight_data.source
        )
        
        db.add(db_flight)
        db.commit()
        db.refresh(db_flight)
        
        logger.info(f"✅ Selected flight {db_flight.id} for trip {trip_id}")
        return db_flight
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to select flight: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to select flight: {str(e)}")

@router.delete("/{trip_id}/flights/{flight_id}", status_code=204)
async def delete_flight(
    trip_id: int = PathParam(..., description="Trip ID"),
    flight_id: int = PathParam(..., description="Flight ID"),
    db: Session = Depends(get_db)
):
    """
    Delete a selected flight from a trip
    """
    try:
        # Verify trip exists
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")
        
        # Verify flight exists and belongs to this trip
        flight = db.query(Flight).filter(
            Flight.id == flight_id,
            Flight.trip_id == trip_id
        ).first()
        
        if not flight:
            raise HTTPException(
                status_code=404,
                detail=f"Flight {flight_id} not found in trip {trip_id}"
            )
        
        # Delete flight
        db.delete(flight)
        db.commit()
        
        logger.info(f"🗑️ Deleted flight {flight_id} from trip {trip_id}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to delete flight: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete flight: {str(e)}"
        )

@router.get("/{trip_id}/flights", response_model=List[FlightResponse])
async def get_trip_flights(
    trip_id: int = PathParam(..., description="Trip ID"),
    db: Session = Depends(get_db)
):
    """
    Get all flights for a trip
    """
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")
        
        flights = db.query(Flight).filter(Flight.trip_id == trip_id).all()
        logger.info(f"📋 Retrieved {len(flights)} flights for trip {trip_id}")
        return flights
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get flights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get flights: {str(e)}")



@router.get("/airports/search", response_model=List[dict])
async def search_airports_endpoint(
    q: str = Query(..., min_length=2, description="Search query"),
):
    """
    Search for airports using autocomplete
    Returns list of matching airports with codes
    """
    try:
        from app.services.flight_service import search_airports
        
        results = search_airports(q)
        return results
        
    except Exception as e:
        logger.error(f"❌ Failed to search airports: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search airports: {str(e)}")

@router.get("/airports/by-city", response_model=List[dict])
async def get_airports_by_city(
    city: str = Query(..., min_length=2, description="City name")
):
    """
    Get all airports for a given city grouped by country
    Returns list of airports with country info for user selection
    """
    try:
        from collections import defaultdict
        
        airports = load_airports_data()
        search_term = city.lower().strip()
        
        # Group airports by country
        country_airports = defaultdict(list)
        
        for code, airport in airports.items():
            if not airport.get("iata"):
                continue
            
            airport_city = airport.get("city", "").lower()
            
            # Exact match only
            if airport_city == search_term:
                country = airport.get("country", "").upper()
                airport_name = airport.get("name", "")
                
                # Skip small airports
                if any(word in airport_name.lower() for word in ["seaplane", "heliport", "ultralight"]):
                    continue
                
                country_airports[country].append({
                    "iata": airport["iata"],
                    "name": airport_name,
                    "city": airport["city"],
                    "country": country,
                    "state": airport.get("state", ""),
                    "elevation": airport.get("elevation", 0)
                })
        
        # Format response
        result = []
        for country, airports_list in country_airports.items():
            # Sort by importance (prefer international, lower elevation)
            airports_list.sort(key=lambda a: (
                "international" not in a["name"].lower(),
                "regional" in a["name"].lower(),
                a["elevation"]
            ))
            
            for airport in airports_list:
                result.append({
                    "code": airport["iata"],
                    "name": airport["name"],
                    "city": airport["city"],
                    "country": country,
                    "state": airport["state"],
                    "display": f"{airport['city']}, {country} ({airport['iata']}) - {airport['name']}"
                })
        
        logger.info(f"📋 Found {len(result)} airports for '{city}' in {len(country_airports)} countries")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to get airports for city: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get airports: {str(e)}")
