from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from app.core.postgres import Base


class Flight(Base):
    """
    Flight model - Flight options and bookings for trips
    """
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    trip_day_id = Column(Integer, ForeignKey("trip_days.id", ondelete="SET NULL"), nullable=True)
    
    # Flight identification
    flight_number = Column(String, nullable=True)
    airline = Column(String, nullable=False)
    airline_code = Column(String, nullable=True)  # e.g., "AI" for Air India
    
    # Route
    departure_airport = Column(String, nullable=False)  # IATA code (e.g., "BOM")
    arrival_airport = Column(String, nullable=False)    # IATA code (e.g., "CDG")
    departure_city = Column(String, nullable=True)
    arrival_city = Column(String, nullable=True)
    
    # Timing
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    
    # Flight details
    stops = Column(Integer, default=0)  # 0 = nonstop, 1 = 1 stop, etc.
    layover_airports = Column(JSON, nullable=True)  # ["DXB", "DOH"] if multi-stop
    cabin_class = Column(String, nullable=False)  # economy, premium_economy, business, first
    
    # Pricing
    price_amount = Column(Float, nullable=False)
    price_currency = Column(String, default="USD")
    
    # Booking
    is_selected = Column(Boolean, default=False)  # User selected this flight
    booking_url = Column(String, nullable=True)  # Deep link to airline/OTA
    booking_reference = Column(String, nullable=True)  # If booked
    
    # Additional data
    aircraft_type = Column(String, nullable=True)
    baggage_allowance = Column(JSON, nullable=True)  # {checked: "2x23kg", carry_on: "7kg"}
    amenities = Column(JSON, nullable=True)  # ["wifi", "meals", "entertainment"]
    
    # Metadata
    source = Column(String, nullable=True)  # "mock", "amadeus", "skyscanner"
    raw_data = Column(JSON, nullable=True)  # Original API response
    
    # Relationships
    trip = relationship("Trip", back_populates="flights")

    def __repr__(self):
        return f"<Flight(id={self.id}, {self.departure_airport}→{self.arrival_airport}, {self.airline})>"
