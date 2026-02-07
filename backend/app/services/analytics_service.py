"""
Service for analytics tracking and reporting
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta,timezone
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import certifi

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for tracking and analyzing user queries"""
    
    def __init__(self):
        self.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        self.db = self.client.get_database("travel_copilot")
        self.analytics_collection = self.db["analytics_queries"]
    
    async def log_query(
        self,
        query_text: str,
        city: str,
        user_location: Dict[str, float],
        preferences: Optional[Dict] = None,
        results_count: int = 0,
        response_time_ms: float = 0,
        user_id: Optional[str] = None
    ) -> str:
        """
        Log a user query for analytics
        
        Args:
            query_text: User's search query
            city: City searched
            user_location: User's coordinates
            preferences: User preferences
            results_count: Number of results returned
            response_time_ms: API response time
            user_id: Optional user ID
            
        Returns:
            Query ID
        """
        try:
            query_doc = {
                "query_text": query_text,
                "city": city,
                "user_location": user_location,
                "preferences": preferences or {},
                "results_count": results_count,
                "response_time_ms": response_time_ms,
                "user_id": user_id,
                "timestamp":datetime.now(timezone.utc),
                "hour_of_day": datetime.now(timezone.utc).hour,
                "day_of_week": datetime.now(timezone.utc).strftime("%A")
            }
            
            result = await self.analytics_collection.insert_one(query_doc)
            
            # Don't log every query to avoid spam
            if results_count > 0:
                logger.debug(f"📊 Logged query: '{query_text}' ({results_count} results)")
            
            return str(result.inserted_id)
        
        except Exception as e:
            # Don't fail the main request if analytics fails
            logger.error(f"❌ Error logging analytics: {e}")
            return ""
    
    async def get_popular_cities(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most searched cities in the last N days
        
        Returns:
            List of cities with search counts
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            pipeline = [
                {"$match": {"timestamp": {"$gte": cutoff_date}}},
                {"$group": {
                    "_id": "$city",
                    "search_count": {"$sum": 1},
                    "avg_results": {"$avg": "$results_count"},
                    "avg_response_time": {"$avg": "$response_time_ms"}
                }},
                {"$sort": {"search_count": -1}},
                {"$limit": limit},
                {"$project": {
                    "city": "$_id",
                    "search_count": 1,
                    "avg_results": {"$round": ["$avg_results", 1]},
                    "avg_response_time": {"$round": ["$avg_response_time", 1]},
                    "_id": 0
                }}
            ]
            
            results = await self.analytics_collection.aggregate(pipeline).to_list(length=limit)
            return results
        
        except Exception as e:
            logger.error(f"❌ Error getting popular cities: {e}")
            return []
    
    async def get_popular_times(self, city: Optional[str] = None, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get popular search times (hours of day)
        
        Args:
            city: Optional city filter
            days: Look back period
            
        Returns:
            List of hours with search counts
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            match_query = {"timestamp": {"$gte": cutoff_date}}
            if city:
                match_query["city"] = city
            
            pipeline = [
                {"$match": match_query},
                {"$group": {
                    "_id": "$hour_of_day",
                    "search_count": {"$sum": 1}
                }},
                {"$sort": {"_id": 1}},
                {"$project": {
                    "hour": "$_id",
                    "search_count": 1,
                    "_id": 0
                }}
            ]
            
            results = await self.analytics_collection.aggregate(pipeline).to_list(length=24)
            return results
        
        except Exception as e:
            logger.error(f"❌ Error getting popular times: {e}")
            return []
    
    async def get_common_preferences(self, city: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
        """
        Get most common user preferences
        
        Returns:
            Dict with top categories, cuisines, dietary preferences
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            match_query = {"timestamp": {"$gte": cutoff_date}}
            if city:
                match_query["city"] = city
            
            # Get all queries with preferences
            queries = await self.analytics_collection.find(
                match_query,
                {"preferences": 1}
            ).to_list(length=10000)
            
            # Count occurrences
            categories = {}
            cuisines = {}
            dietary = {}
            budgets = {}
            
            for query in queries:
                prefs = query.get("preferences", {})
                
                # Categories
                for cat in prefs.get("categories", []):
                    categories[cat] = categories.get(cat, 0) + 1
                
                # Cuisines
                for cuisine in prefs.get("cuisines", []):
                    cuisines[cuisine] = cuisines.get(cuisine, 0) + 1
                
                # Dietary
                for diet in prefs.get("dietary", []):
                    dietary[diet] = dietary.get(diet, 0) + 1
                
                # Budget
                budget = prefs.get("budget")
                if budget:
                    budgets[budget] = budgets.get(budget, 0) + 1
            
            # Sort and limit
            def top_items(items_dict, limit=5):
                return sorted(
                    [{"name": k, "count": v} for k, v in items_dict.items()],
                    key=lambda x: x["count"],
                    reverse=True
                )[:limit]
            
            return {
                "categories": top_items(categories),
                "cuisines": top_items(cuisines),
                "dietary": top_items(dietary),
                "budgets": top_items(budgets)
            }
        
        except Exception as e:
            logger.error(f"❌ Error getting common preferences: {e}")
            return {}
    
    async def get_analytics_summary(self, city: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
        """
        Get comprehensive analytics summary
        
        Returns:
            Dict with all analytics data
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            match_query = {"timestamp": {"$gte": cutoff_date}}
            if city:
                match_query["city"] = city
            
            # Total queries
            total_queries = await self.analytics_collection.count_documents(match_query)
            
            # Average response time
            pipeline = [
                {"$match": match_query},
                {"$group": {
                    "_id": None,
                    "avg_response_time": {"$avg": "$response_time_ms"},
                    "avg_results": {"$avg": "$results_count"}
                }}
            ]
            
            stats = await self.analytics_collection.aggregate(pipeline).to_list(length=1)
            avg_response_time = stats[0]["avg_response_time"] if stats else 0
            avg_results = stats[0]["avg_results"] if stats else 0
            
            # Get other metrics
            popular_cities = await self.get_popular_cities(days=days)
            popular_times = await self.get_popular_times(city=city, days=days)
            common_preferences = await self.get_common_preferences(city=city, days=days)
            
            return {
                "time_range_days": days,
                "city_filter": city,
                "total_queries": total_queries,
                "avg_response_time_ms": round(avg_response_time, 2),
                "avg_results_count": round(avg_results, 1),
                "popular_cities": popular_cities,
                "popular_times": popular_times,
                "common_preferences": common_preferences
            }
        
        except Exception as e:
            logger.error(f"❌ Error getting analytics summary: {e}")
            return {}


# Singleton instance
analytics_service = AnalyticsService()
