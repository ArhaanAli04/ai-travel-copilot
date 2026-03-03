"""
API endpoints for travel disruption management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime,timezone,timedelta
import logging
from app.api.flights import get_airport_code
import re
from app.core.postgres import get_db
from app.models.disruption import DisruptionCase, DisruptionOption, DisruptionType, DisruptionSeverity, OptionType, DisruptionChatMessage
from app.schemas.disruption import (
    DisruptionCaseCreate,
    DisruptionCaseUpdate,
    DisruptionCaseResponse,
    DisruptionCaseWithOptions,
    DisruptionCaseListResponse,
    DisruptionOptionCreate,
    DisruptionOptionResponse,
    ExplainRightsRequest,
    ExplainRightsResponse,
    SuggestOptionsResponse,
    DraftMessageResponse,
    GenerateMessageRequest
)
from app.services.disruption_service import disruption_service  # ✅ ADD THIS IMPORT
from app.ai.disruption_agent import disruption_agent
from app.services.weather_service import weather_service
router = APIRouter(prefix="/disruptions", tags=["disruptions"])
logger = logging.getLogger(__name__)


# ===== Helper Functions =====
def _resolve_airport_codes(origin: str, destination: str) -> tuple[str, str]:
    """
    Convert city names or mixed formats to IATA codes
    
    Examples:
    - "New York" → "JFK"
    - "Miami, US (MIA)" → "MIA"
    - "JFK" → "JFK" (already IATA)
    """
    try:
        # Extract IATA if already in format "City (CODE)" or "City, Country (CODE)"
        origin_match = re.search(r'\(([A-Z]{3})\)', origin)
        if origin_match:
            origin_iata = origin_match.group(1)
        else:
            # Check if already 3-letter IATA code
            if len(origin.strip()) == 3 and origin.strip().isupper():
                origin_iata = origin.strip()
            else:
                origin_iata = get_airport_code(origin)
        
        # Same for destination
        dest_match = re.search(r'\(([A-Z]{3})\)', destination)
        if dest_match:
            dest_iata = dest_match.group(1)
        else:
            if len(destination.strip()) == 3 and destination.strip().isupper():
                dest_iata = destination.strip()
            else:
                dest_iata = get_airport_code(destination)
        
        logger.info(f"✅ Resolved airports: '{origin}' → {origin_iata}, '{destination}' → {dest_iata}")
        return origin_iata, dest_iata
        
    except Exception as e:
        logger.warning(f"⚠️ Could not resolve airport codes: {e}")
        # Fallback to original values
        return origin, destination

def _detect_disruption_type(notes: str) -> DisruptionType:
    """
    Auto-detect disruption type from notes using simple keyword matching
    """
    notes_lower = notes.lower()
    
    if any(word in notes_lower for word in ["cancel", "cancelled"]):
        return DisruptionType.CANCELLATION
    elif any(word in notes_lower for word in ["delay", "delayed", "late"]):
        return DisruptionType.DELAY
    elif any(word in notes_lower for word in ["miss", "missed", "connecting"]):
        return DisruptionType.MISSED_CONNECTION
    elif any(word in notes_lower for word in ["overbook", "bump", "denied boarding"]):
        return DisruptionType.OVERBOOKING
    elif any(word in notes_lower for word in ["baggage", "luggage", "bag", "lost"]):
        return DisruptionType.BAGGAGE_ISSUE
    else:
        return DisruptionType.OTHER

def _weather_severity(code: int, precip: float) -> str:
    """Determine severity from WMO code"""
    if code in [65, 75, 82, 86, 95, 96, 99]:  # heavy rain/snow/thunderstorm
        return "high"
    if code in [63, 73, 81, 85] or precip > 70:  # moderate conditions
        return "medium"
    return "low"

@router.get("/api-usage")  # ✅ This will be: /api/disruptions/api-usage
def get_api_usage():
    """
    Get API usage statistics for disruption service
    
    Returns:
    - AviationStack: calls made, monthly limit, remaining
    - Tomorrow.io: calls made, daily limit, remaining
    """
    return {
        "aviationstack": {
            "calls_made": disruption_service.api_calls.get("aviationstack", 0),
            "monthly_limit": 100,
            "remaining": 100 - disruption_service.api_calls.get("aviationstack", 0)
        },
        "tomorrow_io": {
            "calls_made": disruption_service.api_calls.get("tomorrow_io", 0),
            "daily_limit": 500,
            "hourly_limit": 25,
            "remaining_daily": 500 - disruption_service.api_calls.get("tomorrow_io", 0)
        },
        "note": "Counter resets when server restarts"
    }
# ===== CRUD Operations =====

@router.post("/", response_model=DisruptionCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_disruption_case(
    case_data: DisruptionCaseCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new disruption case
    
    - Accepts flight details and disruption information
    - Auto-detects disruption type based on notes/status
    - Returns created case with initial status
    """
    try:
        logger.info(f"📥 Received disruption case request: {case_data.flight_number}")
        logger.info(f"   Origin: {case_data.origin}")
        logger.info(f"   Destination: {case_data.destination}")

        # ✅ NEW: Resolve airport codes
        logger.info("🔍 Resolving airport codes...")
        origin_iata, dest_iata = _resolve_airport_codes(
            case_data.origin, 
            case_data.destination
        )
        logger.info(f"✅ Resolved: {origin_iata} → {dest_iata}")

        # Auto-detect disruption type from notes (simple heuristic for now)
        disruption_type = _detect_disruption_type(case_data.notes or "")
        logger.info(f"🔍 Detected disruption type: {disruption_type}")

        # Create case
        db_case = DisruptionCase(
            flight_number=case_data.flight_number.upper(),
            airline=case_data.airline,
            origin=origin_iata,
            destination=dest_iata,
            disruption_date=case_data.disruption_date,
            disruption_type=disruption_type,
            pnr=case_data.pnr,
            notes=case_data.notes,
            current_status="Checking flight status",
            severity=DisruptionSeverity.LOW,
            meta_data={
                "original_origin": case_data.origin,      # ✅ Keep original for display
                "original_destination": case_data.destination
            }
        )
        
        db.add(db_case)
        db.commit()
        db.refresh(db_case)
        
        logger.info(f"✅ Created disruption case {db_case.id} for flight {db_case.flight_number}")
        logger.info(f"   Route: {origin_iata} → {dest_iata}")
        # ✅ Auto-enrich with timeout protection
        logger.info(f"🔄 Starting enrichment for case {db_case.id}...")

        try:
            import asyncio
            db_case = await asyncio.wait_for(
                disruption_service.enrich_disruption_case(db_case, db),
                timeout=30.0
            )
            logger.info(f"✅ Case {db_case.id} auto-enriched successfully")
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Enrichment timeout for case {db_case.id} (took >30s)")
            db_case.current_status = "Enrichment in progress (taking longer than expected)"
            db.commit()

        except Exception as e:
            logger.warning(f"⚠️ Auto-enrichment failed for case {db_case.id}: {e}")
            db_case.current_status = "Created (enrichment failed)"
            db.commit()
        logger.info(f"📤 Returning case {db_case.id} to frontend")
        return db_case
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error creating disruption case: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create disruption case: {str(e)}"
        )


