"""
Pydantic models for Chat Sessions
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime,timezone


class Location(BaseModel):
    """Location coordinates"""
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")


class UserPreferences(BaseModel):
    """User preferences"""
    dietary: Optional[List[str]] = None
    cuisines: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    budget: Optional[str] = None
    time_constraint: Optional[str] = None
    group_size: Optional[int] = None


class ChatMessage(BaseModel):
    """Single message in chat"""
    model_config = ConfigDict(json_encoders={
        datetime: lambda v: v.isoformat() if v else None
    })
    id: str = Field(..., description="Message ID")
    role: str = Field(..., description="Role: user or assistant")
    content: str = Field(..., description="Message content")
    pois: Optional[List[Dict[str, Any]]] = Field(default=None, description="POI recommendations")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    location: Optional[Location] = None
    preferences: Optional[UserPreferences] = None


class ChatSession(BaseModel):
    """Chat session"""
    id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="Legacy session-based user ID")
    clerk_id: Optional[str] = Field(None, description="Clerk user ID — primary auth identifier") 
    title: str 
    city: str 
    location: Location 
    messages: List[ChatMessage] = Field(default=[], description="Chat messages")
    created_at: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ✅ NEW: Manual overrides
    manual_location: Optional[Location] = Field(None, description="Manually set location (overrides default)")
    manual_city: Optional[str] = Field(None, description="Manually set city name")
    manual_time: Optional[str] = Field(None, description="Manually set time of day (morning/afternoon/evening/night)")

class CreateSessionRequest(BaseModel):
    """Request to create new chat session"""
    
    city: str
    location: Location
    title: Optional[str] = Field(default="New Chat")


class UpdateSessionRequest(BaseModel):
    """Request to update session"""
    title: Optional[str] = None
    # ✅ NEW: Allow updating manual overrides
    manual_location: Optional[Location] = None
    manual_city: Optional[str] = None
    manual_time: Optional[str] = None

class AddMessageRequest(BaseModel):
    """Request to add message to session"""
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")
    pois: Optional[List[Dict[str, Any]]] = None
    location: Optional[Location] = None
    preferences: Optional[UserPreferences] = None


class ChatSessionResponse(BaseModel):
    """Response with chat session"""
    session: ChatSession
    message: str = "Success"


class ChatSessionListResponse(BaseModel):
    """Response with list of sessions"""
    sessions: List[ChatSession]
    total: int
