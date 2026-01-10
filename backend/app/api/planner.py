from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.postgres import get_db
from app.models.trip import Trip
from app.models.trip_day import TripDay
from app.models.activity import Activity
from app.schemas.trip import (
    TripCreate, TripUpdate, TripResponse, TripListResponse
)
import logging
from app.ai.planner_agent import create_planner_agent
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trips", tags=["Planner"])


@router.post("/", response_model=TripResponse, status_code=201)
async def create_trip(trip: TripCreate, db: Session = Depends(get_db)):
    """
    Create a new trip shell (without itinerary)
    """
    try:
        # Create trip
        db_trip = Trip(
            title=trip.title,
            origin=trip.origin,
            destinations=trip.destinations,
            start_date=trip.start_date,
            end_date=trip.end_date,
            budget=trip.budget,
            budget_currency=trip.budget_currency,
            interests=trip.interests,
            preferences=trip.preferences,
            trip_type=trip.trip_type,
            traveler_count=trip.traveler_count,
            traveler_ages=trip.traveler_ages,
            include_flights=trip.include_flights,
            flight_preferences=trip.flight_preferences,
            notes=trip.notes,
            status="draft",
            user_id=None  # Will add auth later
        )
        
        db.add(db_trip)
        db.commit()
        db.refresh(db_trip)
        
        logger.info(f"✅ Created trip {db_trip.id}: {db_trip.title}")
        return db_trip
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create trip: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create trip: {str(e)}")


@router.get("/", response_model=List[TripListResponse])
async def list_trips(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all trips (with optional filtering)
    """
    try:
        query = db.query(Trip)
        
        # Apply filters
        if user_id is not None:
            query = query.filter(Trip.user_id == user_id)
        if status:
            query = query.filter(Trip.status == status)
        
        # Order by created_at descending
        query = query.order_by(Trip.created_at.desc())
        
        # Pagination
        trips = query.offset(skip).limit(limit).all()
        
        logger.info(f"📋 Listed {len(trips)} trips")
        return trips
        
    except Exception as e:
        logger.error(f"❌ Failed to list trips: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list trips: {str(e)}")


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: int, db: Session = Depends(get_db)):
    """
    Get trip details with all days and activities
    """
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")
        
        logger.info(f"📖 Retrieved trip {trip_id}")
        return trip
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get trip {trip_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trip: {str(e)}")


@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: int,
    trip_update: TripUpdate,
    db: Session = Depends(get_db)
):
    """
    Update trip metadata (dates, budget, preferences, etc.)
    """
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")
        
        # Update only provided fields
        update_data = trip_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(trip, field, value)
        
        db.commit()
        db.refresh(trip)
        
        logger.info(f"✏️ Updated trip {trip_id}")
        return trip
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to update trip {trip_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update trip: {str(e)}")


@router.delete("/{trip_id}", status_code=204)
async def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    """
    Delete trip and all associated days/activities
    """
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")
        
        db.delete(trip)
        db.commit()
        
        logger.info(f"🗑️ Deleted trip {trip_id}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to delete trip {trip_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete trip: {str(e)}")

@router.post("/{trip_id}/plan", response_model=TripResponse)
async def generate_itinerary(trip_id: int, db: Session = Depends(get_db)):
    """
    Generate AI-powered itinerary for a trip
    
    **What it does:**
    1. Fetches weather forecast for trip dates
    2. Uses TravelGuideRetriever to get local recommendations
    3. Calls Gemini to generate day-by-day plans
    4. Saves TripDay and Activity records to database
    
    **Requirements:**
    - Trip must exist
    - Trip must have start_date, end_date, and destinations
    
    **Returns:**
    - Complete trip with days and activities
    """
    try:
        # Check if trip exists
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")
        
        # Validate trip has required fields
        if not trip.destinations:
            raise HTTPException(
                status_code=400,
                detail="Trip must have at least one destination"
            )
        
        if not trip.start_date or not trip.end_date:
            raise HTTPException(
                status_code=400,
                detail="Trip must have start_date and end_date"
            )
        
        # Create planner agent
        planner = create_planner_agent(db)
        
        # Generate itinerary
        logger.info(f"🎯 Starting itinerary generation for trip {trip_id}")
        updated_trip = await planner.generate_itinerary(trip_id)
        
        logger.info(f"✅ Itinerary generated for trip {trip_id}")
        return updated_trip
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Itinerary generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate itinerary: {str(e)}"
        )