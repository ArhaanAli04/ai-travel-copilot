from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FlightBase(BaseModel):
    """Base flight schema with common fields"""
    airline: str
    airline_code: Optional[str] = None
    airline_logo: Optional[str] = None
    flight_number: str
    departure_airport: str
    arrival_airport: str
    departure_city: str
    arrival_city: str
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    stops: int = 0
    layover_airports: Optional[List[str]] = None
    cabin_class: str = "economy"
    price_amount: float
    price_currency: str = "USD"
    booking_url: Optional[str] = None
    aircraft_type: Optional[str] = None
    baggage_allowance: Optional[dict] = None
    amenities: Optional[List[str]] = None
    source: str = "serpapi"  # ✅ ADDED
    flight_direction: str = "one_way"
    
    class Config:
        from_attributes = True


class FlightSearchResponse(FlightBase):
    """Response for flight search (not yet saved to DB)"""
    pass


class FlightSelect(BaseModel):
    """Request to select/book a flight"""
    flight_data: FlightBase
    notes: Optional[str] = None


class FlightResponse(FlightBase):
    """Response for saved flight (includes DB fields)"""
    id: int
    trip_id: int
    trip_day_id: Optional[int] = None
    is_selected: bool = True
    booking_reference: Optional[str] = None
    
    class Config:
        from_attributes = True


class FlightSearchRequest(BaseModel):
    """Request to search for flights"""
    origin: str = Field(..., description="Origin airport code (e.g., BOM)")
    destination: str = Field(..., description="Destination airport code (e.g., DEL)")
    departure_date: str = Field(..., description="Departure date (YYYY-MM-DD)")
    return_date: Optional[str] = Field(None, description="Return date for round trips (YYYY-MM-DD)")
    passengers: int = Field(1, ge=1, le=9, description="Number of passengers")
    cabin_class: str = Field("economy", description="Cabin class: economy, premium_economy, business, first")
    max_stops: Optional[int] = Field(None, ge=0, le=3, description="Maximum number of stops")
    max_price: Optional[float] = Field(None, description="Maximum price filter")
    
    class Config:
        json_schema_extra = {
            "example": {
                "origin": "BOM",
                "destination": "CDG",
                "departure_date": "2026-03-15",
                "passengers": 2,
                "cabin_class": "economy",
                "max_stops": 1
            }
        }
