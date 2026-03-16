"""
Documentation API endpoints
Handles generation, retrieval, and regeneration of trip documentation
(visa requirements, entry rules, legal advisories, emergency contacts)
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import asyncio
import logging

from app.core.postgres import get_db
from app.core.dependencies import get_current_user, require_trip_access, require_trip_editor
from app.models.user import User
from app.models.documentation import TripDocumentation
from app.schemas.documentation import (
    DocumentationResponse,
    DocumentationGenerateResponse,
    DocumentationStatusResponse,
)
from app.ai.documentation_agent import create_documentation_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trips", tags=["Documentation"])


# ── Helper ──────────────────────────────────────────────────────────

def _doc_to_response(doc: TripDocumentation) -> DocumentationResponse:
    """
    Convert TripDocumentation ORM object to DocumentationResponse schema.
    Safely handles None JSON fields by defaulting to empty lists.
    """
    return DocumentationResponse(
        id=doc.id,
        trip_id=doc.trip_id,
        origin_country=doc.origin_country,
        document_checklist=doc.document_checklist or [],
        entry_requirements=doc.entry_requirements or [],
        legal_advisories=doc.legal_advisories or [],
        emergency_contacts=doc.emergency_contacts or [],
        generated_at=doc.generated_at,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


# ── Endpoints ───────────────────────────────────────────────────────

@router.post(
    "/{trip_id}/documentation/generate",
    response_model=DocumentationResponse,
    summary="Generate trip documentation",
    description="""
Generate legal and travel documentation for a trip using AI.

Generates for each destination:
- **Document checklist** — visa type, cost, processing time, procedure, required documents
- **Entry requirements** — health, customs, restricted items, minor travel rules
- **Legal advisories** — drug laws, LGBTQ+ status, drone/photography restrictions
- **Emergency contacts** — embassy, police, ambulance, hospital recommendations

**Permissions:** Owner or Editor only (viewers cannot trigger generation)
**Note:** First-time generation for this trip. Use `/regenerate` to refresh existing docs.
    """,
)
async def generate_documentation(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate documentation for a trip (first time)."""
    try:
        # Permission check — editors and owners only
        require_trip_editor(trip_id, current_user, db)

        # Check if documentation already exists — direct to regenerate
        existing = (
            db.query(TripDocumentation)
            .filter(TripDocumentation.trip_id == trip_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Documentation already exists for this trip. Use /regenerate to refresh.",
            )

        # Run documentation agent
        logger.info(f"📋 Starting documentation generation for trip {trip_id}")
        agent = create_documentation_agent(db)
        doc = await agent.generate_documentation(trip_id)

        logger.info(f"✅ Documentation generated for trip {trip_id}")
        return _doc_to_response(doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Documentation generation failed for trip {trip_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate documentation: {str(e)}",
        )


@router.get(
    "/{trip_id}/documentation",
    response_model=DocumentationResponse,
    summary="Get trip documentation",
    description="""
Retrieve stored legal and travel documentation for a trip.

Returns 404 if documentation has not been generated yet.
Use `POST /generate` to create documentation first.

**Permissions:** Owner, Editor, or Viewer (read-only access)
    """,
)
async def get_documentation(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get existing documentation for a trip."""
    try:
        # Permission check — viewers can read
        require_trip_access(trip_id, current_user, db)

        doc = (
            db.query(TripDocumentation)
            .filter(TripDocumentation.trip_id == trip_id)
            .first()
        )

        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Documentation not yet generated for this trip.",
            )

        return _doc_to_response(doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch documentation for trip {trip_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch documentation: {str(e)}",
        )


@router.post(
    "/{trip_id}/documentation/regenerate",
    response_model=DocumentationResponse,
    summary="Regenerate trip documentation",
    description="""
Regenerate legal and travel documentation for a trip.

Deletes existing documentation and generates fresh data.
Use this when trip details have changed (new destinations, different origin, etc.)

**Permissions:** Owner or Editor only
    """,
)
async def regenerate_documentation(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Regenerate documentation for a trip (replaces existing)."""
    try:
        # Permission check — editors and owners only
        require_trip_editor(trip_id, current_user, db)

        # Delete existing documentation if present
        existing = (
            db.query(TripDocumentation)
            .filter(TripDocumentation.trip_id == trip_id)
            .first()
        )
        if existing:
            logger.info(f"🗑️ Deleting existing documentation for trip {trip_id} to regenerate")
            db.delete(existing)
            db.commit()

        # Run documentation agent fresh
        logger.info(f"🔄 Regenerating documentation for trip {trip_id}")
        agent = create_documentation_agent(db)
        doc = await agent.generate_documentation(trip_id)

        logger.info(f"✅ Documentation regenerated for trip {trip_id}")
        return _doc_to_response(doc)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Documentation regeneration failed for trip {trip_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to regenerate documentation: {str(e)}",
        )


@router.get(
    "/{trip_id}/documentation/status",
    response_model=DocumentationStatusResponse,
    summary="Check documentation status",
    description="""
Lightweight check — returns whether documentation exists for a trip.
Used by frontend to decide whether to show Generate or View button.

**Permissions:** Owner, Editor, or Viewer
    """,
)
async def get_documentation_status(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if documentation exists for a trip."""
    try:
        require_trip_access(trip_id, current_user, db)

        doc = (
            db.query(TripDocumentation)
            .filter(TripDocumentation.trip_id == trip_id)
            .first()
        )

        return DocumentationStatusResponse(
            trip_id=trip_id,
            exists=doc is not None,
            generated_at=doc.generated_at if doc else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to check documentation status for trip {trip_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check documentation status: {str(e)}",
        )
