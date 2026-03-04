from pydantic import BaseModel, Field
from typing import Optional, List


class HotelBase(BaseModel):
    name: str
    property_type: Optional[str] = None
    city: str
    address: Optional[str] = None
    coordinates: Optional[dict] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    rating_breakdown: Optional[dict] = None
    price_per_night: float
    price_currency: str = "USD"
    total_price: Optional[float] = None
    check_in_date: Optional[str] = None
    check_out_date: Optional[str] = None
    nights: Optional[int] = None
    thumbnail: Optional[str] = None
    images: Optional[List[str]] = None
    amenities: Optional[List[str]] = None
    highlights: Optional[List[str]] = None
    booking_url: Optional[str] = None
    source: str = "serpapi"
    serpapi_property_id: Optional[str] = None

    class Config:
        from_attributes = True


class HotelSearchResponse(HotelBase):
    """Response for hotel search results (not yet saved to DB)"""
    pass


class HotelSelect(BaseModel):
    """Request to select and save a hotel"""
    hotel_data: HotelBase
    notes: Optional[str] = None


class HotelResponse(HotelBase):
    """Response for saved hotel (includes DB fields)"""
    id: int
    trip_id: int
    is_selected: bool = True

    class Config:
        from_attributes = True


class HotelSearchRequest(BaseModel):
    """Request to search for hotels"""
    city: str = Field(..., description="City name to search hotels in (e.g., Paris)")
    check_in_date: str = Field(..., description="Check-in date YYYY-MM-DD")
    check_out_date: str = Field(..., description="Check-out date YYYY-MM-DD")
    adults: int = Field(2, ge=1, le=10, description="Number of adults")
    sort_by: Optional[str] = Field(
        "relevance",
        description="Sort order: relevance, lowest_price, highest_rating, most_reviewed"
    )
    max_price: Optional[float] = Field(None, description="Maximum price per night filter")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum rating filter")

    class Config:
        json_schema_extra = {
            "example": {
                "city": "Paris",
                "check_in_date": "2026-03-23",
                "check_out_date": "2026-03-28",
                "adults": 2,
                "sort_by": "highest_rating"
            }
        }