@router.get("/{case_id}", response_model=DisruptionCaseWithOptions)
def get_disruption_case(
    case_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific disruption case with options
    
    - Returns case details
    - Includes all suggested options
    - Includes rights summary (to be added)
    """
    case = db.query(DisruptionCase).filter(
        DisruptionCase.id == case_id,
        DisruptionCase.is_deleted == 0
    ).first()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disruption case {case_id} not found"
        )
    
    return case


@router.get("/", response_model=DisruptionCaseListResponse)
def list_disruption_cases(
    skip: int = 0,
    limit: int = 10,
    user_id: int = None,
    db: Session = Depends(get_db)
):
    """
    List disruption cases
    
    - Returns paginated list of cases
    - Optionally filter by user_id
    - Ordered by created_at descending (newest first)
    """
    query = db.query(DisruptionCase).filter(DisruptionCase.is_deleted == 0)
    
    if user_id:
        query = query.filter(DisruptionCase.user_id == user_id)
    
    total = query.count()
    cases = query.order_by(DisruptionCase.created_at.desc()).offset(skip).limit(limit).all()
    
    return DisruptionCaseListResponse(total=total, cases=cases)


@router.put("/{case_id}", response_model=DisruptionCaseResponse)
def update_disruption_case(
    case_id: int,
    case_update: DisruptionCaseUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a disruption case
    
    - Updates current_status, severity, notes, metadata
    - Used for enriching case with flight/weather data
    """
    case = db.query(DisruptionCase).filter(
        DisruptionCase.id == case_id,
        DisruptionCase.is_deleted == 0
    ).first()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disruption case {case_id} not found"
        )
    
    # Update fields
    update_data = case_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)
    
    case.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(case)
    
    logger.info(f"✅ Updated disruption case {case_id}")
    
    return case


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_disruption_case(
    case_id: int,
    db: Session = Depends(get_db)
):
    """
    Soft delete a disruption case
    
    - Marks case as deleted (is_deleted = 1)
    - Does not actually remove from database
    """
    case = db.query(DisruptionCase).filter(
        DisruptionCase.id == case_id,
        DisruptionCase.is_deleted == 0
    ).first()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disruption case {case_id} not found"
        )
    
    case.is_deleted = 1
    db.commit()
    
    logger.info(f"🗑️ Soft deleted disruption case {case_id}")
    
    return None

