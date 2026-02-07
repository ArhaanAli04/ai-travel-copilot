"""
Service for managing user preferences persistence
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime,timezone
from app.core.mongo import get_database

logger = logging.getLogger(__name__)


class PreferencesService:
    """Service for user preferences"""
    
    def __init__(self):
        self.db = None
        self.collection = None
    
    def _get_collection(self):
        """Get MongoDB collection (lazy initialization)"""
        if self.collection is None:
            self.db = get_database()
            if self.db is None:
                raise RuntimeError("MongoDB database not initialized")
            self.collection = self.db["user_preferences"]
        return self.collection
    
    async def save_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save or update user preferences
        
        Args:
            user_id: User identifier
            preferences: Preferences dict
            
        Returns:
            Saved preferences with metadata
        """
        try:
            collection = self._get_collection()
            
            document = {
                "user_id": user_id,
                "preferences": preferences,
                "updated_at": datetime.now(timezone.utc)
            }
            
            # Upsert (update if exists, insert if not)
            result = await collection.update_one(
                {"user_id": user_id},
                {"$set": document},
                upsert=True
            )
            
            logger.info(f"✅ Saved preferences for user {user_id}")
            
            return {
                "user_id": user_id,
                "preferences": preferences,
                "updated_at": document["updated_at"]
            }
        
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")
            raise
    
    async def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user preferences
        
        Args:
            user_id: User identifier
            
        Returns:
            Preferences dict or None if not found
        """
        try:
            collection = self._get_collection()
            
            document = await collection.find_one({"user_id": user_id})
            
            if not document:
                logger.info(f"No preferences found for user {user_id}")
                return None
            
            return {
                "user_id": document["user_id"],
                "preferences": document.get("preferences", {}),
                "updated_at": document.get("updated_at")
            }
        
        except Exception as e:
            logger.error(f"Error fetching preferences: {e}")
            raise
    
    async def delete_preferences(self, user_id: str) -> bool:
        """
        Delete user preferences
        
        Args:
            user_id: User identifier
            
        Returns:
            True if deleted, False if not found
        """
        try:
            collection = self._get_collection()
            
            result = await collection.delete_one({"user_id": user_id})
            
            if result.deleted_count > 0:
                logger.info(f"✅ Deleted preferences for user {user_id}")
                return True
            else:
                logger.info(f"No preferences to delete for user {user_id}")
                return False
        
        except Exception as e:
            logger.error(f"Error deleting preferences: {e}")
            raise


# Singleton instance
preferences_service = PreferencesService()
