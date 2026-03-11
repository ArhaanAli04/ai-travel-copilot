from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.postgres import get_db
from app.core.dependencies import get_current_user,require_trip_owner,require_trip_access,require_trip_editor
from app.models.user import User
from app.models.trip import Trip
from app.models.trip_day import TripDay
from app.models.activity import Activity
from app.schemas.trip import (
    TripCreate, TripUpdate, TripResponse, TripListResponse,
    ActivityReorderRequest, DayReplanRequest, ActivityDeleteResponse ,ActivityUpdate,
    ActivityPhotoResponse
)
import asyncio
from app.api.ws import manager as ws_manager
from app.models.collaborator import TripCollaborator, CollaboratorStatus
import logging
from app.ai.planner_agent import create_planner_agent
from datetime import time as time_type, datetime,timedelta
from app.services.email_service import EmailService
from app.services.photo_service import get_activity_photos
from pydantic import BaseModel, EmailStr
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trips", tags=["Planner"])

@router.post("/", response_model=TripResponse, status_code=201)
async def create_trip(
    trip: TripCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):
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
            include_hotels=trip.include_hotels,        # ADD
            hotel_preferences=trip.hotel_preferences,  # ADD
            notes=trip.notes,
            status="draft",
            user_id=current_user.id  # Will add auth later
        )
        
        db.add(db_trip)
        db.commit()
        db.refresh(db_trip)
        
        logger.info(f"✅ Created trip {db_trip.id}: {db_trip.title} for user {current_user.id}")
        return db_trip
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create trip: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create trip: {str(e)}")

