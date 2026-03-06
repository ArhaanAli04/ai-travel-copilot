from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.postgres import get_db
from app.core.clerk import verify_clerk_token
from app.models.user import User
from pydantic import BaseModel
from typing import Optional
import jwt
import logging
import httpx
from app.core.config import settings
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])
bearer_scheme = HTTPBearer()


class UserSyncResponse(BaseModel):
    id: int
    clerk_id: str
    email: str
    name: Optional[str]
    is_new: bool

    class Config:
        from_attributes = True


@router.post("/sync", response_model=UserSyncResponse)
async def sync_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """
    Called once after Clerk login to upsert user into our DB.
    Creates user if first time, updates name/email if changed.
    """
    try:
        payload = await verify_clerk_token(credentials.credentials)
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    clerk_id = payload.get("sub")

    if not clerk_id:
        raise HTTPException(status_code=400, detail="Invalid Clerk token: missing sub")

    # Extract from JWT first
    email = (
        payload.get("email")
        or payload.get("email_address")
        or ""
    )
    name = (
        payload.get("name")
        or payload.get("full_name")
        or payload.get("username")
        or ""
    )

    # If email missing, fetch directly from Clerk REST API
    if not email or email.endswith("@clerk.local"):
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.clerk.com/v1/users/{clerk_id}",
                headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"}
            )
            if resp.status_code == 200:
                clerk_user = resp.json()
                email_objs = clerk_user.get("email_addresses", [])
                if email_objs:
                    email = email_objs[0].get("email_address", "")
                if not name:
                    first = clerk_user.get("first_name") or ""
                    last = clerk_user.get("last_name") or ""
                    name = f"{first} {last}".strip()
    # Try to find existing user
    user = db.query(User).filter(User.clerk_id == clerk_id).first()

    if user:
        # Update in case name/email changed in Clerk
        if email and user.email != email:
            user.email = email
        if name:
            user.name = name
        db.commit()
        db.refresh(user)
        return UserSyncResponse(**user.__dict__, is_new=False)

    # Check if email already exists (pre-Clerk user)
    if email:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            existing.clerk_id = clerk_id
            existing.is_verified = True
            if name:
                existing.name = name
            db.commit()
            db.refresh(existing)
            return UserSyncResponse(**existing.__dict__, is_new=False)

    # Create new user
    new_user = User(
        clerk_id=clerk_id,
        email=email or f"{clerk_id}@clerk.local",
        name=name or "",
        provider="clerk",
        is_active=True,
        is_verified=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return UserSyncResponse(**new_user.__dict__, is_new=True)
