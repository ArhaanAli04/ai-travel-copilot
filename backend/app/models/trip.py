from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.postgres import Base


class Trip(Base):
    """
    Trip model - Main travel itinerary
    """
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    
    # User relationship (will add foreign key when auth is implemented)
    user_id = Column(Integer, nullable=True)  # Placeholder for now
    
    # Basic trip info
    title = Column(String, nullable=False)
    origin = Column(String, nullable=False)  # Starting city/airport
    destinations = Column(JSON, nullable=False)  # ["Paris", "Rome", "Barcelona"]
    
    # Dates
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Budget and preferences
    budget = Column(Float, nullable=True)  # Total budget in USD (or currency)
    budget_currency = Column(String, default="USD")
    interests = Column(JSON, nullable=True)  # ["culture", "food", "adventure"]
    preferences = Column(JSON, nullable=True)  # Any additional preferences
    
    # Trip type and travelers
    trip_type = Column(String, nullable=False, default="solo")  # solo, couple, family, group
    traveler_count = Column(Integer, default=1)
    traveler_ages = Column(JSON, nullable=True)  # [28, 32, 5, 7] for family with kids
    
    # Flight preferences
    include_flights = Column(Boolean, default=False)
    flight_preferences = Column(JSON, nullable=True)  # {class: "economy", max_stops: 1}
    
    # Status
    status = Column(String, default="draft")  # draft, planning, planned, completed
    
    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    days = relationship("TripDay", back_populates="trip", cascade="all, delete-orphan")
    flights = relationship("Flight", back_populates="trip", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Trip(id={self.id}, title='{self.title}', destinations={self.destinations})>"
