"""
Collaborator endpoints for trip sharing
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime, timezone

from app.core.postgres import get_db
from app.core.dependencies import get_current_user, require_trip_owner, require_trip_access
from app.models.user import User
from app.models.collaborator import TripCollaborator, CollaboratorStatus, CollaboratorRole
from app.schemas.collaborator import (
    InviteCollaboratorRequest,
    ChangeRoleRequest,
    CollaboratorResponse,
    CollaboratorListResponse,
    InvitePreviewResponse,
    AcceptInviteResponse,
)
from app.services.invite_email import send_invite_email
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Collaborators"])


# ── POST /trips/{trip_id}/collaborators/invite ──────────────────────
@router.post("/trips/{trip_id}/collaborators/invite", response_model=CollaboratorResponse, status_code=201)
async def invite_collaborator(
    trip_id: int,
    body: InviteCollaboratorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Owner invites someone by email. Generates UUID token and sends invite email."""
    trip = require_trip_owner(trip_id, current_user, db)

    # Prevent duplicate pending invites for same email
    existing = db.query(TripCollaborator).filter(
        TripCollaborator.trip_id == trip_id,
        TripCollaborator.email == body.email,
        TripCollaborator.status == CollaboratorStatus.PENDING,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="A pending invite already exists for this email")

    # Prevent re-inviting an accepted collaborator
    accepted = db.query(TripCollaborator).filter(
        TripCollaborator.trip_id == trip_id,
        TripCollaborator.email == body.email,
        TripCollaborator.status == CollaboratorStatus.ACCEPTED,
    ).first()
    if accepted:
        raise HTTPException(status_code=409, detail="This person already has access to the trip")

    token = str(uuid.uuid4())
    collab = TripCollaborator(
        trip_id=trip_id,
        invited_by_user_id=current_user.id,
        email=body.email,
        role=body.role,
        status=CollaboratorStatus.PENDING,
        invite_token=token,
    )
    db.add(collab)
    db.commit()
    db.refresh(collab)

    # Send invite email (non-blocking failure — don't roll back if email fails)
    try:
        send_invite_email(
            to_email=body.email,
            invited_by_name=current_user.name or current_user.email,
            trip_title=trip.title,
            trip_destinations=trip.destinations,
            role=body.role.value,
            invite_token=token,
        )
    except Exception as e:
        logger.warning(f"⚠️ Invite created but email failed for {body.email}: {e}")

    logger.info(f"✅ Invited {body.email} to trip {trip_id} as {body.role.value}")
    return collab


# ── GET /trips/{trip_id}/collaborators ─────────────────────────────
@router.get("/trips/{trip_id}/collaborators", response_model=CollaboratorListResponse)
def list_collaborators(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all collaborators for a trip. Owner only."""
    require_trip_owner(trip_id, current_user, db)

    collabs = db.query(TripCollaborator).filter(
        TripCollaborator.trip_id == trip_id
    ).order_by(TripCollaborator.invited_at.desc()).all()

    return CollaboratorListResponse(trip_id=trip_id, collaborators=collabs, total=len(collabs))


# ── DELETE /trips/{trip_id}/collaborators/{collab_id} ──────────────
@router.delete("/trips/{trip_id}/collaborators/{collab_id}", status_code=204)
def remove_collaborator(
    trip_id: int,
    collab_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a collaborator. Owner only."""
    require_trip_owner(trip_id, current_user, db)

    collab = db.query(TripCollaborator).filter(
        TripCollaborator.id == collab_id,
        TripCollaborator.trip_id == trip_id,
    ).first()
    if not collab:
        raise HTTPException(status_code=404, detail="Collaborator not found")

    db.delete(collab)
    db.commit()
    logger.info(f"🗑️ Removed collaborator {collab_id} from trip {trip_id}")
    return None


# ── PATCH /trips/{trip_id}/collaborators/{collab_id} ───────────────
@router.patch("/trips/{trip_id}/collaborators/{collab_id}", response_model=CollaboratorResponse)
def change_collaborator_role(
    trip_id: int,
    collab_id: int,
    body: ChangeRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change a collaborator's role. Owner only."""
    require_trip_owner(trip_id, current_user, db)

    collab = db.query(TripCollaborator).filter(
        TripCollaborator.id == collab_id,
        TripCollaborator.trip_id == trip_id,
    ).first()
    if not collab:
        raise HTTPException(status_code=404, detail="Collaborator not found")

    collab.role = body.role
    db.commit()
    db.refresh(collab)
    logger.info(f"✏️ Changed collaborator {collab_id} role to {body.role.value}")
    return collab


# ── GET /invites/{token} ────────────────────────────────────────────
@router.get("/invites/{token}", response_model=InvitePreviewResponse)
def get_invite_preview(
    token: str,
    db: Session = Depends(get_db),
):
    """Validate token and return trip preview. Public — no auth required."""
    collab = db.query(TripCollaborator).filter(
        TripCollaborator.invite_token == token
    ).first()

    if not collab:
        raise HTTPException(status_code=404, detail="Invite not found or already used")
    if collab.status == CollaboratorStatus.DECLINED:
        raise HTTPException(status_code=410, detail="This invite was declined")
    if collab.status == CollaboratorStatus.ACCEPTED:
        raise HTTPException(status_code=410, detail="This invite was already accepted")

    trip = collab.trip
    inviter = db.query(User).filter(User.id == collab.invited_by_user_id).first()

    return InvitePreviewResponse(
        token=token,
        trip_id=trip.id,
        trip_title=trip.title,
        trip_origin=trip.origin,
        destinations=trip.destinations,
        start_date=trip.start_date,
        end_date=trip.end_date,
        invited_by_name=inviter.name or inviter.email if inviter else None,
        role=collab.role,
        status=collab.status,
    )


# ── POST /invites/{token}/accept ────────────────────────────────────
@router.post("/invites/{token}/accept", response_model=AcceptInviteResponse)
def accept_invite(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept an invite. Links current user's clerk_id to the collaborator row."""
    collab = db.query(TripCollaborator).filter(
        TripCollaborator.invite_token == token
    ).first()

    if not collab:
        raise HTTPException(status_code=404, detail="Invite not found")
    if collab.status == CollaboratorStatus.ACCEPTED:
        raise HTTPException(status_code=410, detail="Invite already accepted")
    if collab.status == CollaboratorStatus.DECLINED:
        raise HTTPException(status_code=410, detail="Invite was declined")

    # Prevent owner from accepting their own invite
    if collab.trip.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You are already the owner of this trip")

    collab.clerk_user_id = current_user.clerk_id
    collab.status = CollaboratorStatus.ACCEPTED
    collab.accepted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(collab)

    logger.info(f"✅ User {current_user.id} accepted invite to trip {collab.trip_id}")
    return AcceptInviteResponse(
        success=True,
        message="You now have access to this trip",
        trip_id=collab.trip_id,
        trip_title=collab.trip.title,
        role=collab.role,
    )