@router.get("/favorites", response_model=List[TripListResponse])
async def get_favorite_trips(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all favorite trips
    
    **What it does:**
    1. Queries trips where is_favorite = true
    2. Returns list of favorite trips
    
    **Returns:**
    - List of favorite trips
    """
    try:
        trips = (
            db.query(Trip)
            .filter(Trip.user_id == current_user.id, Trip.is_favorite == True)
            .order_by(Trip.updated_at.desc())
            .offset(skip).limit(limit).all()
        )
        logger.info(f"⭐ Listed {len(trips)} favorites for user {current_user.id}")
        return trips
        
    except Exception as e:
        logger.error(f"❌ Failed to list favorite trips: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list favorite trips: {str(e)}")
    
@router.get("/", response_model=List[TripListResponse])
async def list_trips(
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all trips (with optional filtering)
    """
    try:
       # Get shared trip IDs as a plain list
        shared_trip_ids = [
            row.trip_id for row in db.query(TripCollaborator.trip_id).filter(
                TripCollaborator.clerk_user_id == current_user.clerk_id,
                TripCollaborator.status == CollaboratorStatus.ACCEPTED
            ).all()
        ]

        # Single query using OR — avoids UNION on JSON columns
        query = db.query(Trip).filter(
            (Trip.user_id == current_user.id) |
            (Trip.id.in_(shared_trip_ids))
        )

        if status:
            query = query.filter(Trip.status == status)
        trips = query.order_by(Trip.created_at.desc()).offset(skip).limit(limit).all()
        logger.info(f"📋 Listed {len(trips)} trips (owned + shared) for user {current_user.id}")
        result = []
        for trip in trips:
            trip_data = TripListResponse.model_validate(trip)
            trip_data.is_owner = (trip.user_id == current_user.id)
            result.append(trip_data)
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to list trips: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list trips: {str(e)}")

@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: int, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    """
    Get trip details with all days and activities
    """
    try:
        trip, role = require_trip_access(trip_id, current_user, db)
        trip.days = sorted(trip.days, key=lambda x: x.day_number)
        for day in trip.days:
            day.activities = sorted(day.activities, key=lambda x: x.order)
        trip_data = TripResponse.model_validate(trip)
        trip_data.is_owner = (trip.user_id == current_user.id)
        return trip_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get trip {trip_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trip: {str(e)}")


@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: int,
    trip_update: TripUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update trip metadata (dates, budget, preferences, etc.)
    """
    try:
        trip = require_trip_editor(trip_id, current_user, db)
        
        # Update only provided fields
        update_data = trip_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(trip, field, value)
        
        db.commit()
        db.refresh(trip)
        asyncio.create_task(ws_manager.broadcast(trip_id, {
            "type": "trip_updated",
            "payload": {"trip_id": trip_id, "updated_fields": list(update_data.keys())}
        }))
        
        logger.info(f"✏️ Updated trip {trip_id}")
        return trip
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to update trip {trip_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update trip: {str(e)}")

@router.post("/{trip_id}/favorite", response_model=dict)
async def toggle_favorite(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Toggle favorite status for a trip
    
    **What it does:**
    1. Finds the trip by ID
    2. Toggles the is_favorite field
    3. Returns updated favorite status
    
    **Returns:**
    - trip_id: ID of the trip
    - is_favorite: New favorite status (true/false)
    - message: Confirmation message
    """
    try:
        trip = require_trip_owner(trip_id, current_user, db)
        
        # Toggle favorite status
        trip.is_favorite = not trip.is_favorite
        
        db.commit()
        db.refresh(trip)
        
        status = "added to" if trip.is_favorite else "removed from"
        logger.info(f"⭐ Trip {trip_id} {status} favorites")
        
        return {
            "trip_id": trip.id,
            "is_favorite": trip.is_favorite,
            "message": f"Trip {status} favorites"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to toggle favorite for trip {trip_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to toggle favorite: {str(e)}"
        )


@router.delete("/{trip_id}", status_code=204)
async def delete_trip(trip_id: int, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    """
    Delete trip and all associated days/activities
    """
    try:
        trip = require_trip_owner(trip_id, current_user, db)
        
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
async def generate_itinerary(trip_id: int, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
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
        trip = require_trip_editor(trip_id, current_user, db)
        
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
        asyncio.create_task(ws_manager.broadcast(trip_id, {
            "type": "itinerary_generated",
            "payload": {"trip_id": trip_id}
        }))
        return updated_trip
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Itinerary generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate itinerary: {str(e)}"
        )

# Add this model at the top with other models
class EmailItineraryRequest(BaseModel):
    email: EmailStr
    include_pdf: bool = True

# Add this endpoint with your other trip endpoints
@router.post("/{trip_id}/email", response_model=dict)
def email_trip_itinerary(
    trip_id: int,
    request: EmailItineraryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send trip itinerary via email
    """
    # Get trip
    trip = require_trip_editor(trip_id, current_user, db)
    
    try:
        # Send email (without PDF for now - we'll add PDF generation later)
        result = EmailService.send_itinerary_email(
            trip=trip,
            recipient_email=request.email,
            pdf_bytes=None  # We'll add PDF generation in next step
        )
        
        return {
            "success": True,
            "message": f"Itinerary sent to {request.email}",
            "message_id": result.get("message_id")
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send email: {str(e)}"
        )

# ─────────────────────────────────────────────
# DAYS
# ─────────────────────────────────────────────

@router.post("/{trip_id}/days/{day_id}/reorder", response_model=dict)
async def reorder_activities(
    trip_id: int,
    day_id: int,
    reorder_request: ActivityReorderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reorder activities within a specific day
    
    **What it does:**
    1. Validates all activity IDs belong to the specified day
    2. Updates the order field for each activity
    3. Returns updated day with reordered activities
    
    **Request body:**
    - activity_ids: List of activity IDs in desired order
    
    **Returns:**
    - Success message
    - Updated activities in new order
    """
    try:
        # Verify trip exists
        trip = require_trip_editor(trip_id, current_user, db)
        
        # Verify day exists and belongs to trip
        day = db.query(TripDay).filter(
            TripDay.id == day_id,
            TripDay.trip_id == trip_id
        ).first()
        
        if not day:
            raise HTTPException(
                status_code=404,
                detail=f"Day {day_id} not found in trip {trip_id}"
            )
        
        # Get all activities for this day
        activities = db.query(Activity).filter(
            Activity.trip_day_id == day_id
        ).all()
        
        # Validate activity IDs
        activity_ids_in_day = {act.id for act in activities}
        requested_ids = set(reorder_request.activity_ids)
        
        if requested_ids != activity_ids_in_day:
            missing = activity_ids_in_day - requested_ids
            extra = requested_ids - activity_ids_in_day
            error_msg = []
            if missing:
                error_msg.append(f"Missing activity IDs: {missing}")
            if extra:
                error_msg.append(f"Invalid activity IDs (not in this day): {extra}")
            raise HTTPException(
                status_code=400,
                detail="; ".join(error_msg)
            )
        
        # Update order for each activity
        activity_map = {act.id: act for act in activities}
        
        for new_order, activity_id in enumerate(reorder_request.activity_ids, start=1):
            activity_map[activity_id].order = new_order
        
        db.commit()
        asyncio.create_task(ws_manager.broadcast(trip_id, {
            "type": "activities_reordered",
            "payload": {"trip_id": trip_id, "day_id": day_id}
        }))
        # Refresh activities to get updated order
        for act in activities:
            db.refresh(act)
        
        # Sort by new order
        sorted_activities = sorted(activities, key=lambda x: x.order)
        
        logger.info(f"🔄 Reordered {len(activities)} activities in day {day_id}")
        
        return {
            "message": "Activities reordered successfully",
            "day_id": day_id,
            "activities_count": len(activities),
            "new_order": [act.id for act in sorted_activities]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to reorder activities: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reorder activities: {str(e)}"
        )

@router.post("/{trip_id}/days/{day_id}/replan", response_model=TripResponse)
async def replan_day(
    trip_id: int,
    day_id: int,
    replan_request: DayReplanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Re-plan a specific day with new preferences
    
    **What it does:**
    1. Loads existing day and trip details
    2. Combines original preferences with new ones
    3. Deletes existing activities (unless keep_existing_activities=true)
    4. Generates new activities using AI with updated preferences
    5. Returns updated trip
    
    **Request body:**
    - additional_preferences: New constraints/preferences for this day
    - keep_existing_activities: If true, adds to existing; if false, replaces all
    
    **Returns:**
    - Complete updated trip with re-planned day
    """
    try:
        # Verify trip exists
        trip = require_trip_editor(trip_id, current_user, db)
        
        # Verify day exists and belongs to trip
        day = db.query(TripDay).filter(
            TripDay.id == day_id,
            TripDay.trip_id == trip_id
        ).first()
        
        if not day:
            raise HTTPException(
                status_code=404,
                detail=f"Day {day_id} not found in trip {trip_id}"
            )
        
        # Delete existing activities if not keeping them
        if not replan_request.keep_existing_activities:
            logger.info(f"🗑️ Deleting existing activities for day {day_id}")
            db.query(Activity).filter(Activity.trip_day_id == day_id).delete()
            db.commit()
        
        # Create planner agent
        planner = create_planner_agent(db)
        # Fetch weather for this specific day
        weather_forecast = await planner._fetch_weather(trip)
        weather_data = planner._get_day_weather(weather_forecast, day.date)
        # Calculate budget
        budget_per_day = planner._calculate_daily_budget(trip)
        # Merge preferences
        original_prefs = trip.preferences or {}
        merged_preferences = {
            **original_prefs,
            "day_specific": replan_request.additional_preferences
        }
        
        # Fetch guide context
        guide_context, guide_documents = await planner._fetch_guide_context(
            city=day.city,
            interests=trip.interests or []
        )
        
        # Create prompt with additional preferences
        from app.ai.prompts import create_day_planning_prompt
        
        user_prompt = create_day_planning_prompt(
            day_number=day.day_number,
            date_str=day.date.isoformat(),
            city=day.city,
            weather=weather_data,
            budget_per_day=budget_per_day,
            interests=trip.interests or [],
            preferences=merged_preferences,
            guide_context=guide_context,
            trip_type=trip.trip_type,
            traveler_count=trip.traveler_count
        )
        
        # Add additional preferences to prompt
        user_prompt += f"\n\n**IMPORTANT - Additional preferences for this day:**\n{replan_request.additional_preferences}"
        
        # Combine with system prompt
        from app.ai.prompts import ITINERARY_SYSTEM_PROMPT
        full_prompt = f"{ITINERARY_SYSTEM_PROMPT}\n\n{user_prompt}"
        
        # Call Gemini
        logger.info(f"🤖 Re-planning Day {day.day_number} with new preferences...")
        response = planner.client.models.generate_content(
            model=planner.model_name,
            contents=full_prompt,
            config=planner.config
        )
        
        # Parse response
        day_plan = planner._parse_gemini_response(response.text)
        
        if not day_plan:
            raise HTTPException(
                status_code=500,
                detail="Failed to parse AI response"
            )
        
        # Update day metadata
        day.theme = day_plan.get("day_theme", day.theme)
        day.description = day_plan.get("day_description", day.description)
        
        # Get starting order (if keeping existing activities)
        starting_order = 1
        if replan_request.keep_existing_activities:
            max_order = db.query(Activity).filter(
                Activity.trip_day_id == day_id
            ).count()
            starting_order = max_order + 1
        
        # Create new activities
        activities = day_plan.get("activities", [])
        for idx, activity_data in enumerate(activities, start=starting_order):
            activity = planner._create_activity(
                trip_day_id=day.id,
                order=idx,
                activity_data=activity_data,
                guide_documents=guide_documents
            )
            db.add(activity)
        
        db.commit()
        asyncio.create_task(ws_manager.broadcast(trip_id, {
            "type": "day_replanned",
            "payload": {"trip_id": trip_id, "day_id": day_id}
        }))
        
        logger.info(f"✅ Re-planned day {day_id} with {len(activities)} activities")
        
        # Refresh trip to load all relationships
        db.refresh(trip)
        return trip
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to re-plan day: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to re-plan day: {str(e)}"
        )

# ─────────────────────────────────────────────
# ACTIVITIES
# Note: /activities/{id} routes have no trip_id in path,
# so we verify ownership via the activity→day→trip chain
# ─────────────────────────────────────────────
def _get_activity_and_verify_owner(activity_id: int, user_id: int, db: Session) -> Activity:
    """
    Fetch activity and verify caller has at least viewer access via trip chain.
    For mutations (delete/update), caller should also call require_trip_editor separately.
    """
    from app.models.collaborator import TripCollaborator, CollaboratorStatus

    activity = (
        db.query(Activity)
        .join(TripDay, Activity.trip_day_id == TripDay.id)
        .join(Trip, TripDay.trip_id == Trip.id)
        .filter(Activity.id == activity_id)
        .filter(
            (Trip.user_id == user_id) |
            (
                db.query(TripCollaborator).filter(
                    TripCollaborator.trip_id == Trip.id,
                    TripCollaborator.clerk_user_id == db.query(User.clerk_id).filter(User.id == user_id).scalar_subquery(),
                    TripCollaborator.status == CollaboratorStatus.ACCEPTED,
                ).exists()
            )
        )
        .first()
    )
    if not activity:
        raise HTTPException(status_code=404, detail=f"Activity {activity_id} not found")
    return activity

@router.get("/activities/{activity_id}/explain")
async def explain_activity_choice(
    activity_id: int,
    force_refresh: bool = Query(False, description="Force regenerate explanation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Explain why an activity was recommended
    
    **Caching:**
    - Explanations are cached for 7 days
    - Use force_refresh=true to regenerate

    **What it does:**
    1. Checks for cached explanation
    2. If cache valid, returns immediately
    3. Otherwise generates new explanation via Gemini
    4. Caches result for future requests
    
    **Returns:**
    - explanation: 2-4 sentence explanation
    - sources: List of travel guide sources used
    - has_sources: Whether source references were available
    - cached: Whether this response came from cache
    - generated_at: Unix timestamp of generation
    """
    try:
        _get_activity_and_verify_owner(activity_id, current_user.id, db)  # OWNERSHIP CHECK
        from app.ai.explanations import explain_activity
        
        result = await explain_activity(activity_id, db,force_refresh)
        
        if result.get("cached"):
            logger.info(f"⚡ Returned cached explanation for activity {activity_id}")
        else:
            logger.info(f"✅ Generated new explanation for activity {activity_id}")
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Explanation generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate explanation: {str(e)}"
        )

@router.get("/activities/{activity_id}/photos", response_model=ActivityPhotoResponse)
async def get_activity_photos_endpoint(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch photos for a specific activity using Google Images (SerpAPI).
    
    **Priority chain:**
    1. In-memory cache (7-day TTL) → instant response
    2. SerpAPI Google Images → real tourist attraction photos
    3. Wikimedia Commons fallback
    4. Unsplash generic fallback
    5. Placeholder if all fail

    **Returns:**
    - photos: List of photo objects with url, thumbnail_url, attribution
    - source: Which provider returned the photos
    - cached: Whether response came from cache
    """
    try:
        activity = _get_activity_and_verify_owner(activity_id, current_user.id, db)  # OWNERSHIP CHECK
        if not activity:
            raise HTTPException(status_code=404, detail=f"Activity {activity_id} not found")

        # Build location string: prefer specific location field, fall back to address
        location = activity.location or activity.address or ""

        result = await get_activity_photos(activity.title, location)

        logger.info(
            f"📸 Photos for activity '{activity.title}': "
            f"{len(result['photos'])} photos from {result['source']} "
            f"(cached: {result['cached']})"
        )

        return ActivityPhotoResponse(
            activity_id=activity_id,
            activity_title=activity.title,
            photos=result["photos"],
            source=result["source"],
            cached=result["cached"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch photos for activity {activity_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch activity photos: {str(e)}"
        )

@router.delete("/activities/{activity_id}", response_model=ActivityDeleteResponse)
async def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a specific activity from a day
    
    **What it does:**
    1. Finds the activity by ID
    2. Deletes it from database
    3. Re-orders remaining activities in the day
    
    **Returns:**
    - Confirmation message
    - Deleted activity ID
    - Count of remaining activities in that day
    """
    try:
        # Get activity
        activity = _get_activity_and_verify_owner(activity_id, current_user.id, db)  # OWNERSHIP CHECK
        if not activity:
            raise HTTPException(status_code=404, detail=f"Activity {activity_id} not found")
        trip_day = db.query(TripDay).filter(TripDay.id == activity.trip_day_id).first()
        require_trip_editor(trip_day.trip_id, current_user, db)
        trip_day_id = activity.trip_day_id
        deleted_order = activity.order
        
        # Delete activity
        db.delete(activity)
        db.flush()
        
        # Re-order remaining activities in the day
        remaining_activities = db.query(Activity).filter(
            Activity.trip_day_id == trip_day_id,
            Activity.order > deleted_order
        ).all()
        
        for act in remaining_activities:
            act.order -= 1
        
        db.commit()
        # Get trip_id from trip_day before we lost the reference
        asyncio.create_task(ws_manager.broadcast(trip_day.trip_id, {
            "type": "activity_deleted",
            "payload": {"trip_id": trip_day.trip_id, "activity_id": activity_id, "day_id": trip_day_id}
        }))
        # Count remaining activities
        remaining_count = db.query(Activity).filter(
            Activity.trip_day_id == trip_day_id
        ).count()
        
        logger.info(f"🗑️ Deleted activity {activity_id}, {remaining_count} activities remaining")
        
        return {
            "message": "Activity deleted successfully",
            "deleted_activity_id": activity_id,
            "remaining_activities_count": remaining_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to delete activity {activity_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete activity: {str(e)}"
        )

@router.patch("/activities/{activity_id}", response_model=dict)
async def update_activity(
    activity_id: int,
    update_data: ActivityUpdate,
    auto_adjust_subsequent: bool = Query(True, description="Auto-adjust subsequent activity times"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update activity details (title, times)
    
    **What it does:**
    1. Updates activity title and/or times
    2. Recalculates duration if both start and end times provided
    3. Optionally adjusts subsequent activities' times
    4. Validates time conflicts
    
    **Request body:**
    - title: New activity title
    - start_time: New start time (HH:MM format)
    - end_time: New end time (HH:MM format)
    - duration_minutes: New duration (will be recalculated if times provided)
    
    **Query params:**
    - auto_adjust_subsequent: If true, shifts subsequent activities by the time difference
    
    **Returns:**
    - Updated activity
    - List of other activities that were adjusted
    """
    try:
        # Get activity
        activity = _get_activity_and_verify_owner(activity_id, current_user.id, db)  # OWNERSHIP CHECK
        
        if not activity:
            raise HTTPException(status_code=404, detail=f"Activity {activity_id} not found")
        trip_day = db.query(TripDay).filter(TripDay.id == activity.trip_day_id).first()
        require_trip_editor(trip_day.trip_id, current_user, db)
        # Store original times for adjustment calculation
        original_start = activity.start_time
        original_end = activity.end_time
        original_duration = activity.duration_minutes

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            if field in ['start_time', 'end_time'] and value:
                # Convert string to time object
                time_obj = datetime.strptime(value, '%H:%M').time()
                setattr(activity, field, time_obj)
            elif field == 'title':
                setattr(activity, field, value)
        
        # Recalculate duration if both times provided
        if activity.start_time and activity.end_time:
            start_dt = datetime.combine(datetime.today(), activity.start_time)
            end_dt = datetime.combine(datetime.today(), activity.end_time)
            
            # Handle crossing midnight
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
            
            duration = (end_dt - start_dt).total_seconds() / 60
            activity.duration_minutes = int(duration)
            
            # Validate: end time must be after start time
            if duration <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="End time must be after start time"
                )
        
        db.flush()
        
        # Auto-adjust subsequent activities if requested
        adjusted_activities = []
        time_shift = 0

        if auto_adjust_subsequent:
            # Calculate shift based on what changed
            if original_end and activity.end_time and original_end != activity.end_time:
                # End time changed - shift subsequent activities by the difference
                orig_end_dt = datetime.combine(datetime.today(), original_end)
                new_end_dt = datetime.combine(datetime.today(), activity.end_time)
                time_shift = (new_end_dt - orig_end_dt).total_seconds() / 60  # minutes
                
                logger.info(f"📊 End time changed from {original_end} to {activity.end_time}, shift: {time_shift} min")
                
            elif original_start and activity.start_time and original_start != activity.start_time:
                # Start time changed - shift subsequent activities by the difference
                orig_start_dt = datetime.combine(datetime.today(), original_start)
                new_start_dt = datetime.combine(datetime.today(), activity.start_time)
                time_shift = (new_start_dt - orig_start_dt).total_seconds() / 60  # minutes
                
                logger.info(f"📊 Start time changed from {original_start} to {activity.start_time}, shift: {time_shift} min")
            
            # Apply shift to subsequent activities if there's a change
            if time_shift != 0:
                # Get subsequent activities in the same day
                subsequent_activities = db.query(Activity).filter(
                    Activity.trip_day_id == activity.trip_day_id,
                    Activity.order > activity.order
                ).order_by(Activity.order).all()
                
                logger.info(f"🔄 Adjusting {len(subsequent_activities)} subsequent activities by {time_shift} minutes")
                
                # Shift each subsequent activity
                for act in subsequent_activities:
                    if act.start_time:
                        old_start = datetime.combine(datetime.today(), act.start_time)
                        new_start = old_start + timedelta(minutes=time_shift)
                        act.start_time = new_start.time()
                        
                    if act.end_time:
                        old_end = datetime.combine(datetime.today(), act.end_time)
                        new_end = old_end + timedelta(minutes=time_shift)
                        act.end_time = new_end.time()
                    
                    adjusted_activities.append({
                        "id": act.id,
                        "title": act.title,
                        "new_start_time": act.start_time.strftime('%H:%M') if act.start_time else None,
                        "new_end_time": act.end_time.strftime('%H:%M') if act.end_time else None
                    })
        
        db.commit()
        db.refresh(activity)
        asyncio.create_task(ws_manager.broadcast(trip_day.trip_id, {
            "type": "activity_updated",
            "payload": {"trip_id": trip_day.trip_id, "activity_id": activity_id}
        }))
        
        logger.info(f"✏️ Updated activity {activity_id}, adjusted {len(adjusted_activities)} subsequent activities")
        
        return {
            "message": "Activity updated successfully",
            "activity": {
                "id": activity.id,
                "title": activity.title,
                "start_time": activity.start_time.strftime('%H:%M') if activity.start_time else None,
                "end_time": activity.end_time.strftime('%H:%M') if activity.end_time else None,
                "duration_minutes": activity.duration_minutes
            },
            "adjusted_activities": adjusted_activities,
            "time_shift_minutes": time_shift 
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to update activity {activity_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update activity: {str(e)}"
        )
    