@router.get("/{case_id}/weather")
async def get_disruption_weather(
    case_id: int,
    db: Session = Depends(get_db)
):
    """Fetch weather for disruption case origin using Open-Meteo (free)"""
    case = db.query(DisruptionCase).filter(
        DisruptionCase.id == case_id,
        DisruptionCase.is_deleted == 0
    ).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        disruption_date = case.disruption_date.date() if isinstance(case.disruption_date, datetime) else case.disruption_date

        # Use original city name for geocoding if available, else IATA code
        city = (case.meta_data or {}).get("original_origin") or case.origin

        logger.info(f"🌦️ Fetching weather for {city} on {disruption_date}")

        forecast = await weather_service.get_forecast(
            city=city,
            start_date=disruption_date,
            end_date=disruption_date
        )

        if not forecast or not forecast.daily_forecasts:
            return {"weather": None, "error": "No weather data available"}

        day = forecast.daily_forecasts[0]

        return {
            "weather": {
                "condition": day.condition,
                "icon": day.icon,
                "temp_max": day.temp_max,
                "temp_min": day.temp_min,
                "precipitation_probability": day.precipitation_probability,
                "wind_speed_max": day.wind_speed_max,
                "visibility_mean": day.visibility_mean,
                "uv_index_max": day.uv_index_max,
                "sunrise": day.sunrise,
                "sunset": day.sunset,
                "severity": _weather_severity(day.condition_code, day.precipitation_probability),
                "airport_code": case.origin,
                "city": city,
                "fetched_at": forecast.cached_at.isoformat()
            }
        }

    except Exception as e:
        logger.error(f"❌ Weather fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# ===== Option Management =====

@router.post("/{case_id}/options", response_model=DisruptionOptionResponse, status_code=status.HTTP_201_CREATED)
def create_disruption_option(
    case_id: int,
    option_data: DisruptionOptionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new option for a disruption case
    
    - Used by AI agent to add suggested alternatives
    """
    # Verify case exists
    case = db.query(DisruptionCase).filter(
        DisruptionCase.id == case_id,
        DisruptionCase.is_deleted == 0
    ).first()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disruption case {case_id} not found"
        )
    
    # Create option
    db_option = DisruptionOption(**option_data.model_dump())
    db.add(db_option)
    db.commit()
    db.refresh(db_option)
    
    logger.info(f"✅ Created option {db_option.id} for case {case_id}")
    
    return db_option

@router.get("/{case_id}/options", response_model=List[DisruptionOptionResponse])
def list_disruption_options(
    case_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all options for a disruption case
    
    - Returns options ordered by priority_rank descending
    """
    # Verify case exists
    case = db.query(DisruptionCase).filter(
        DisruptionCase.id == case_id,
        DisruptionCase.is_deleted == 0
    ).first()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disruption case {case_id} not found"
        )
    
    options = db.query(DisruptionOption).filter(
        DisruptionOption.disruption_case_id == case_id
    ).order_by(DisruptionOption.priority_rank.desc()).all()
    
    return options

@router.post("/{case_id}/refresh", response_model=DisruptionCaseResponse)
async def refresh_disruption_case(
    case_id: int,
    db: Session = Depends(get_db)
):
    """
    Refresh disruption case with latest flight/weather data
    
    - Re-checks flight status
    - Re-checks weather alerts
    - Updates case metadata and status
    """
    case = db.query(DisruptionCase).filter(
        DisruptionCase.id == case_id,
        DisruptionCase.is_deleted == 0
    ).first()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disruption case {case_id} not found"
        )
    
    try:
        # Enrich with latest data
        case = await disruption_service.enrich_disruption_case(case, db)
        
        logger.info(f"✅ Case {case_id} refreshed successfully")
        return case
        
    except Exception as e:
        logger.error(f"❌ Case refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh case: {str(e)}"
        )

