from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.postgres import Base
from sqlalchemy.orm import relationship 

class User(Base):
    """
    User model for authentication and profile
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    clerk_id = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)  # Optional for OAuth users
    provider = Column(String, default="email")  # email, google, etc.
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ✅ ADD THESE RELATIONSHIPS (optional but recommended)
    # trips = relationship("Trip", backref="user", cascade="all, delete-orphan")
    # disruption_cases = relationship("DisruptionCase", backref="user", cascade="all, delete-orphan")
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"
