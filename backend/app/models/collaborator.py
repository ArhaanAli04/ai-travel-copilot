"""
TripCollaborator model — shared access to trips
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.postgres import Base
import enum


class CollaboratorRole(str, enum.Enum):
    VIEWER = "viewer"
    EDITOR = "editor"


class CollaboratorStatus(str, enum.Enum):
    PENDING  = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class TripCollaborator(Base):
    __tablename__ = "trip_collaborators"

    id                = Column(Integer, primary_key=True, index=True)
    trip_id           = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    invited_by_user_id= Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    email             = Column(String(255), nullable=False, index=True)
    clerk_user_id     = Column(String(255), nullable=True, index=True)  # null until accepted
    role              = Column(Enum(CollaboratorRole), nullable=False, default=CollaboratorRole.VIEWER)
    status            = Column(Enum(CollaboratorStatus), nullable=False, default=CollaboratorStatus.PENDING)
    invite_token      = Column(String(36), unique=True, nullable=False, index=True)  # UUID
    invited_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    accepted_at       = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    trip          = relationship("Trip", back_populates="collaborators")
    invited_by    = relationship("User", foreign_keys=[invited_by_user_id])
