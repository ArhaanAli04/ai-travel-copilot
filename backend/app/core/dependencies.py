from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.postgres import get_db
from app.core.clerk import verify_clerk_token
from app.models.user import User
import jwt
import logging

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and verify Clerk JWT, return the matching User from DB.
    Raises 401 if token is missing or invalid.
    Raises 404 if user not yet synced (should call /auth/sync first).
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    try:
        payload = await verify_clerk_token(credentials.credentials)
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )

    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
        )

    user = db.query(User).filter(User.clerk_id == clerk_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Call /api/auth/sync first.",
        )

    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Same as get_current_user but returns None instead of raising 401."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None

from app.models.collaborator import TripCollaborator, CollaboratorStatus, CollaboratorRole
from app.models.trip import Trip


def get_trip_or_404(trip_id: int, db: Session) -> Trip:
    """Fetch trip or raise 404."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")
    return trip


def require_trip_owner(trip_id: int, current_user: User, db: Session) -> Trip:
    """
    Return trip if current_user is the owner, else raise 403.
    Use for: delete, invite, remove collaborator, change role, toggle favorite.
    """
    trip = get_trip_or_404(trip_id, db)
    if trip.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the trip owner can perform this action")
    return trip


def require_trip_access(trip_id: int, current_user: User, db: Session) -> tuple[Trip, str]:
    """
    Return (trip, role) if current_user is owner OR accepted collaborator.
    role is 'owner' | 'editor' | 'viewer'.
    Use for: read trip, generate itinerary, update trip, reorder, replan.
    """
    trip = get_trip_or_404(trip_id, db)

    # Owner always has full access
    if trip.user_id == current_user.id:
        return trip, "owner"

    # Check accepted collaborator
    collab = db.query(TripCollaborator).filter(
        TripCollaborator.trip_id == trip_id,
        TripCollaborator.clerk_user_id == current_user.clerk_id,
        TripCollaborator.status == CollaboratorStatus.ACCEPTED,
    ).first()

    if not collab:
        raise HTTPException(status_code=403, detail="You do not have access to this trip")

    return trip, collab.role.value


def require_trip_editor(trip_id: int, current_user: User, db: Session) -> Trip:
    """
    Return trip if current_user is owner or editor. Raise 403 for viewers.
    Use for: mutating routes — plan, update, reorder, replan, email.
    """
    trip, role = require_trip_access(trip_id, current_user, db)
    if role == "viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot modify this trip")
    return trip