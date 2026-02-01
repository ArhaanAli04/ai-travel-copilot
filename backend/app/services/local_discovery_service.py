"""
Local Discovery Service - Hybrid search combining MongoDB geo-queries and Qdrant semantic search

Combines:
1. MongoDB geospatial queries (POIs within radius)
2. Qdrant semantic search (relevant blog posts/tips)
3. Scoring and ranking
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, time
import logging

from app.core.mongo import get_database,connect_to_mongo
from app.services.qdrant_service import qdrant_service
from app.services.embedding_service import embedding_service
from app.utils.geo_utils import calculate_distance, get_city_coordinates
from qdrant_client.models import Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)


class LocalDiscoveryService:
    """Service for local discovery with hybrid search"""
    
    def __init__(self):
        self.collection_name = "local_discovery"
        logger.info("✅ LocalDiscoveryService initialized")
    
    async def hybrid_search(
        self,
        query: str,
        user_location: Dict[str, float],
        city: str,
        radius_km: float = 5.0,
        categories: Optional[List[str]] = None,
        cuisines: Optional[List[str]] = None,
        limit: int = 20,
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Hybrid search combining MongoDB geo-query and Qdrant semantic search
        
        Args:
            query: User search query (e.g., "vegetarian restaurants")
            user_location: Dict with 'lat' and 'lon' keys
            city: City name for filtering
            radius_km: Search radius in kilometers (default: 5km)
            categories: Optional list of categories to filter
            cuisines: Optional list of cuisines to filter
            limit: Maximum number of results
            include_context: Whether to include blog/tip context
        
        Returns:
            Dictionary with POIs, context, and metadata
        """
        logger.info(f"🔍 Hybrid search: '{query}' near ({user_location['lat']}, {user_location['lon']})")
        
        # Step 1: MongoDB Geospatial Query
        pois = await self._geo_query_pois(
            user_location=user_location,
            city=city,
            radius_km=radius_km,
            categories=categories,
            cuisines=cuisines,
            limit=limit
        )
        
        logger.info(f"   📍 Found {len(pois)} POIs within {radius_km}km radius")
        
        # Step 2: Qdrant Semantic Search (for context)
        context_results = []
        if include_context and query:
            context_results = await self._semantic_search_context(
                query=query,
                city=city,
                limit=10
            )
            logger.info(f"   🔎 Found {len(context_results)} semantic matches")
        
        # Step 3: Score and rank POIs based on query relevance
        if query:
            pois = await self._score_pois_by_query(query, pois)
        
        # Step 3.5: Apply feedback boost to scores (NEW - Day 22)
        pois = await self._apply_feedback_boost(pois)

        # Step 4: Add distance to each POI
        for poi in pois:
            if "location" in poi and "coordinates" in poi["location"]:
                poi_lat, poi_lon = poi["location"]["coordinates"][1], poi["location"]["coordinates"][0]
                distance = calculate_distance(
                    user_location["lat"],
                    user_location["lon"],
                    poi_lat,
                    poi_lon
                )
                poi["distance_km"] = round(distance, 2)
                poi["distance_text"] = self._format_distance(distance)
        
        # Step 5: Merge and return results
        return {
            "query": query,
            "location": user_location,
            "city": city,
            "radius_km": radius_km,
            "total_pois": len(pois),
            "pois": pois[:limit],
            "context": context_results,
            "filters_applied": {
                "categories": categories,
                "cuisines": cuisines,
            }
        }
    
    async def _geo_query_pois(
        self,
        user_location: Dict[str, float],
        city: str,
        radius_km: float,
        categories: Optional[List[str]] = None,
        cuisines: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Query MongoDB for POIs within radius using geospatial index
        
        Args:
            user_location: User's current location
            city: City filter
            radius_km: Search radius in kilometers
            categories: Optional category filters
            cuisines: Optional cuisine filters
            limit: Maximum results
        
        Returns:
            List of POI documents
        """
        db = get_database()
        if db is None:
            logger.error("❌ Database not connected!")
            await connect_to_mongo()
            db = get_database()
        # Build MongoDB query
        query = {
            "city": city.lower(),
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [user_location["lon"], user_location["lat"]]
                    },
                    "$maxDistance": radius_km * 1000  # Convert km to meters
                }
            }
        }
        
        # Add category filter
        if categories:
            categories_lower = [cat.lower() for cat in categories]
            query["category"] = {"$in": categories_lower}
        
        # Add cuisine filter
        if cuisines:
            # Build $or conditions for flexible matching
            cuisine_patterns = []
            for cuisine in cuisines:
                cuisine_patterns.append({
                    "tags.cuisine": {
                        "$regex": f"^{cuisine}$",
                        "$options": "i"  # case-insensitive
                    }
                })
            
            # Add to query
            if cuisine_patterns:
                if "$or" in query:
                    # Merge with existing $or
                    query["$and"] = [
                        {"$or": query.pop("$or")},
                        {"$or": cuisine_patterns}
                    ]
                else:
                    query["$or"] = cuisine_patterns
        
        # Execute query
        cursor = db.pois.find(query).limit(limit)
        pois = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for poi in pois:
            if "_id" in poi:
                poi["_id"] = str(poi["_id"])
        
        return pois
    
    async def _semantic_search_context(
        self,
        query: str,
        city: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Semantic search in Qdrant for relevant blog posts and tips
        
        Args:
            query: User query
            city: City filter
            limit: Maximum results
        
        Returns:
            List of context items (blog posts, tips)
        """
        # Generate query embedding
        query_embedding = embedding_service.generate_embeddings(
            [query],
            task_type="RETRIEVAL_QUERY"
        )[0]
        
        # Create Qdrant filter for city
        city_filter = Filter(
            must=[
                FieldCondition(
                    key="city",
                    match=MatchValue(value=city.lower())
                )
            ]
        )
        
        # Search Qdrant
        results = qdrant_service.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            query_filter=city_filter
        )
        
        return results
    
    async def _score_pois_by_query(
        self,
        query: str,
        pois: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Score POIs by relevance to query using semantic similarity
        
        Args:
            query: User query
            pois: List of POIs from geo-query
        
        Returns:
            POIs sorted by relevance score
        """
        if not pois:
            return pois
        
        # Generate query embedding
        query_embedding = embedding_service.generate_embeddings(
            [query],
            task_type="RETRIEVAL_QUERY"
        )[0]
        
        # Generate embeddings for POI descriptions
        poi_texts = []
        for poi in pois:
            # Combine name, category, and tags into searchable text
            text_parts = [poi.get("name", "")]
            
            if poi.get("category"):
                text_parts.append(poi["category"])
            
            if poi.get("tags", {}).get("cuisine"):
                text_parts.append(poi["tags"]["cuisine"])
            
            if poi.get("tags", {}).get("amenity"):
                text_parts.append(poi["tags"]["amenity"])
            
            poi_texts.append(" ".join(text_parts))
        
        # Generate embeddings
        poi_embeddings = embedding_service.generate_embeddings(
            poi_texts,
            task_type="RETRIEVAL_DOCUMENT"
        )
        
        # Calculate cosine similarity scores
        import numpy as np
        
        query_vec = np.array(query_embedding)
        
        for i, poi in enumerate(pois):
            poi_vec = np.array(poi_embeddings[i])
            
            # Cosine similarity
            similarity = np.dot(query_vec, poi_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(poi_vec)
            )
            
            poi["relevance_score"] = float(similarity)
        
        # Sort by relevance score (descending)
        pois.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return pois
    
    async def _apply_feedback_boost(self, pois: List[Dict]) -> List[Dict]:
        """
        Apply feedback-based boost to POI relevance scores
        
        Args:
            pois: List of POIs with relevance_score
            
        Returns:
            POIs with boosted scores
        """
        try:
            from app.services.feedback_service import feedback_service
            
            if not pois:
                return pois
            
            # Extract POI IDs
            poi_ids = [str(poi["_id"]) for poi in pois]
            
            # Get boost scores
            boost_scores = await feedback_service.get_feedback_boost_scores(poi_ids)
            
            # Apply boost to relevance scores
            for poi in pois:
                poi_id_str = str(poi["_id"])
                boost = boost_scores.get(poi_id_str, 1.0)
                
                # Apply boost to existing score
                if "relevance_score" in poi:
                    original_score = poi["relevance_score"]
                    poi["relevance_score"] = original_score * boost
                    poi["feedback_boost"] = boost  # Store boost for debugging
                else:
                    # If no relevance score, use boost as base score
                    poi["relevance_score"] = boost
                    poi["feedback_boost"] = boost
            
            # Re-sort by boosted scores
            pois.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            
            logger.info(f"   ⭐ Applied feedback boost to {len(pois)} POIs")
            
            return pois
        
        except Exception as e:
            logger.error(f"❌ Error applying feedback boost: {e}")
            return pois  # Return unchanged on error

    def _format_distance(self, distance_km: float) -> str:
        """Format distance in human-readable format"""
        if distance_km < 1:
            meters = int(distance_km * 1000)
            return f"{meters} m"
        else:
            return f"{distance_km:.1f} km"
    
    async def get_poi_by_id(self, poi_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single POI by ID
        
        Args:
            poi_id: POI ID
        
        Returns:
            POI document or None
        """
        from bson import ObjectId
        
        db = get_database()
        
        try:
            poi = await db.pois.find_one({"_id": ObjectId(poi_id)})
            
            if poi:
                poi["_id"] = str(poi["_id"])
            
            return poi
        except Exception as e:
            logger.error(f"Error fetching POI {poi_id}: {e}")
            return None
    
    async def search_by_category(
        self,
        city: str,
        category: str,
        user_location: Optional[Dict[str, float]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search POIs by category
        
        Args:
            city: City name
            category: Category to search
            user_location: Optional user location for distance sorting
            limit: Maximum results
        
        Returns:
            List of POIs
        """
        db = get_database()
        
        query = {
            "city": city.lower(),
            "category": category
        }
        
        # If user location provided, sort by distance
        if user_location:
            query["location"] = {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [user_location["lon"], user_location["lat"]]
                    }
                }
            }
        
        cursor = db.pois.find(query).limit(limit)
        pois = await cursor.to_list(length=limit)
        
        # Convert ObjectId
        for poi in pois:
            if "_id" in poi:
                poi["_id"] = str(poi["_id"])
            
            # Add distance if location provided
            if user_location and "location" in poi and "coordinates" in poi["location"]:
                poi_lat, poi_lon = poi["location"]["coordinates"][1], poi["location"]["coordinates"][0]
                distance = calculate_distance(
                    user_location["lat"],
                    user_location["lon"],
                    poi_lat,
                    poi_lon
                )
                poi["distance_km"] = round(distance, 2)
                poi["distance_text"] = self._format_distance(distance)
        
        return pois
    
    async def get_categories_by_city(self, city: str) -> List[str]:
        """
        Get all available categories for a city
        
        Args:
            city: City name
        
        Returns:
            List of unique categories
        """
        db =get_database()
        
        categories = await db.pois.distinct("category", {"city": city.lower()})
        
        return sorted(categories)
    
    async def get_cuisines_by_city(self, city: str) -> List[str]:
        """
        Get all available cuisines for a city
        
        Args:
            city: City name
        
        Returns:
            List of unique cuisines
        """
        db = get_database()
        
        cuisines = await db.pois.distinct("tags.cuisine", {"city": city.lower()})
        
        # Filter out None values
        cuisines = [c for c in cuisines if c]
        
        return sorted(cuisines)


# Singleton instance
local_discovery_service = LocalDiscoveryService()
