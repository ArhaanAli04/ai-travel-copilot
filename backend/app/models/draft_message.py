"""
Draft Message Model - AI-generated email templates for disruption resolution
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum


from app.core.postgres import Base


class MessageRecipientType(str, enum.Enum):
    """Types of message recipients"""
    AIRLINE = "airline"
    HOTEL = "hotel"
    INSURANCE = "insurance"
    OTHER = "other"


class MessageTone(str, enum.Enum):
    """Message tone options"""
    FORMAL = "formal"        # Professional, neutral
    FIRM = "firm"           # Assertive, demanding rights
    FRIENDLY = "friendly"    # Polite, cooperative


class DraftMessage(Base):
    """
    AI-generated draft messages for disruption resolution
    
    Stores professionally formatted emails/letters for:
    - Airline refund requests
    - Hotel cancellation requests
    - Insurance claim submissions
    """
    __tablename__ = "draft_messages"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    disruption_case_id = Column(
        Integer,
        ForeignKey("disruption_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    disruption_option_id = Column(
        Integer,
        ForeignKey("disruption_options.id", ondelete="SET NULL"),
        nullable=True  # Optional: can generate message without specific option
    )
    
    # Message details
    recipient_type = Column(Enum(MessageRecipientType), nullable=False)
    recipient_name = Column(String(200), nullable=True)  # e.g., "British Airways"
    recipient_email = Column(String(200), nullable=True)  # e.g., "customer.service@ba.com"
    
    # Email content
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    
    # Message metadata
    tone = Column(Enum(MessageTone), default=MessageTone.FORMAL)
    language = Column(String(10), default="en")  # ISO language code
    
    # Generation info
    generated_by = Column(String(50), default="ai")  # "ai" or "user_edited"
    ai_model = Column(String(50), nullable=True)  # e.g., "gemini-2.5-flash"
    
    # Attachments guidance
    attachments_needed = Column(Text, nullable=True)  # JSON array of required documents
    
    # Status
    sent_at = Column(DateTime, nullable=True)  # When user marked as sent
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    case = relationship("DisruptionCase", backref="draft_messages")
    option = relationship("DisruptionOption", backref="draft_messages")
    
    def __repr__(self):
        return f"<DraftMessage {self.id} - {self.recipient_type.value} for Case {self.disruption_case_id}>"
