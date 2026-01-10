from sqlalchemy import Column, Integer, String, Date, ForeignKey, JSON, Text,Float
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

    # ✨ NEW: Weather fields
    weather_temp_high = Column(Float, nullable=True)  # Max temp in Celsius
    weather_temp_low = Column(Float, nullable=True)   # Min temp in Celsius
    weather_condition = Column(String, nullable=True)  # "Partly cloudy", "Rain", etc.
    weather_icon = Column(String, nullable=True)       # "⛅", "🌧️", etc.
    weather_precipitation_prob = Column(Float, nullable=True)  # 0-100%

    # Metadata
    preferences = Column(JSON, nullable=True)  # Day-specific preferences
    
    # Relationships
    trip = relationship("Trip", back_populates="days")
    activities = relationship("Activity", back_populates="day", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TripDay(id={self.id}, trip_id={self.trip_id}, day={self.day_number}, city='{self.city}')>"
    
    @property
    def weather_summary(self) -> str:
        """Get formatted weather summary"""
        if not self.weather_condition:
            return "Weather data unavailable"
        
        temp_f_high = (self.weather_temp_high * 9/5) + 32 if self.weather_temp_high else 0
        temp_f_low = (self.weather_temp_low * 9/5) + 32 if self.weather_temp_low else 0
        
        return f"{self.weather_icon} {self.weather_condition} • {self.weather_temp_low:.0f}-{self.weather_temp_high:.0f}°C ({temp_f_low:.0f}-{temp_f_high:.0f}°F)"
