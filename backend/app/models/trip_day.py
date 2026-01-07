from sqlalchemy import Column, Integer, String, Date, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.core.postgres import Base


class TripDay(Base):
    """
    TripDay model - Single day in a trip
    """
    __tablename__ = "trip_days"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    
    # Day info
    day_number = Column(Integer, nullable=False)  # 1, 2, 3...
    date = Column(Date, nullable=False)
    city = Column(String, nullable=False)  # Which city/destination for this day
    
    # Day theme/focus
    theme = Column(String, nullable=True)  # "cultural exploration", "beach day", etc.
    description = Column(Text, nullable=True)  # AI-generated day summary
    
    # Metadata
    preferences = Column(JSON, nullable=True)  # Day-specific preferences
    
    # Relationships
    trip = relationship("Trip", back_populates="days")
    activities = relationship("Activity", back_populates="day", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TripDay(id={self.id}, trip_id={self.trip_id}, day={self.day_number}, city='{self.city}')>"
