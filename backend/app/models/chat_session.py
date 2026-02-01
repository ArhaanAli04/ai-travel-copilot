"""
Pydantic models for Chat Sessions
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


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
    id: str = Field(..., description="Message ID")
    role: str = Field(..., description="Role: user or assistant")
    content: str = Field(..., description="Message content")
    pois: Optional[List[Dict[str, Any]]] = Field(default=None, description="POI recommendations")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    location: Optional[Location] = None
    preferences: Optional[UserPreferences] = None


class ChatSession(BaseModel):
    """Chat session"""
    id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID (session ID for anonymous)")
    title: str = Field(..., description="Session title")
    city: str = Field(..., description="City")
    location: Location = Field(..., description="User location")
    messages: List[ChatMessage] = Field(default=[], description="Chat messages")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CreateSessionRequest(BaseModel):
    """Request to create new chat session"""
    user_id: str = Field(..., description="User ID")
    city: str = Field(..., description="City name")
    location: Location = Field(..., description="User location")
    title: Optional[str] = Field(default="New Chat", description="Session title")


class UpdateSessionRequest(BaseModel):
    """Request to update session"""
    title: Optional[str] = None


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