@router.post("/{case_id}/explain-rights", response_model=ExplainRightsResponse)
async def explain_passenger_rights(
    case_id: int,
    request: ExplainRightsRequest = None,
    db: Session = Depends(get_db)
):
    """
    Explain passenger rights for a disruption case
    
    Uses:
    - AI-powered analysis of airline policies
    - Regional regulations (EU261, DOT, etc.)
    - Cached policy documents (90-day TTL)
    
    Returns:
    - Plain-language rights explanation
    - Compensation amounts
    - Actionable next steps
    - Source citations
    """
    # Get disruption case
    case = db.query(DisruptionCase).filter(
        DisruptionCase.id == case_id,
        DisruptionCase.is_deleted == 0
    ).first()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disruption case {case_id} not found"
        )
    
    try:
        # Use disruption agent to explain rights
        if request:
            explanation = await disruption_agent.explain_rights(
                disruption_case=case,
                airline_code=request.airline_code,
                booking_class=request.booking_class,
                insurance_provider=request.insurance_provider
            )
        else:
            explanation = await disruption_agent.explain_rights(
                disruption_case=case
            )
        
        logger.info(f"✅ Explained rights for case {case_id}")
        
        return explanation
        
    except Exception as e:
        logger.error(f"❌ Failed to explain rights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to explain rights: {str(e)}"
        )
    

