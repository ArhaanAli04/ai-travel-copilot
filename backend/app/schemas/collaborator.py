"""
Pydantic schemas for collaborator API
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.collaborator import CollaboratorRole, CollaboratorStatus


class InviteCollaboratorRequest(BaseModel):
    email: EmailStr = Field(..., description="Email to invite")
    role: CollaboratorRole = Field(CollaboratorRole.VIEWER, description="viewer or editor")

    model_config = ConfigDict(json_schema_extra={
        "example": {"email": "friend@example.com", "role": "editor"}
    })


class ChangeRoleRequest(BaseModel):
    role: CollaboratorRole = Field(..., description="New role for collaborator")


class CollaboratorResponse(BaseModel):
    id:                 int
    trip_id:            int
    invited_by_user_id: int
    email:              str
    clerk_user_id:      Optional[str]
    role:               CollaboratorRole
    status:             CollaboratorStatus
    invite_token:       str
    invited_at:         datetime
    accepted_at:        Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class CollaboratorListResponse(BaseModel):
    trip_id:       int
    collaborators: List[CollaboratorResponse]
    total:         int


class InvitePreviewResponse(BaseModel):
    """Returned when validating a token before accepting"""
    token:           str
    trip_id:         int
    trip_title:      str
    trip_origin:     str
    destinations:    List[str]
    start_date:      datetime
    end_date:        datetime
    invited_by_name: Optional[str]
    role:            CollaboratorRole
    status:          CollaboratorStatus


class AcceptInviteResponse(BaseModel):
    success:    bool
    message:    str
    trip_id:    int
    trip_title: str
    role:       CollaboratorRole
