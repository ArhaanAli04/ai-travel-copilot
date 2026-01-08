from fastapi import APIRouter, Depends, HTTPException, Path,Query
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
from app.services.flight_service import search_flights_serpapi,get_city_name
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trips", tags=["Flights"])

@router.post("/{trip_id}/flights/search", response_model=List[FlightSearchResponse])
async def search_flights(
    trip_id: int = Path(..., description="Trip ID"),
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
        raise HTTPException(status_code=500, detail=f"Failed to search flights: {str(e)}")


@router.post("/{trip_id}/flights/select", response_model=FlightResponse, status_code=201)
async def select_flight(
    trip_id: int = Path(..., description="Trip ID"),
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


@router.get("/{trip_id}/flights", response_model=List[FlightResponse])
async def get_trip_flights(
    trip_id: int = Path(..., description="Trip ID"),
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


def get_airport_code(city_name: str) -> str:
    """Convert city name to airport code (mock mapping)"""
    airport_map = {
        "mumbai": "BOM",
        "delhi": "DEL",
        "paris": "CDG",
        "rome": "FCO",
        "barcelona": "BCN",
        "london": "LHR",
        "new york": "JFK",
        "dubai": "DXB",
        "singapore": "SIN",
        "tokyo": "HND",
    }
    return airport_map.get(city_name.lower(), "XXX")

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

