from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.postgres import Base


class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)

    # Identity
    name = Column(String, nullable=False)
    property_type = Column(String, nullable=True)  # hotel, resort, hostel, etc.

    # Location
    city = Column(String, nullable=False)
    address = Column(String, nullable=True)
    coordinates = Column(JSON, nullable=True)  # {"lat": 48.8566, "lng": 2.3522}

    # Rating
    rating = Column(Float, nullable=True)       # e.g. 4.5
    reviews_count = Column(Integer, nullable=True)
    rating_breakdown = Column(JSON, nullable=True)  # {"cleanliness": 4.8, "location": 4.9}

    # Pricing
    price_per_night = Column(Float, nullable=False)
    price_currency = Column(String, default="USD")
    total_price = Column(Float, nullable=True)   # price_per_night * nights

    # Stay details
    check_in_date = Column(String, nullable=True)   # stored as YYYY-MM-DD string
    check_out_date = Column(String, nullable=True)
    nights = Column(Integer, nullable=True)

    # Media
    thumbnail = Column(String, nullable=True)    # main image URL
    images = Column(JSON, nullable=True)         # list of image URLs

    # Amenities & highlights
    amenities = Column(JSON, nullable=True)      # ["wifi", "pool", "breakfast"]
    highlights = Column(JSON, nullable=True)     # ["Great location", "Free cancellation"]

    # Booking
    is_selected = Column(Boolean, default=False)
    booking_url = Column(String, nullable=True)

    # Source
    source = Column(String, default="serpapi")
    serpapi_property_id = Column(String, nullable=True)  # for deduplication
    raw_data = Column(JSON, nullable=True)

    # Relationship
    trip = relationship("Trip", back_populates="hotels")

    def __repr__(self):
        return f"<Hotel(id={self.id}, name='{self.name}', city='{self.city}')>"