@router.post("/{case_id}/suggest-options", response_model=SuggestOptionsResponse)
async def suggest_disruption_options(
    case_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered alternative options for a disruption case
    
    Uses:
    - Real flight search via SerpAPI
    - Passenger rights calculation (Day 13)
    - AI ranking with Gemini
    
    Returns:
    - 3-5 ranked options (alternative flights, refunds, hotel, insurance)
    - Each with pros/cons, costs, and action steps
    """
    # Get disruption case
    case = db.query(DisruptionCase).filter(
        DisruptionCase.id == case_id,
        DisruptionCase.is_deleted == 0
    ).first()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disruption case {case_id} not found"
        )
    
    try:
        # ✅ Check DB cache first — avoid Gemini call if options already exist
        existing = db.query(DisruptionOption).filter(
            DisruptionOption.disruption_case_id == case_id,
            DisruptionOption.option_type != OptionType.ALTERNATIVE_FLIGHT
        ).all()

        if existing:
            logger.info(f"⚡ DB CACHE HIT — returning {len(existing)} saved options for case {case_id}, no Gemini call")
            from app.schemas.disruption import DisruptionOptionResponse
            option_responses = [DisruptionOptionResponse.model_validate(opt) for opt in existing]
            return SuggestOptionsResponse(
                options=option_responses,
                total_options=len(option_responses),
                generated_at=datetime.now(timezone.utc)
            )

        # No cached options — generate with Gemini
        logger.info(f"🤖 GEMINI CALL — generating options for case {case_id}...")
        options = await disruption_agent.suggest_options(
            disruption_case=case,
            db=db,
            max_options=5
        )
        
        if not options:
            logger.warning(f"⚠️ No options generated for case {case_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate options. Please try again."
            )
        
        # Convert to response format
        from app.schemas.disruption import DisruptionOptionResponse
        
        option_responses = [
            DisruptionOptionResponse.model_validate(opt) for opt in options
        ]
        
        response = SuggestOptionsResponse(
            options=option_responses,
            total_options=len(option_responses),
            generated_at=datetime.now(timezone.utc)
        )
        
        logger.info(f"✅ Generated {len(options)} options for case {case_id}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Failed to suggest options: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate options: {str(e)}"
        )

@router.post("/{case_id}/generate-message", response_model=DraftMessageResponse)
async def generate_disruption_message(
    case_id: int,
    request: GenerateMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Generate professional email/message for disruption resolution
    
    Supports:
    - Airline refund/rebooking requests
    - Hotel cancellation requests
    - Insurance claim submissions
    
    Tone options:
    - formal: Professional, neutral
    - firm: Assertive, demanding rights
    - friendly: Polite, cooperative
    
    Returns:
    - Email subject and body
    - Recipient contact info
    - Required attachments
    - Next steps
    """
    # Get disruption case
    case = db.query(DisruptionCase).filter(
        DisruptionCase.id == case_id,
        DisruptionCase.is_deleted == 0
    ).first()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disruption case {case_id} not found"
        )
    
    # Get option if specified
    disruption_option = None
    if request.option_id:
        disruption_option = db.query(DisruptionOption).filter(
            DisruptionOption.id == request.option_id,
            DisruptionOption.disruption_case_id == case_id
        ).first()
        
        if not disruption_option:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Option {request.option_id} not found for case {case_id}"
            )
        # ✅ FIX: Refresh to ensure meta_data is loaded
        db.refresh(disruption_option)
    try:
        # Generate message using AI agent
        message_data = await disruption_agent.generate_message(
            disruption_case=case,
            disruption_option=disruption_option,
            recipient_type=request.recipient_type,
            tone=request.tone,
            recipient_name=request.recipient_name,
            db=db
        )
        
        # ✅ FIX: Handle case where generation failed
        if not message_data or "error" in message_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message_data.get("error", "Failed to generate message")
            )
        
        # Convert to response format
        response = DraftMessageResponse(
            id=message_data.get("id"),
            disruption_case_id=case_id,
            disruption_option_id=request.option_id,
            recipient_type=message_data.get("recipient_type") or request.recipient_type,  # ✅ Fallback
            recipient_name=message_data.get("recipient_name"),
            recipient_email=message_data.get("recipient_email"),
            subject=message_data.get("subject") or "Flight Disruption",  # ✅ Fallback
            body=message_data.get("body") or "Message generation failed",  # ✅ Fallback
            tone=message_data.get("tone") or request.tone,  # ✅ Fallback
            language="en",
            attachments_needed=str(message_data.get("attachments_needed", [])),
            next_steps=message_data.get("next_steps", []),
            created_at=datetime.now(timezone.utc)
        )
        
        logger.info(f"✅ Generated {request.tone} message to {request.recipient_type} for case {case_id}")
        
        return response
    except HTTPException:
        raise     
    except Exception as e:
        logger.error(f"❌ Failed to generate message: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate message: {str(e)}"
        )

