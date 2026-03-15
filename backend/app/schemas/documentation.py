"""
Pydantic schemas for Trip Documentation
Covers: document checklist, entry requirements, legal advisories, emergency contacts
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Section 1: Document Checklist ──────────────────────────────────

class ChecklistItem(BaseModel):
    """Individual document checklist item"""
    item: str                          # e.g. "Passport"
    required: bool                     # True = mandatory, False = recommended
    notes: Optional[str] = None        # e.g. "Must be valid 6 months beyond travel date"

    class Config:
        from_attributes = True


class VisaRequirement(BaseModel):
    """
    Visa and document requirements per destination.
    One entry per destination in the trip.
    """
    destination: str                              # e.g. "Paris, France"
    visa_type: str                                # e.g. "Schengen Visa", "Visa on Arrival", "Visa Free"
    visa_cost: Optional[str] = None              # e.g. "$80 USD" or "Free"
    processing_days: Optional[str] = None        # e.g. "15-20 business days"
    apply_url: Optional[str] = None              # Official visa application URL
    procedure: Optional[str] = None             # Step-by-step visa procedure as text
    checklist_items: List[ChecklistItem] = []    # All documents needed for this destination

    class Config:
        from_attributes = True


# ── Section 2: Entry Requirements ──────────────────────────────────

class EntryRequirementItem(BaseModel):
    """Single entry requirement for a destination"""
    category: str          # e.g. "Health", "Customs", "Restricted Items", "Minor Travel"
    description: str       # Short title e.g. "Currency Limit"
    details: str           # Full explanation e.g. "Max $10,000 USD cash allowed"

    class Config:
        from_attributes = True


class EntryRequirements(BaseModel):
    """
    Entry requirements per destination.
    Covers health, customs, restrictions, minors.
    """
    destination: str
    items: List[EntryRequirementItem] = []

    class Config:
        from_attributes = True


# ── Section 3: Legal Advisories ────────────────────────────────────

class LegalAdvisory(BaseModel):
    """
    A single legal advisory for a destination.
    severity drives UI color coding:
      - critical → red  (illegal, criminal offense)
      - warning  → amber (restricted, fines)
      - info     → blue  (cultural norms, dress codes)
    """
    severity: str      # "critical" | "warning" | "info"
    category: str      # e.g. "Drug Laws", "LGBTQ+ Rights", "Drone Regulations"
    description: str   # Full advisory text

    class Config:
        from_attributes = True


class LegalAdvisories(BaseModel):
    """Legal advisories per destination"""
    destination: str
    advisories: List[LegalAdvisory] = []

    class Config:
        from_attributes = True


# ── Section 4: Emergency Contacts ──────────────────────────────────

class HospitalRecommendation(BaseModel):
    """Recommended hospital in a destination"""
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None       # e.g. "Best English-speaking hospital"

    class Config:
        from_attributes = True


class EmergencyContacts(BaseModel):
    """
    Emergency contacts per destination.
    Includes embassy, local emergency services, hospitals.
    """
    destination: str
    police: Optional[str] = None                              # Local police number e.g. "17"
    ambulance: Optional[str] = None                          # Ambulance number e.g. "15"
    fire: Optional[str] = None                               # Fire brigade
    general_emergency: Optional[str] = None                  # e.g. "112" EU unified
    embassy_phone: Optional[str] = None                      # Your country's embassy phone
    embassy_address: Optional[str] = None                    # Embassy address
    embassy_website: Optional[str] = None                    # Embassy website URL
    hospital_recommendations: List[HospitalRecommendation] = []
    travel_advisory_level: Optional[str] = None              # e.g. "Level 1 - Exercise Normal Precautions"
    travel_advisory_source: Optional[str] = None             # e.g. "US State Department"

    class Config:
        from_attributes = True


# ── Top-level Response Schemas ──────────────────────────────────────

class DocumentationResponse(BaseModel):
    """
    Full documentation response for a trip.
    Returned by GET /trips/{id}/documentation
    and POST /trips/{id}/documentation/generate
    """
    id: int
    trip_id: int
    origin_country: Optional[str] = None

    # 4 core sections — one entry per destination
    document_checklist: List[VisaRequirement] = []
    entry_requirements: List[EntryRequirements] = []
    legal_advisories: List[LegalAdvisories] = []
    emergency_contacts: List[EmergencyContacts] = []

    # Metadata
    generated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentationGenerateResponse(BaseModel):
    """
    Lightweight response for trigger endpoints.
    Returned immediately when background generation is triggered.
    """
    success: bool
    message: str
    trip_id: int
    status: str     # "generating" | "completed" | "failed"

    class Config:
        from_attributes = True


class DocumentationStatusResponse(BaseModel):
    """
    Check if documentation exists for a trip.
    Used by frontend to decide whether to show generate button or fetch existing.
    """
    trip_id: int
    exists: bool
    generated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
