"""
Service for chat session management
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime,timezone
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
        title: str = "New Chat",
        clerk_id: Optional[str] = None,
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
                "clerk_id": clerk_id,
                "title": title,
                "city": city,
                "location": location,
                "messages": [],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                # ✅ NEW: Initialize manual overrides as None (use defaults)
                "manual_location": None,
                "manual_city": None,
                "manual_time": None
            }
            
            result = await self.sessions_collection.insert_one(session_doc)
            session_id = str(result.inserted_id)
            
            logger.info(f"✅ Created chat session {session_id} for user {user_id}")
            
            return ChatSession(
                id=session_id,
                user_id=user_id,
                clerk_id=clerk_id,
                title=title,
                city=city,
                location=location,
                messages=[],
                created_at=session_doc["created_at"],
                updated_at=session_doc["updated_at"],
                manual_location=None,
                manual_city=None,
                manual_time=None
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
        limit: int = 50,
        clerk_id: Optional[str] = None,
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
            # Prefer clerk_id filter but also catch old sessions by user_id
            if clerk_id:
                query = {"$or": [{"clerk_id": clerk_id}, {"user_id": user_id}]}
            else:
                query = {"user_id": user_id}

            cursor = self.sessions_collection.find(query).sort("updated_at", -1).limit(limit)
            
            sessions = await cursor.to_list(length=limit)
            # ✅ DEBUG: Log timestamps
            for doc in sessions[:3]:  # First 3 sessions
                logger.info(f"📊 Session {doc.get('title')}: updated_at = {doc.get('updated_at')}")
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
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            return result.modified_count > 0
        
        except Exception as e:
            logger.error(f"❌ Error updating session title: {e}")
            return False
    
    # ✅ NEW: Update manual overrides
    async def update_session_context(
        self,
        session_id: str,
        manual_location: Optional[Dict[str, float]] = None,
        manual_city: Optional[str] = None,
        manual_time: Optional[str] = None
    ) -> bool:
        """
        Update session's manual location/time overrides
        
        Args:
            session_id: Session ID
            manual_location: Manual location override (or None to clear)
            manual_city: Manual city override (or None to clear)
            manual_time: Manual time override (or None to clear)
            
        Returns:
            True if successful
        """
        try:
            update_fields = {"updated_at": datetime.now(timezone.utc)}
            
            # Only update fields that are explicitly provided
            if manual_location is not None:
                update_fields["manual_location"] = manual_location
            if manual_city is not None:
                update_fields["manual_city"] = manual_city
            if manual_time is not None:
                update_fields["manual_time"] = manual_time
            
            result = await self.sessions_collection.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": update_fields}
            )
            
            logger.info(f"✅ Updated context for session {session_id}")
            return result.modified_count > 0
        
        except Exception as e:
            logger.error(f"❌ Error updating session context: {e}")
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
            # ✅ Get current time
            now = datetime.now(timezone.utc)
            
            # Check if we need to update title (for first user message)
            update_fields = {"updated_at": now}
            if message.role == "user":
                session = await self.get_session(session_id)
                if session and session.title == "New Chat":
                    # Update title in same query (optimize to single DB call)
                    update_fields["title"] = message.content[:50]

            # ✅ LOG: Show what we're updating
            logger.info(f"🕐 Updating session {session_id} timestamp to: {now}")

            result = await self.sessions_collection.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$push": {"messages": message_doc},
                    "$set": update_fields
                }
            )
            
             
            logger.info(f"✅ Added message to session {session_id}, modified_count: {result.modified_count}")
            
            # ✅ VERIFY: Check if update worked
            if result.modified_count > 0:
                updated_session = await self.sessions_collection.find_one({"_id": ObjectId(session_id)})
                logger.info(f"✅ Verified updated_at: {updated_session.get('updated_at')}")
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
    
        # Helper function to ensure timezone-aware datetime
        def ensure_timezone_aware(dt):
            """Convert naive datetime to timezone-aware UTC"""
            if dt is None:
                return None
            if dt.tzinfo is None:
                # Naive datetime - assume it's UTC and add timezone
                return dt.replace(tzinfo=timezone.utc)
            return dt
        
        # Convert message timestamps to timezone-aware
        messages = []
        for msg in doc.get("messages", []):
            msg_copy = msg.copy()
            if "timestamp" in msg_copy and msg_copy["timestamp"]:
                msg_copy["timestamp"] = ensure_timezone_aware(msg_copy["timestamp"])
            messages.append(ChatMessage(**msg_copy))
        
        return ChatSession(
            id=str(doc["_id"]),
            user_id=doc["user_id"],
            clerk_id=doc.get("clerk_id"),
            title=doc["title"],
            city=doc["city"],
            location=doc["location"],
            messages=messages,
            created_at=ensure_timezone_aware(doc["created_at"]),
            updated_at=ensure_timezone_aware(doc["updated_at"]),
            manual_location=doc.get("manual_location"),
            manual_city=doc.get("manual_city"),
            manual_time=doc.get("manual_time")
        )


# Singleton instance
chat_service = ChatService()