@router.post("/{case_id}/search-flights", response_model=SuggestOptionsResponse)
async def search_alternative_flights(
    case_id: int,
    search_date: Optional[str] = None,  # YYYY-MM-DD, defaults to disruption_date
    force: bool = False,
    db: Session = Depends(get_db)
):
    """
    Search alternative flights for a specific date.
    Used by frontend date tab switcher (today / tomorrow).
    Does NOT regenerate refund/hotel/insurance options.
    Only generates alternative_flight options for the given date.
    """
    case = db.query(DisruptionCase).filter(
        DisruptionCase.id == case_id,
        DisruptionCase.is_deleted == 0
    ).first()

    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    try:
        from app.services.disruption_service import disruption_service
        from app.models.disruption import DisruptionOption, OptionType

        # Use provided date or fall back to disruption date
        if search_date:
            departure_date = search_date
        else:
            departure_date = case.disruption_date.strftime("%Y-%m-%d")

        origin_iata = case.origin.strip().upper()
        destination_iata = case.destination.strip().upper()

        # Force refresh — delete existing DB rows for this date
        if force:
            existing_for_date = db.query(DisruptionOption).filter(
                DisruptionOption.disruption_case_id == case_id,
                DisruptionOption.option_type == OptionType.ALTERNATIVE_FLIGHT,
            ).all()
            to_delete = [
                opt for opt in existing_for_date
                if (opt.meta_data or {}).get("search_date") == departure_date
            ]
            for opt in to_delete:
                db.delete(opt)
            db.commit()
            logger.info(f"🗑️ Deleted {len(to_delete)} cached flights for {departure_date} (forced refresh)")

        logger.info(f"🔍 Flight request: {origin_iata}→{destination_iata} on {departure_date} for case {case_id}")

        # Check DB cache first — skip SerpAPI if already saved for this date
        existing = db.query(DisruptionOption).filter(
            DisruptionOption.disruption_case_id == case_id,
            DisruptionOption.option_type == OptionType.ALTERNATIVE_FLIGHT,
        ).all()

        existing_dates = {
            (opt.meta_data or {}).get("search_date") for opt in existing
        }

        if departure_date in existing_dates:
            logger.info(f"⚡ DB CACHE HIT — returning saved flights for {departure_date}, no SerpAPI call")
            cached = [opt for opt in existing if (opt.meta_data or {}).get("search_date") == departure_date]
            from app.schemas.disruption import DisruptionOptionResponse
            option_responses = [DisruptionOptionResponse.model_validate(opt) for opt in cached]
            return SuggestOptionsResponse(
                options=option_responses,
                total_options=len(option_responses),
                generated_at=datetime.now(timezone.utc)
            )

        # No cache — call SerpAPI
        logger.info(f"🌐 SERPAPI CALL — searching flights: {origin_iata}→{destination_iata} on {departure_date}")
        alternative_flights = await disruption_service.search_alternative_flights(
            origin_iata=origin_iata,
            destination_iata=destination_iata,
            departure_date=departure_date,
            cabin_class="economy",
            max_results=3
        )

        if not alternative_flights:
            return SuggestOptionsResponse(
                options=[],
                total_options=0,
                generated_at=datetime.now(timezone.utc)
            )

        # Build and SAVE to DB
        flight_options = []
        for i, flight in enumerate(alternative_flights):
            original_time = case.disruption_date
            new_departure = datetime.fromisoformat(flight["departure_time"])
            time_diff_hours = (new_departure - original_time).total_seconds() / 3600

            pros, cons = [], []
            if flight["stops"] == 0:
                pros.append("Direct flight")
            else:
                cons.append(f"{flight['stops']} stop(s)")
            if flight["airline"] == case.airline:
                pros.append("Same airline — easier rebooking")
            else:
                cons.append("Different airline — may require new booking")
            if abs(time_diff_hours) < 2:
                pros.append("Similar departure time")
            elif time_diff_hours > 0:
                cons.append(f"Departs {int(time_diff_hours)}h later")
            if flight["duration_minutes"] < 300:
                pros.append("Short flight time")

            airline_info = await disruption_service.get_airline_info(flight["airline"], db)

            db_option = DisruptionOption(
                disruption_case_id=case_id,
                option_type=OptionType.ALTERNATIVE_FLIGHT,
                title=f"Rebook on {flight['flight_number']} ({flight['airline']})",
                description=f"Alternative flight on {departure_date}",
                estimated_cost=flight["price_amount"],
                action_required=f"Contact {flight['airline']} or use booking link",
                booking_url=flight.get("booking_url"),
                contact_info=f"{flight['airline']} customer service",
                priority_rank=100 - (i * 10),
                ai_reasoning=f"{flight['stops']} stop(s), {flight['duration_minutes']}min",
                meta_data={
                    "flight_details": {
                        "flight_number": flight["flight_number"],
                        "airline": flight["airline"],
                        "departure_time": flight["departure_time"],
                        "arrival_time": flight["arrival_time"],
                        "duration_minutes": flight["duration_minutes"],
                        "stops": flight["stops"],
                        "price_amount": flight["price_amount"],
                        "price_currency": flight["price_currency"],
                    },
                    "pros": pros,
                    "cons": cons,
                    "recommended": i == 0,
                    "search_date": departure_date,
                    "contact_details": {          # ✅ NEW
                        "website": airline_info.get("website"),
                        "phone": airline_info.get("phone"),
                        "customer_service_url": airline_info.get("customer_service_url"),
                    }
                }
            )
            db.add(db_option)
            flight_options.append(db_option)

        db.commit()
        for opt in flight_options:
            db.refresh(opt)  # get real DB-assigned IDs and created_at
        logger.info(f"💾 Saved {len(flight_options)} flight options to DB for {departure_date}")

        from app.schemas.disruption import DisruptionOptionResponse
        option_responses = [DisruptionOptionResponse.model_validate(opt) for opt in flight_options]

        return SuggestOptionsResponse(
            options=option_responses,
            total_options=len(option_responses),
            generated_at=datetime.now(timezone.utc)
        )

    except Exception as e:
        logger.error(f"❌ Flight search failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Flight search failed: {str(e)}")

