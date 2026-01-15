"""
Pydantic schemas for disruption API
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.disruption import DisruptionType, DisruptionSeverity, OptionType


# ===== DisruptionCase Schemas =====

class DisruptionCaseCreate(BaseModel):
    """Schema for creating a disruption case"""
    flight_number: str = Field(..., min_length=2, max_length=20, description="Flight number (e.g., AA123)")
    airline: str = Field(..., min_length=2, max_length=100, description="Airline name")
    origin: str = Field(..., min_length=3, max_length=100, description="Origin airport/city")
    destination: str = Field(..., min_length=3, max_length=100, description="Destination airport/city")
    disruption_date: datetime = Field(..., description="Date of disruption")
    pnr: Optional[str] = Field(None, max_length=50, description="Passenger Name Record")
    notes: Optional[str] = Field(None, description="Additional notes about the disruption")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "flight_number": "AA123",
            "airline": "American Airlines",
            "origin": "New York (JFK)",
            "destination": "London (LHR)",
            "disruption_date": "2026-01-20T10:30:00",
            "pnr": "ABC123",
            "notes": "Flight cancelled due to weather"
        }
    })


class DisruptionCaseUpdate(BaseModel):
    """Schema for updating a disruption case"""
    current_status: Optional[str] = None
    severity: Optional[DisruptionSeverity] = None
    notes: Optional[str] = None
    meta_data: Optional[dict] = None


class DisruptionCaseResponse(BaseModel):
    """Schema for disruption case response"""
    id: int
    user_id: Optional[int]
    flight_number: str
    airline: str
    origin: str
    destination: str
    disruption_date: datetime
    disruption_type: DisruptionType
    current_status: Optional[str]
    severity: DisruptionSeverity
    pnr: Optional[str]
    booking_reference: Optional[str]
    notes: Optional[str]
    meta_data: Optional[dict]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DisruptionCaseWithOptions(DisruptionCaseResponse):
    """Schema for disruption case with options"""
    options: List["DisruptionOptionResponse"] = []
    
    model_config = ConfigDict(from_attributes=True)


# ===== DisruptionOption Schemas =====

class DisruptionOptionCreate(BaseModel):
    """Schema for creating a disruption option"""
    disruption_case_id: int
    option_type: OptionType
    title: str = Field(..., min_length=5, max_length=200)
    description: Optional[str] = None
    estimated_cost: Optional[float] = None
    action_required: Optional[str] = None
    booking_url: Optional[str] = None
    contact_info: Optional[str] = None
    priority_rank: int = Field(default=0, ge=0, le=10)
    ai_reasoning: Optional[str] = None


class DisruptionOptionResponse(BaseModel):
    """Schema for disruption option response"""
    id: int
    disruption_case_id: int
    option_type: OptionType
    title: str
    description: Optional[str]
    estimated_cost: Optional[float]
    action_required: Optional[str]
    booking_url: Optional[str]
    contact_info: Optional[str]
    priority_rank: int
    ai_reasoning: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ===== List Responses =====

class DisruptionCaseListResponse(BaseModel):
    """Schema for list of disruption cases"""
    total: int
    cases: List[DisruptionCaseResponse]
