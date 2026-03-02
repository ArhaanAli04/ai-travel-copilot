from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.core.postgres import Base

class Airline(Base):
    __tablename__ = "airlines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    iata_code = Column(String(10), nullable=True, index=True)
    website = Column(String(500), nullable=True)
    customer_service_url = Column(String(500), nullable=True)
    phone = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
