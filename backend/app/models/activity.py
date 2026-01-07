from sqlalchemy import Column, Integer, String, Time, ForeignKey, Float, JSON, Text, Boolean
from sqlalchemy.orm import relationship
from app.core.postgres import Base


class Activity(Base):
    """
    Activity model - Individual activity within a day
    """
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    trip_day_id = Column(Integer, ForeignKey("trip_days.id", ondelete="CASCADE"), nullable=False)
    
    # Activity details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)  # "sightseeing", "dining", "entertainment"
    
    # Timing
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    order = Column(Integer, nullable=False)  # Order within the day (1, 2, 3...)
    
    # Location
    location = Column(String, nullable=True)
    address = Column(String, nullable=True)
    coordinates = Column(JSON, nullable=True)  # {"lat": 48.8584, "lng": 2.2945}
    
    # Cost
    estimated_cost = Column(Float, nullable=True)
    cost_currency = Column(String, default="USD")
    
    # AI context
    source_refs = Column(JSON, nullable=True)  # References to guide chunks used
    ai_reasoning = Column(Text, nullable=True)  # Why this was recommended
    
    # Status
    is_booked = Column(Boolean, default=False)
    booking_url = Column(String, nullable=True)
    
    # Relationships
    day = relationship("TripDay", back_populates="activities")

    def __repr__(self):
        return f"<Activity(id={self.id}, title='{self.title}', order={self.order})>"
