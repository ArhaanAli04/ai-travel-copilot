"""
Service for chat session management
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import certifi

from app.core.config import settings
from app.models.chat_session import ChatSession, ChatMessage

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat sessions"""
    
    def __init__(self):
        self.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        self.db = self.client.get_database("travel_copilot")
        self.sessions_collection = self.db["chat_sessions"]
    
    async def create_session(
        self,
        user_id: str,
        city: str,
        location: Dict[str, float],
        title: str = "New Chat"
    ) -> ChatSession:
        """
        Create a new chat session
        
        Args:
            user_id: User ID
            city: City name
            location: User location coordinates
            title: Session title
            
        Returns:
            Created chat session
        """
        try:
            session_doc = {
                "user_id": user_id,
                "title": title,
                "city": city,
                "location": location,
                "messages": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.sessions_collection.insert_one(session_doc)
            session_id = str(result.inserted_id)
            
            logger.info(f"✅ Created chat session {session_id} for user {user_id}")
            
            return ChatSession(
                id=session_id,
                user_id=user_id,
                title=title,
                city=city,
                location=location,
                messages=[],
                created_at=session_doc["created_at"],
                updated_at=session_doc["updated_at"]
            )
        
        except Exception as e:
            logger.error(f"❌ Error creating chat session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Get chat session by ID
        
        Args:
            session_id: Session ID
            
        Returns:
            Chat session or None if not found
        """
        try:
            session_doc = await self.sessions_collection.find_one({"_id": ObjectId(session_id)})
            
            if not session_doc:
                return None
            
            return self._doc_to_session(session_doc)
        
        except Exception as e:
            logger.error(f"❌ Error fetching session {session_id}: {e}")
            return None
    
    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[ChatSession]:
        """
        Get all sessions for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of sessions
            
        Returns:
            List of chat sessions
        """
        try:
            cursor = self.sessions_collection.find(
                {"user_id": user_id}
            ).sort("updated_at", -1).limit(limit)
            
            sessions = await cursor.to_list(length=limit)
            
            return [self._doc_to_session(doc) for doc in sessions]
        
        except Exception as e:
            logger.error(f"❌ Error fetching user sessions: {e}")
            return []
    
    async def update_session_title(self, session_id: str, title: str) -> bool:
        """
        Update session title
        
        Args:
            session_id: Session ID
            title: New title
            
        Returns:
            True if successful
        """
        try:
            result = await self.sessions_collection.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$set": {
                        "title": title,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        
        except Exception as e:
            logger.error(f"❌ Error updating session title: {e}")
            return False
    
    async def add_message(
        self,
        session_id: str,
        message: ChatMessage
    ) -> bool:
        """
        Add message to chat session
        
        Args:
            session_id: Session ID
            message: Chat message
            
        Returns:
            True if successful
        """
        try:
            message_doc = {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "pois": message.pois,
                "timestamp": message.timestamp,
                "location": message.location.dict() if message.location else None,
                "preferences": message.preferences.dict() if message.preferences else None
            }
            
            result = await self.sessions_collection.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$push": {"messages": message_doc},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            # Auto-update title from first user message
            if message.role == "user":
                session = await self.get_session(session_id)
                if session and session.title == "New Chat":
                    await self.update_session_title(
                        session_id,
                        message.content[:50]  # First 50 chars
                    )
            
            return result.modified_count > 0
        
        except Exception as e:
            logger.error(f"❌ Error adding message to session: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete chat session
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful
        """
        try:
            result = await self.sessions_collection.delete_one({"_id": ObjectId(session_id)})
            
            logger.info(f"🗑️  Deleted chat session {session_id}")
            
            return result.deleted_count > 0
        
        except Exception as e:
            logger.error(f"❌ Error deleting session: {e}")
            return False
    
    def _doc_to_session(self, doc: Dict) -> ChatSession:
        """Convert MongoDB document to ChatSession object"""
        return ChatSession(
            id=str(doc["_id"]),
            user_id=doc["user_id"],
            title=doc["title"],
            city=doc["city"],
            location=doc["location"],
            messages=[
                ChatMessage(**msg) for msg in doc.get("messages", [])
            ],
            created_at=doc["created_at"],
            updated_at=doc["updated_at"]
        )


# Singleton instance
chat_service = ChatService()
