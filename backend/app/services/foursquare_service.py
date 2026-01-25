"""
Foursquare Places API service for enriching POIs with user tips and reviews
Uses NEW Places API (2025 version)
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime
from ratelimit import limits, sleep_and_retry
from difflib import SequenceMatcher
import time
import logging

from app.core.config import settings
from app.core.mongo import get_database
from app.models.poi import POI, FoursquareTip


logger = logging.getLogger(__name__)


class FoursquareService:
    """Service for enriching OSM POIs with Foursquare data"""
    
    # ✅ NEW: Updated base URL for Places API
    BASE_URL = "https://places-api.foursquare.com"
    API_VERSION = "2025-06-17"
    
    # Foursquare rate limit: 950 requests per 15 minutes
    RATE_LIMIT_CALLS = 950
    RATE_LIMIT_PERIOD = 900  # 15 minutes in seconds
    
    # OSM to Foursquare category mapping (IDs remain same)
    CATEGORY_MAPPING = {
        "restaurant": "13065",
        "cafe": "13035",
        "bar": "13003",
        "fast_food": "13145",
        "attraction": "16000",
        "park": "16032",
        "museum": "10027",
        "monument": "16020",
    }
    
    def __init__(self):
        """Initialize Foursquare API client"""
        if not settings.FOURSQUARE_API_KEY:
            raise RuntimeError("FOURSQUARE_API_KEY not set in environment")
        
        self.api_key = settings.FOURSQUARE_API_KEY
        
        # ✅ NEW: Updated headers for Places API
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",  # Changed from X-Places-Api-Key
            "X-Places-Api-Version": self.API_VERSION
        }
        
        # Lazy load database
        self._db = None
        self._pois_collection = None
        self._tips_collection = None
        
        logger.info("✅ FoursquareService initialized (Places API 2025)")
    
    @property
    def db(self):
        """Lazy load database connection"""
        if self._db is None:
            self._db = get_database()
        return self._db
    
    @property
    def pois_collection(self):
        """Lazy load pois collection"""
        if self._pois_collection is None:
            self._pois_collection = self.db["pois"]
        return self._pois_collection
    
    @property
    def tips_collection(self):
        """Lazy load tips collection"""
        if self._tips_collection is None:
            self._tips_collection = self.db["foursquare_tips"]
        return self._tips_collection
    
    @sleep_and_retry
    @limits(calls=RATE_LIMIT_CALLS, period=RATE_LIMIT_PERIOD)
    def _rate_limited_request(self, method: str, url: str, **kwargs):
        """Rate-limited HTTP request wrapper"""
        return requests.request(method, url, **kwargs)
    
    def search_places(
        self,
        latitude: float,
        longitude: float,
        query: Optional[str] = None,
        categories: Optional[str] = None,
        radius: int = 50,
        limit: int = 5
    ) -> List[Dict]:
        """
        Search for Foursquare places near coordinates
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            query: Optional search query (place name)
            categories: Foursquare category IDs (comma-separated)
            radius: Search radius in meters (default: 50m)
            limit: Max results (default: 5)
        
        Returns:
            List of place dictionaries
        """
        # ✅ NEW: Updated endpoint path
        url = f"{self.BASE_URL}/places/search"
        
        params = {
            "ll": f"{latitude},{longitude}",
            "radius": radius,
            "limit": limit
        }
        
        if query:
            params["query"] = query
        
        if categories:
            params["categories"] = categories
        
        try:
            response = self._rate_limited_request(
                "GET",
                url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("results", [])
        
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Foursquare API error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response text: {e.response.text}")
            return []
    
    def get_place_details(self, fsq_place_id: str) -> Optional[Dict]:
        """
        Get detailed information for a place (including tips)
        
        Args:
            fsq_place_id: Foursquare place ID
        
        Returns:
            Place details dictionary with tips embedded
        """
        # ✅ NEW: Get place details (tips are included in the response)
        url = f"{self.BASE_URL}/places/{fsq_place_id}"
        
        params = {
            "fields": "fsq_place_id,name,rating,popularity,photos,tips,stats"
        }
        
        try:
            response = self._rate_limited_request(
                "GET",
                url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"⚠️ Rate limit hit for {fsq_place_id}, waiting 2 seconds...")
                time.sleep(2)  # Wait before retry
                
                # Retry once
                try:
                    response = self._rate_limited_request(
                        "GET",
                        url,
                        headers=self.headers,
                        timeout=10
                    )
                    response.raise_for_status()
                    return response.json()
                except:
                    logger.error(f"❌ Still rate limited for {fsq_place_id}")
                    return None
            else:
                logger.error(f"❌ Error fetching details for {fsq_place_id}: {e}")
                return None
        
        except Exception as e:
            logger.error(f"❌ Unexpected error for {fsq_place_id}: {e}")
            return None
        
    
    def match_poi_to_foursquare(
        self,
        poi: POI,
        max_distance: int = 50
    ) -> Optional[Dict]:
        """
        Match an OSM POI to a Foursquare place
        
        Args:
            poi: POI object from MongoDB
            max_distance: Maximum distance in meters for matching
        
        Returns:
            Best matching Foursquare place dict or None
        """
        # Get Foursquare category for POI
        fsq_category = self.CATEGORY_MAPPING.get(poi.category)
        
        # Search Foursquare
        places = self.search_places(
            latitude=poi.location.coordinates[1],  # lat
            longitude=poi.location.coordinates[0],  # lng
            query=poi.name,
            categories=fsq_category,
            radius=max_distance,
            limit=5
        )
        
        if not places:
            return None
        
        # Find best match by name similarity
        best_match = None
        best_score = 0.0
        
        for place in places:
            place_name = place.get("name", "")
            
            # Calculate name similarity (0-1)
            similarity = SequenceMatcher(None, poi.name.lower(), place_name.lower()).ratio()
            
            # ✅ NEW: Updated location field structure
            place_lat = place.get("latitude")
            place_lng = place.get("longitude")
            
            if place_lat is None or place_lng is None:
                continue
            
            distance = self._calculate_distance(
                poi.location.coordinates[1],
                poi.location.coordinates[0],
                place_lat,
                place_lng
            )
            
            # Combined score: 70% name similarity + 30% distance (inverse)
            distance_score = max(0, 1 - (distance / max_distance))
            combined_score = (0.7 * similarity) + (0.3 * distance_score)
            
            if combined_score > best_score and combined_score > 0.6:  # Minimum 60% match
                best_score = combined_score
                best_match = {
                    **place,
                    "match_confidence": combined_score,
                    "distance_meters": distance
                }
        
        return best_match
    
    def _calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate distance between two coordinates in meters (Haversine formula)"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # Earth radius in meters
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    async def enrich_poi_with_tips(
        self,
        poi_id: str,
        latitude: float,
        longitude: float
    ) -> Optional[FoursquareTip]:
        """
        Enrich a POI with Foursquare tips
        
        Args:
            poi_id: MongoDB POI _id
            latitude: POI latitude
            longitude: POI longitude
        
        Returns:
            FoursquareTip object or None
        """
        from bson import ObjectId
        
        # Get POI from MongoDB
        poi_doc = await self.pois_collection.find_one({"_id": ObjectId(poi_id)})
        
        if not poi_doc:
            logger.warning(f"POI {poi_id} not found")
            return None
        
        poi = POI(**poi_doc)
        
        # Check if already enriched
        existing = await self.tips_collection.find_one({"poi_id": poi_id})
        if existing:
            logger.info(f"POI {poi.name} already enriched, skipping")
            return FoursquareTip(**existing)
        
        # Match to Foursquare
        logger.info(f"Matching POI: {poi.name} ({poi.category})")
        fsq_place = self.match_poi_to_foursquare(poi)
        
        if not fsq_place:
            logger.warning(f"No Foursquare match found for {poi.name}")
            return None
        
        # ✅ NEW: Updated field name
        fsq_place_id = fsq_place.get("fsq_place_id")
        logger.info(f"✅ Matched to Foursquare: {fsq_place.get('name')} (confidence: {fsq_place['match_confidence']:.2f})")
        
        # Get detailed place info with tips
        place_details = self.get_place_details(fsq_place_id)
        time.sleep(0.5)  # Rate limiting
        if not place_details:
            logger.warning(f"Could not fetch details for {fsq_place_id}")
            return None
        
        # ✅ NEW: Extract data from new API response structure
        tips_data = place_details.get("tips", [])
        photos_data = place_details.get("photos", [])
        rating = place_details.get("rating")
        popularity = place_details.get("popularity")
        
        # Format tips
        formatted_tips = []
        for tip in tips_data[:5]:  # Limit to 5 tips
            formatted_tips.append({
                "text": tip.get("text", ""),
                "created_at": tip.get("created_at", ""),
                "agree_count": tip.get("agree_count", 0)
            })
        
        # Format photos
        photo_urls = []
        for photo in photos_data[:3]:  # Limit to 3 photos
            if "prefix" in photo and "suffix" in photo:
                photo_url = f"{photo['prefix']}original{photo['suffix']}"
                photo_urls.append(photo_url)
        
        # Create FoursquareTip object
        tip_obj = FoursquareTip(
            poi_id=poi_id,
            fsq_place_id=fsq_place_id,
            fsq_name=fsq_place.get("name"),
            tips=formatted_tips,
            rating=rating,
            popularity=popularity,
            photos=photo_urls,
            city=poi.city,
            match_confidence=fsq_place["match_confidence"]
        )
        
        # Store in MongoDB
        await self.tips_collection.insert_one(
            tip_obj.dict(by_alias=True, exclude={"id"})
        )
        
        logger.info(f"✅ Enriched {poi.name} with {len(formatted_tips)} tips")
        
        return tip_obj
    
    def combine_poi_with_tips(self, poi: POI, tip_obj: FoursquareTip) -> str:
        """
        Combine OSM POI description with Foursquare tips into enriched text
        
        Args:
            poi: POI object
            tip_obj: FoursquareTip object
        
        Returns:
            Combined enriched description
        """
        parts = [poi.description or poi.name]
        
        # Add rating
        if tip_obj.rating:
            parts.append(f"Rated {tip_obj.rating}/10 on Foursquare.")
        
        # Add tips
        if tip_obj.tips:
            parts.append("\nWhat locals say:")
            for tip in tip_obj.tips[:5]:
                tip_text = tip.get("text", "").strip()
                agree_count = tip.get("agree_count", 0)
                if tip_text:
                    parts.append(f"- {tip_text} ({agree_count} agrees)")
        
        return " ".join(parts)


# Singleton instance
foursquare_service = FoursquareService()
