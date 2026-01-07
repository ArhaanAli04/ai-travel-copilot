from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


# Activity Schemas
class ActivityBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    start_time: Optional[str] = None  # "09:00"
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    address: Optional[str] = None
    estimated_cost: Optional[float] = None
    order: int


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
