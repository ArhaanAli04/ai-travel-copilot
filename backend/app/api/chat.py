"""
API routes for Chat Session Management
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
from datetime import datetime,timezone

from app.services.chat_service import chat_service
from app.models.chat_session import (
    ChatSession,
    ChatMessage,
    CreateSessionRequest,
    UpdateSessionRequest,
    AddMessageRequest,
    ChatSessionResponse,
    ChatSessionListResponse,
    Location,
    UserPreferences
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat Sessions"])


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(request: CreateSessionRequest):
    """
    Create a new chat session
    
    Example request:
    ```json
    {
        "user_id": "user_123",
        "city": "mumbai",
        "location": {"lat": 19.0760, "lon": 72.8777},
        "title": "Coffee shops in Bandra"
    }
    ```
    """
    try:
        session = await chat_service.create_session(
            user_id=request.user_id,
            city=request.city,
            location=request.location.dict(),
            title=request.title
        )
        
        return ChatSessionResponse(
            session=session,
            message="Chat session created successfully"
        )
    
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=ChatSessionListResponse)
async def get_chat_sessions(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(50, description="Maximum number of sessions", ge=1, le=100)
):
    """
    Get all chat sessions for a user
    
    Returns sessions sorted by most recently updated first
    
    Example:
    /api/chat/sessions?user_id=user_123&limit=20
    """
    try:
        sessions = await chat_service.get_user_sessions(
            user_id=user_id,
            limit=limit
        )
        
        return ChatSessionListResponse(
            sessions=sessions,
            total=len(sessions)
        )
    
    except Exception as e:
        logger.error(f"Error fetching chat sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(session_id: str):
    """
    Get a specific chat session by ID
    
    Returns full session with all messages
    """
    try:
        session = await chat_service.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        return ChatSessionResponse(
            session=session,
            message="Success"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(session_id: str, request: UpdateSessionRequest):
    """
    Update chat session (currently only title)
    
    Example request:
    ```json
    {
        "title": "Best cafes in Bandra"
    }
    ```
    """
    try:
        # Check if session exists
        session = await chat_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Update title if provided
        if request.title:
            success = await chat_service.update_session_title(session_id, request.title)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to update session title")
        
        # ✅ NEW: Update manual context overrides if provided
        if request.manual_location or request.manual_city or request.manual_time:
            success = await chat_service.update_session_context(
                session_id,
                manual_location=request.manual_location.dict() if request.manual_location else None,
                manual_city=request.manual_city,
                manual_time=request.manual_time
            )
            if not success:
                raise HTTPException(status_code=500, detail="Failed to update session context")
            
        # Get updated session
        updated_session = await chat_service.get_session(session_id)
        
        return ChatSessionResponse(
            session=updated_session,
            message="Session updated successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/messages", response_model=ChatSessionResponse)
async def add_message_to_session(session_id: str, request: AddMessageRequest):
    """
    Add a message to a chat session
    
    Example request:
    ```json
    {
        "role": "user",
        "content": "Find me a coffee shop",
        "location": {"lat": 19.0760, "lon": 72.8777},
        "preferences": {
            "dietary": ["vegetarian"],
            "budget": "moderate"
        }
    }
    ```
    
    For assistant messages with POIs:
    ```json
    {
        "role": "assistant",
        "content": "Here are some great coffee shops:",
        "pois": [...]
    }
    ```
    """
    try:
        # Check if session exists
        session = await chat_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Create message object
        message = ChatMessage(
            id=f"{session_id}_{len(session.messages)}",
            role=request.role,
            content=request.content,
            pois=request.pois,
            timestamp=datetime.now(timezone.utc),
            location=request.location,
            preferences=request.preferences
        )
        
        # Add message to session
        success = await chat_service.add_message(session_id, message)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add message")
        
        # Get updated session
        updated_session = await chat_service.get_session(session_id)
        
        return ChatSessionResponse(
            session=updated_session,
            message="Message added successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding message to session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """
    Delete a chat session
    
    This permanently removes the session and all its messages
    """
    try:
        success = await chat_service.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        return {
            "message": "Session deleted successfully",
            "session_id": session_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for chat service"""
    return {
        "status": "healthy",
        "service": "chat_sessions",
        "version": "1.0.0"
    }