from app.schemas.disruption import ChatRequest, ChatResponse

@router.post("/{case_id}/chat", response_model=ChatResponse)
async def chat_with_assistant(
    case_id: int,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    case = db.query(DisruptionCase).filter(
        DisruptionCase.id == case_id,
        DisruptionCase.is_deleted == 0
    ).first()

    if not case:
        raise HTTPException(status_code=404, detail=f"Disruption case {case_id} not found")

    try:
        # Save user message
        db.add(DisruptionChatMessage(
            disruption_case_id=case_id,
            role="user",
            content=request.message,
        ))
        db.commit()

        # Generate response
        response_text = await disruption_agent.chat(
            disruption_case=case,
            user_message=request.message,
            conversation_history=request.history or [],
            db=db
        )

        # Save assistant response
        db.add(DisruptionChatMessage(
            disruption_case_id=case_id,
            role="assistant",
            content=response_text,
        ))
        db.commit()

        return ChatResponse(
            response=response_text,
            case_id=case_id,
            timestamp=datetime.now(timezone.utc)
        )

    except Exception as e:
        logger.error(f"❌ Chat failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/{case_id}/chat-history")
async def get_chat_history(
    case_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get chat history for a disruption case
    
    Returns recent conversation messages
    """
    # Verify case exists
    case = db.query(DisruptionCase).filter(
        DisruptionCase.id == case_id,
        DisruptionCase.is_deleted == 0
    ).first()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disruption case {case_id} not found"
        )
    
    msgs = (
        db.query(DisruptionChatMessage)
        .filter(DisruptionChatMessage.disruption_case_id == case_id)
        .order_by(DisruptionChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )
    return {
        "messages": [
            {
                "id": m.id,
                "case_id": case_id,
                "role": m.role,
                "content": m.content,
                "timestamp": m.created_at.isoformat(),
            }
            for m in msgs
        ],
        "case_id": case_id,
        "total": len(msgs),
    }

@router.get("/{case_id}/messages", response_model=List[DraftMessageResponse])
def get_draft_messages(
    case_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all draft messages generated for a disruption case
    
    Returns history of all generated emails/messages
    """
    # Verify case exists
    case = db.query(DisruptionCase).filter(
        DisruptionCase.id == case_id,
        DisruptionCase.is_deleted == 0
    ).first()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disruption case {case_id} not found"
        )
    
    # Get all draft messages for this case
    from app.models.draft_message import DraftMessage
    
    messages = db.query(DraftMessage).filter(
        DraftMessage.disruption_case_id == case_id
    ).order_by(DraftMessage.created_at.desc()).all()
    
     #  Convert to response format properly
    response_list = []
    for msg in messages:
        response_list.append(
            DraftMessageResponse(
                id=msg.id,
                disruption_case_id=msg.disruption_case_id,
                disruption_option_id=msg.disruption_option_id,
                recipient_type=msg.recipient_type.value if hasattr(msg.recipient_type, 'value') else msg.recipient_type,
                recipient_name=msg.recipient_name,
                recipient_email=msg.recipient_email,
                subject=msg.subject,
                body=msg.body,
                tone=msg.tone.value if hasattr(msg.tone, 'value') else msg.tone,
                language=msg.language,
                attachments_needed=msg.attachments_needed,
                next_steps=None,  # Not stored in DB
                created_at=msg.created_at
            )
        )
    
    logger.info(f"✅ Returning {len(response_list)} draft messages for case {case_id}")
    return response_list
