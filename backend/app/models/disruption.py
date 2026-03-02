"""
Disruption models for travel disruption management
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.postgres import Base


class DisruptionType(str, enum.Enum):
    """Types of travel disruptions"""
    DELAY = "delay"
    CANCELLATION = "cancellation"
    WEATHER = "weather"
    STRIKE = "strike"
    OTHER = "other"


class DisruptionSeverity(str, enum.Enum):
    """Severity levels for disruptions"""
    LOW = "low"          # Minor delay (<2 hours)
    MEDIUM = "medium"    # Significant delay (2-4 hours)
    HIGH = "high"        # Major disruption (4-8 hours)
    CRITICAL = "critical"  # Cancellation or >8 hours


class OptionType(str, enum.Enum):
    """Types of disruption resolution options"""
    ALTERNATIVE_FLIGHT = "alternative_flight"
    REFUND = "refund"
    HOTEL_VOUCHER = "hotel_voucher"
    COMPENSATION = "compensation"
    MEAL_VOUCHER = "meal_voucher"
    REBOOKING = "rebooking"


class DisruptionCase(Base):
    """
    Represents a travel disruption case
    
    Stores flight disruption information and real-time status
    """
    __tablename__ = "disruption_cases"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # User reference - Foreign key to users table
    # Will be enforced when authentication is implemented
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True) 
    
    # Flight information
    flight_number = Column(String(20), nullable=False, index=True)
    airline = Column(String(100), nullable=False)
    origin = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    
    # Disruption details
    disruption_date = Column(DateTime, nullable=False, index=True)
    disruption_type = Column(Enum(DisruptionType), nullable=False)
    current_status = Column(String(200), nullable=True)  # e.g., "Delayed by 3 hours"
    severity = Column(Enum(DisruptionSeverity), default=DisruptionSeverity.LOW)
    
    # Booking information
    pnr = Column(String(50), nullable=True)  # Passenger Name Record
    booking_reference = Column(String(50), nullable=True)
    
    # Additional context
    notes = Column(Text, nullable=True)  # User's free-text notes
    
    # Metadata (JSON field for flexible storage)
    # Stores: flight status API response, weather data, strike info
    meta_data = Column(JSON, nullable=True)
    
    # Soft delete
    is_deleted = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    options = relationship("DisruptionOption", back_populates="case", cascade="all, delete-orphan")
    user = relationship("User", backref="disruption_cases")  #  ADDED relationship to User
    
    def __repr__(self):
        return f"<DisruptionCase {self.flight_number} - {self.disruption_type.value}>"


class DisruptionOption(Base):
    """
    Represents a resolution option for a disruption case
    
    AI-generated alternatives and recommendations
    """
    __tablename__ = "disruption_options"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to disruption case
    disruption_case_id = Column(Integer, ForeignKey("disruption_cases.id", ondelete="CASCADE"), nullable=False)
    
    # Option details
    option_type = Column(Enum(OptionType), nullable=False)
    title = Column(String(200), nullable=False)  # e.g., "Alternative Flight UA456"
    description = Column(Text, nullable=True)  # Detailed explanation
    
    # Cost information
    estimated_cost = Column(Float, nullable=True)  # Additional cost (can be negative for refunds)
    
    # Action details
    action_required = Column(Text, nullable=True)  # What user needs to do
    booking_url = Column(String(500), nullable=True)  # Direct booking link
    contact_info = Column(String(200), nullable=True)  # Phone/email for this option
    
    # AI metadata
    priority_rank = Column(Integer, default=0)  # Higher = more recommended
    ai_reasoning = Column(Text, nullable=True)  # Why AI suggested this option
    
    # Flexible JSON storage (flight details, pros/cons, etc.)
    meta_data = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    case = relationship("DisruptionCase", back_populates="options")
    
    def __repr__(self):
        return f"<DisruptionOption {self.option_type.value} for Case {self.disruption_case_id}>"
