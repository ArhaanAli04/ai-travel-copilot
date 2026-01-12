from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from datetime import time as Time
from app.schemas.flight import FlightResponse

# Add this after the imports
class ActivityExplanationResponse(BaseModel):
    """Response for activity explanation"""
    explanation: str
    sources: List[dict] = []
    has_sources: bool
    
    class Config:
        from_attributes = True

# Activity Schemas
class ActivityBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    start_time: Optional[Time] = None  # "09:00"
    end_time: Optional[Time] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    address: Optional[str] = None
    estimated_cost: Optional[float] = None
    order: int
    class Config:
        from_attributes = True
        json_encoders = {
            Time: lambda v: v.strftime("%H:%M") if v else None
        }

class ActivityCreate(ActivityBase):
    trip_day_id: int


class ActivityResponse(ActivityBase):
    id: int
    trip_day_id: int
    source_refs: Optional[dict] = None
    ai_reasoning: Optional[str] = None
    is_booked: bool = False

    class Config:
        from_attributes = True
        json_encoders = {
            Time: lambda v: v.strftime("%H:%M") if v else None
        }


# TripDay Schemas
class TripDayBase(BaseModel):
    day_number: int
    date: date
    city: str
    theme: Optional[str] = None
    description: Optional[str] = None


class TripDayCreate(TripDayBase):
    trip_id: int


class TripDayResponse(TripDayBase):
    id: int
    trip_id: int
    activities: List[ActivityResponse] = []
    # Add weather fields to response
    weather_temp_high: Optional[float] = None
    weather_temp_low: Optional[float] = None
    weather_condition: Optional[str] = None
    weather_icon: Optional[str] = None
    weather_precipitation_prob: Optional[float] = None
    class Config:
        from_attributes = True


# Trip Schemas
class TripBase(BaseModel):
    title: str
    origin: str
    destinations: List[str]
    start_date: datetime
    end_date: datetime
    budget: Optional[float] = None
    budget_currency: str = "USD"
    interests: Optional[List[str]] = None
    preferences: Optional[dict] = None
    trip_type: str = Field(default="solo", pattern="^(solo|couple|family|group)$")
    traveler_count: int = Field(default=1, ge=1)
    traveler_ages: Optional[List[int]] = None
    include_flights: bool = False
    flight_preferences: Optional[dict] = None
    notes: Optional[str] = None


class TripCreate(TripBase):
    pass


class TripUpdate(BaseModel):
    title: Optional[str] = None
    origin: Optional[str] = None
    destinations: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = None
    interests: Optional[List[str]] = None
    preferences: Optional[dict] = None
    trip_type: Optional[str] = None
    traveler_count: Optional[int] = None
    traveler_ages: Optional[List[int]] = None
    include_flights: Optional[bool] = None
    flight_preferences: Optional[dict] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class TripResponse(TripBase):
    id: int
    user_id: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    days: List[TripDayResponse] = []
    flights: List[FlightResponse] = [] 
    class Config:
        from_attributes = True


class TripListResponse(BaseModel):
    id: int
    title: str
    destinations: List[str]
    start_date: datetime
    end_date: datetime
    status: str
    trip_type: str
    traveler_count: int
    created_at: datetime

    class Config:
        from_attributes = True
