"""
MongoDB Pydantic models for Disruption Knowledge Base

Collections:
- passenger_rights: Pre-ingested rights by region + disruption_type
- draft_message_templates: Pre-ingested email templates by recipient + message_type + tone
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone


class CompensationTier(BaseModel):
    """
    Compensation tier for distance-based regulations (e.g., EU261)
    Each tier defines the compensation for flights up to a given distance
    """
    max_distance_km: int = Field(..., description="Max flight distance in km for this tier (use 999999 for unlimited)")
    amount: int = Field(..., description="Compensation amount in local currency")
    currency: str = Field(..., description="Currency code (EUR, USD, GBP, etc.)")
    condition: Optional[str] = Field(None, description="Additional condition (e.g., 'delay > 3 hours')")


class RightsSourceLink(BaseModel):
    """Source citation for a rights document"""
    title: str
    url: str
    type: str = Field(..., description="Source type: regulation, airline, authority")
    region: str


class PassengerRightsDocument(BaseModel):
    """
    MongoDB document for pre-ingested passenger rights knowledge

    Stored in: travel_copilot.passenger_rights
    Lookup key: region + disruption_type
    """
    region: str = Field(..., description="Region code: EU, US, UK, IN, CA, AU, AE, GENERAL")
    disruption_type: str = Field(..., description="Disruption type: delay, cancellation, overbooking, etc.")
    regulation_name: str = Field(..., description="Full regulation name e.g. EU Regulation 261/2004")
    applicable_regulation: str = Field(..., description="Short display name e.g. EU261")
    enforcement_body: str = Field(..., description="Regulatory body passengers can escalate to")
    summary: str = Field(..., description="Plain-language 2-3 sentence summary of passenger rights")
    rights_bullets: List[str] = Field(default=[], description="Actionable bullet points of entitlements")
    compensation_tiers: List[CompensationTier] = Field(
        default=[],
        description="Distance/delay-based compensation tiers (primarily used for EU/UK/CA)"
    )
    default_compensation_amount: Optional[int] = Field(
        None,
        description="Flat compensation if no tiers apply (e.g., US overbooking: 1550 USD)"
    )
    default_compensation_currency: str = Field(default="USD", description="Currency for flat compensation")
    next_steps: List[str] = Field(default=[], description="What the passenger should do next")
    source_links: List[RightsSourceLink] = Field(default=[], description="Official source citations")
    version: int = Field(default=1, description="Document version for future updates")
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this document was last updated"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "region": "EU",
                "disruption_type": "cancellation",
                "regulation_name": "EU Regulation 261/2004",
                "applicable_regulation": "EU261",
                "enforcement_body": "National Enforcement Body (e.g., CAA in UK, Luftfahrt-Bundesamt in DE)",
                "summary": "Under EU261, if your flight is cancelled with less than 14 days notice, you are entitled to compensation of €250–€600 depending on flight distance, plus a full refund or alternative flight.",
                "rights_bullets": [
                    "Compensation of €250–€600 depending on flight distance",
                    "Full refund of ticket price or re-routing to destination",
                    "Right to care: meals, refreshments, hotel if overnight stay needed"
                ],
                "compensation_tiers": [
                    {"max_distance_km": 1500, "amount": 250, "currency": "EUR", "condition": "All cancellations < 14 days notice"},
                    {"max_distance_km": 3500, "amount": 400, "currency": "EUR", "condition": "Internal EU flights > 1500km"},
                    {"max_distance_km": 999999, "amount": 600, "currency": "EUR", "condition": "All flights > 3500km"}
                ],
                "next_steps": [
                    "File a claim directly with the airline in writing",
                    "Keep all receipts for meals, accommodation, transport",
                    "Escalate to national enforcement body if airline refuses within 8 weeks"
                ]
            }
        }


class DraftMessageTemplateDocument(BaseModel):
    """
    MongoDB document for pre-ingested email draft templates

    Stored in: travel_copilot.draft_message_templates
    Lookup key: recipient_type + message_type + tone
    """
    recipient_type: str = Field(..., description="airline, hotel, insurance")
    message_type: str = Field(..., description="refund, rebooking, cancellation, claim, alternative_flight")
    tone: str = Field(..., description="formal, firm, friendly")
    disruption_types: List[str] = Field(
        default=[],
        description="Which disruption types this template is relevant for"
    )
    subject_template: str = Field(..., description="Email subject with {variable} placeholders")
    body_template: str = Field(..., description="Full email body with {variable} placeholders")
    required_variables: List[str] = Field(
        default=[],
        description="List of variable names that MUST be filled in the template"
    )
    optional_variables: List[str] = Field(
        default=[],
        description="List of variable names that are optional in the template"
    )
    attachments_needed: List[str] = Field(
        default=[],
        description="Documents the passenger needs to attach"
    )
    next_steps: List[str] = Field(
        default=[],
        description="Actionable steps after sending this message"
    )
    version: int = Field(default=1, description="Template version")
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Config:
        json_schema_extra = {
            "example": {
                "recipient_type": "airline",
                "message_type": "refund",
                "tone": "formal",
                "disruption_types": ["cancellation", "delay"],
                "subject_template": "Refund Request - Flight {flight_number} Cancellation",
                "body_template": "Dear {airline_name} Customer Service,\n\nI am writing to request...",
                "required_variables": ["airline_name", "flight_number", "origin", "destination", "departure_date", "pnr"],
                "optional_variables": ["compensation_amount", "compensation_currency", "regulation"],
                "attachments_needed": ["Booking confirmation", "Flight cancellation notice"],
                "next_steps": ["Send email to airline customer service", "Follow up in 48-72 hours"]
            }
        }


class RightsLookupResult(BaseModel):
    """
    Standardized result returned to disruption_agent.py from MongoDB lookup.
    Matches the exact shape of ExplainRightsResponse so it can be returned directly.
    """
    summary: str
    rights_bullets: List[str] = []
    compensation_amount: Optional[int] = None
    compensation_currency: str = "USD"
    next_steps: List[str] = []
    source_links: List[Dict[str, Any]] = []
    cached: bool = True
    region: str = ""
    applicable_regulation: str = ""
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
