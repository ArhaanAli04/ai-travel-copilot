"""
Pydantic schemas for disruption API
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.disruption import DisruptionType, DisruptionSeverity, OptionType
from app.models.draft_message import MessageRecipientType, MessageTone

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
    meta_data: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)


# ===== List Responses =====

class DisruptionCaseListResponse(BaseModel):
    """Schema for list of disruption cases"""
    total: int
    cases: List[DisruptionCaseResponse]

# ADD THESE NEW SCHEMAS:

class ExplainRightsRequest(BaseModel):
    """Request body for explain-rights endpoint"""
    airline_code: Optional[str] = Field(None, description="IATA airline code (e.g., AA, BA)")
    booking_class: Optional[str] = Field(None, description="Booking class (economy, business, first)")
    insurance_provider: Optional[str] = Field(None, description="Travel insurance provider name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "airline_code": "AA",
                "booking_class": "economy",
                "insurance_provider": "Allianz"
            }
        }


class SourceLink(BaseModel):
    """Source citation for policy information"""
    title: str
    url: str
    type: str  # airline, regional, hotel, insurance
    region: str


class ExplainRightsResponse(BaseModel):
    """Response from explain-rights endpoint"""
    summary: str = Field(..., description="Plain-language summary of passenger rights")
    rights_bullets: List[str] = Field(default=[], description="Actionable bullet points")
    compensation_amount: Optional[int] = Field(None, description="Compensation amount (if applicable)")
    compensation_currency: str = Field(default="USD", description="Currency code")
    next_steps: List[str] = Field(default=[], description="What the passenger should do next")
    source_links: List[SourceLink] = Field(default=[], description="Source citations")
    cached: bool = Field(..., description="Whether data was retrieved from cache")
    region: str = Field(..., description="Applicable region (EU, US, UK, etc.)")
    applicable_regulation: str = Field(default="", description="Name of regulation (e.g., EU261)")
    generated_at: str = Field(..., description="Timestamp of generation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "summary": "You are entitled to €600 compensation under EU Regulation 261/2004 because your flight was cancelled less than 14 days before departure and the airline did not provide an alternative flight.",
                "rights_bullets": [
                    "Claim €600 compensation for cancellation",
                    "Request full refund or alternative flight",
                    "Claim reimbursement for meals and accommodation if needed"
                ],
                "compensation_amount": 600,
                "compensation_currency": "EUR",
                "next_steps": [
                    "File a claim directly with the airline",
                    "Keep all receipts for expenses",
                    "Contact your credit card company if airline refuses"
                ],
                "source_links": [
                    {
                        "title": "EU Regulation 261/2004",
                        "url": "https://europa.eu/...",
                        "type": "regional",
                        "region": "EU"
                    }
                ],
                "cached": True,
                "region": "EU",
                "applicable_regulation": "EU Regulation 261/2004",
                "generated_at": "2026-01-16T20:00:00"
            }
        }

class SuggestOptionsResponse(BaseModel):
    """Response for suggest-options endpoint"""
    options: List["DisruptionOptionResponse"]
    total_options: int
    generated_at: datetime
    
    class Config:
        from_attributes = True


class GenerateMessageRequest(BaseModel):
    """Request for generate-message endpoint"""
    option_id: Optional[int] = None  # Optional: which option this message is for
    recipient_type: str
    tone: str= "formal"
    recipient_name: Optional[str] = None  # e.g., "British Airways"
    
    class Config:
        use_enum_values = True


class DraftMessageResponse(BaseModel):
    """Response containing generated draft message"""
    id: Optional[int] = None 
    disruption_case_id: int
    disruption_option_id: Optional[int]
    recipient_type: str
    recipient_name: Optional[str]
    recipient_email: Optional[str]
    subject: str
    body: str
    tone: str
    language: str
    attachments_needed: Optional[str]
    next_steps: Optional[List[str]] = None  # Actionable next steps
    created_at: datetime
    
    class Config:
        from_attributes = True


class AlternativeFlightDetail(BaseModel):
    """Detailed flight information for alternative option"""
    flight_number: str
    airline: str
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    stops: int
    price_amount: float
    price_currency: str
    price_difference: float  # Difference from original
    booking_url: Optional[str]
    
    class Config:
        from_attributes = True


class RefundDetail(BaseModel):
    """Refund calculation details"""
    ticket_refund: float
    eu261_compensation: Optional[float]
    additional_expenses: Optional[float]
    total: float
    currency: str
    
    class Config:
        from_attributes = True

# ===== CHAT SCHEMAS =====

class ChatMessage(BaseModel):
    """Single chat message"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    """Request to chat with AI assistant"""
    message: str
    history: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    """Response from AI assistant"""
    response: str
    case_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True
