"""
Service for handling user feedback on POIs
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import certifi
from app.core.config import settings

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service for POI feedback operations"""
    
    def __init__(self):
        # FIXED: Use same connection pattern as mongo.py
        self.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        self.db = self.client.get_database("travel_copilot")  #  FIXED: Use correct database name
        self.pois_collection = self.db["pois"]
    
    async def submit_feedback(
        self,
        poi_id: str,
        user_id: str,
        feedback_type: str,
        rating: Optional[int] = None,
        visited_at: Optional[datetime] = None,
        comment: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Submit user feedback for a POI
        
        Args:
            poi_id: MongoDB POI ID
            user_id: User ID (session ID for anonymous)
            feedback_type: 'thumbs_up', 'thumbs_down', or 'rating'
            rating: Star rating (1-5) if feedback_type is 'rating'
            visited_at: When user visited
            comment: Optional comment
            tags: Experience tags
            
        Returns:
            Dict with success status and updated stats
        """
        try:
            logger.info(f"📝 Submitting feedback for POI {poi_id} by user {user_id}")
            
            # Validate POI exists
            poi = await self.pois_collection.find_one({"_id": ObjectId(poi_id)})
            if not poi:
                raise ValueError(f"POI {poi_id} not found")
            
            # Create feedback object
            feedback_obj = {
                "user_id": user_id,
                "feedback_type": feedback_type,
                "rating": rating,
                "visited_at": visited_at or datetime.utcnow(),
                "comment": comment,
                "tags": tags or [],
                "submitted_at": datetime.utcnow()
            }
            
            # Add feedback to array
            await self.pois_collection.update_one(
                {"_id": ObjectId(poi_id)},
                {
                    "$push": {"user_feedback": feedback_obj},
                    "$set": {"last_feedback_at": datetime.utcnow()}
                }
            )
            
            # Recalculate stats
            updated_stats = await self._recalculate_poi_stats(poi_id)
            
            logger.info(f"✅ Feedback submitted successfully")
            logger.info(f"   New avg rating: {updated_stats['average_rating']:.2f}")
            logger.info(f"   Total feedback: {updated_stats['feedback_count']}")
            
            return {
                "success": True,
                "message": "Feedback submitted successfully",
                "poi_id": poi_id,
                "feedback_id": str(ObjectId()),  # Generate ID for this feedback
                "updated_stats": updated_stats
            }
        
        except Exception as e:
            logger.error(f"❌ Error submitting feedback: {e}")
            raise
    
    async def _recalculate_poi_stats(self, poi_id: str) -> Dict[str, Any]:
        """
        Recalculate POI statistics based on all feedback
        
        Returns:
            Dict with average_rating, feedback_count, etc.
        """
        poi = await self.pois_collection.find_one({"_id": ObjectId(poi_id)})
        if not poi:
            raise ValueError(f"POI {poi_id} not found")
        
        feedback_list = poi.get("user_feedback", [])
        
        if not feedback_list:
            stats = {
                "average_rating": 0.0,
                "feedback_count": 0,
                "positive_feedback_count": 0,
                "negative_feedback_count": 0
            }
        else:
            # Calculate stats
            total_feedback = len(feedback_list)
            positive_count = sum(1 for f in feedback_list if f["feedback_type"] == "thumbs_up")
            negative_count = sum(1 for f in feedback_list if f["feedback_type"] == "thumbs_down")
            
            # Calculate average rating from star ratings and thumbs
            ratings = []
            for f in feedback_list:
                if f["feedback_type"] == "rating" and f.get("rating"):
                    ratings.append(f["rating"])
                elif f["feedback_type"] == "thumbs_up":
                    ratings.append(5)  # Convert thumbs up to 5 stars
                elif f["feedback_type"] == "thumbs_down":
                    ratings.append(1)  # Convert thumbs down to 1 star
            
            avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
            
            stats = {
                "average_rating": round(avg_rating, 2),
                "feedback_count": total_feedback,
                "positive_feedback_count": positive_count,
                "negative_feedback_count": negative_count
            }
        
        # Update POI document
        await self.pois_collection.update_one(
            {"_id": ObjectId(poi_id)},
            {"$set": stats}
        )
        
        return stats
    
    async def get_trending_pois(
        self,
        city: str,
        category: Optional[str] = None,
        limit: int = 10,
        min_feedback_count: int = 5,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get trending POIs based on recent feedback
        
        Args:
            city: City name
            category: Optional category filter
            limit: Max results
            min_feedback_count: Minimum feedback required
            days: Look back period in days
            
        Returns:
            List of trending POIs with stats
        """
        try:
            logger.info(f"📈 Getting trending POIs for {city}")
            
            # Build query
            query = {
                "city": city,
                "feedback_count": {"$gte": min_feedback_count}
            }
            
            if category:
                query["category"] = category
            
            # Calculate cutoff date for recency
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Find POIs with pipeline for trending score
            pipeline = [
                {"$match": query},
                {
                    "$addFields": {
                        # Calculate trending score (rating * recency_weight)
                        "recency_weight": {
                            "$cond": {
                                "if": {"$gte": ["$last_feedback_at", cutoff_date]},
                                "then": 2.0,  # 2x boost for recent feedback
                                "else": 1.0
                            }
                        },
                        "trending_score": {
                            "$multiply": [
                                {"$ifNull": ["$average_rating", 0]},  # ✅ Handle null ratings
                                {"$add": [1, {"$divide": [{"$ifNull": ["$feedback_count", 0]}, 10]}]},  # ✅ Handle null counts
                                {
                                    "$cond": {
                                        "if": {"$gte": ["$last_feedback_at", cutoff_date]},
                                        "then": 2.0,
                                        "else": 1.0
                                    }
                                }
                            ]
                        }
                    }
                },
                {"$sort": {"trending_score": -1, "feedback_count": -1}},
                {"$limit": limit},
                {
                    "$project": {
                        "poi_id": {"$toString": "$_id"},
                        "name": 1,
                        "category": 1,
                        "city": 1,
                        "location": 1,
                        "address": 1,
                        "average_rating": {"$ifNull": ["$average_rating", 0]},
                        "feedback_count": {"$ifNull": ["$feedback_count", 0]},
                        "positive_feedback_count": {"$ifNull": ["$positive_feedback_count", 0]},
                        "negative_feedback_count": {"$ifNull": ["$negative_feedback_count", 0]},
                        "tags": 1,
                        "trending_score": 1,
                        "recent_comments": {
                            "$slice": [
                                {
                                    "$map": {
                                        "input": {
                                            "$filter": {
                                                "input": {"$ifNull": ["$user_feedback", []]},
                                                "as": "fb",
                                                "cond": {"$ne": ["$$fb.comment", None]}
                                            }
                                        },
                                        "as": "fb",
                                        "in": "$$fb.comment"
                                    }
                                },
                                -3  # Last 3 comments
                            ]
                        },
                        "_id":0
                    }
                }
            ]
            
            trending_pois = await self.pois_collection.aggregate(pipeline).to_list(length=limit)
            
            logger.info(f"✅ Found {len(trending_pois)} trending POIs")
            
            return trending_pois
        
        except Exception as e:
            logger.error(f"❌ Error getting trending POIs: {e}")
            raise

    async def get_feedback_boost_scores(self, poi_ids: List[str]) -> Dict[str, float]:
        """
        Get feedback boost scores for a list of POIs
        
        Args:
            poi_ids: List of MongoDB POI IDs
            
        Returns:
            Dict mapping poi_id to boost score (0.8 to 1.5)
        """
        try:
            from bson import ObjectId
            
            # Convert string IDs to ObjectId
            object_ids = [ObjectId(poi_id) for poi_id in poi_ids]
            
            # Fetch POIs with feedback stats
            pois = await self.pois_collection.find(
                {"_id": {"$in": object_ids}},
                {"_id": 1, "average_rating": 1, "feedback_count": 1}
            ).to_list(length=len(poi_ids))
            
            boost_scores = {}
            
            for poi in pois:
                poi_id_str = str(poi["_id"])
                avg_rating = poi.get("average_rating", 0)
                feedback_count = poi.get("feedback_count", 0)
                
                # Calculate boost score
                if feedback_count == 0:
                    # No feedback = neutral (1.0)
                    boost_scores[poi_id_str] = 1.0
                elif avg_rating >= 4.5 and feedback_count >= 5:
                    # Highly rated with good sample size = strong boost
                    boost_scores[poi_id_str] = 1.5
                elif avg_rating >= 4.0 and feedback_count >= 3:
                    # Good rating = moderate boost
                    boost_scores[poi_id_str] = 1.3
                elif avg_rating >= 3.5:
                    # Average rating = slight boost
                    boost_scores[poi_id_str] = 1.1
                elif avg_rating >= 3.0:
                    # Below average = neutral
                    boost_scores[poi_id_str] = 1.0
                else:
                    # Poor rating = slight penalty
                    boost_scores[poi_id_str] = 0.8
            
            # Fill in 1.0 for any missing POIs
            for poi_id in poi_ids:
                if poi_id not in boost_scores:
                    boost_scores[poi_id] = 1.0
            
            return boost_scores
        
        except Exception as e:
            logger.error(f"❌ Error getting feedback boost scores: {e}")
            # Return neutral scores on error
            return {poi_id: 1.0 for poi_id in poi_ids}
# Singleton instance
feedback_service = FeedbackService()
