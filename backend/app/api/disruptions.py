"""
API endpoints for travel disruption management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime,timezone
import logging

from app.core.postgres import get_db
from app.models.disruption import DisruptionCase, DisruptionOption, DisruptionType, DisruptionSeverity
from app.schemas.disruption import (
    DisruptionCaseCreate,
    DisruptionCaseUpdate,
    DisruptionCaseResponse,
    DisruptionCaseWithOptions,
    DisruptionCaseListResponse,
    DisruptionOptionCreate,
    DisruptionOptionResponse
)
from app.services.disruption_service import disruption_service  # ✅ ADD THIS IMPORT


router = APIRouter(prefix="/disruptions", tags=["disruptions"])
logger = logging.getLogger(__name__)


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
        # Auto-detect disruption type from notes (simple heuristic for now)
        disruption_type = _detect_disruption_type(case_data.notes or "")
        
        # Create case
        db_case = DisruptionCase(
            flight_number=case_data.flight_number.upper(),
            airline=case_data.airline,
            origin=case_data.origin,
            destination=case_data.destination,
            disruption_date=case_data.disruption_date,
            disruption_type=disruption_type,
            pnr=case_data.pnr,
            notes=case_data.notes,
            current_status="Checking flight status",
            severity=DisruptionSeverity.LOW,
            meta_data={}
        )
        
        db.add(db_case)
        db.commit()
        db.refresh(db_case)
        
        logger.info(f"✅ Created disruption case {db_case.id} for flight {db_case.flight_number}")
        try:
            db_case = await disruption_service.enrich_disruption_case(db_case, db)
            logger.info(f"✅ Case {db_case.id} auto-enriched with flight/weather data")
        except Exception as e:
            logger.warning(f"⚠️ Auto-enrichment failed (case still created): {e}")
            # Don't fail the request if enrichment fails
        return db_case
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error creating disruption case: {e}")
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

# ===== Helper Functions =====
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
