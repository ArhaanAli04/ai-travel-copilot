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
        # Food & Drink
        "restaurant":   "13065",
        "cafe":         "13035",
        "coffee":       "13035",
        "fast_food":    "13145",
        "bar":          "13003",
        "pub":          "13003",
        "bakery":       "13040",
        "pizza":        "13064",
        "ice_cream":    "13049",
        "food_court":   "13145",
        "street_food":  "13145",
        # Attractions
        "attraction":   "16000",
        "museum":       "10027",
        "monument":     "16020",
        "park":         "16032",
        "aquarium":     "16055",
        "zoo":          "16056",
        "temple":       "12090",
        "mosque":       "12090",
        "church":       "12090",
        # Shopping
        "mall":         "17069",
        "shopping_mall":"17069",
        "supermarket":  "17069",
        "pharmacy":     "15014",
        # Services
        "hospital":     "15014",
        "hotel":        "19014",
        "gym":          "18008",
        "cinema":       "10024",
        "theater":      "10024",
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
        
    def get_place_photos(self, fsq_place_id: str, limit: int = 8) -> list:
        """
        Fetch photos for a Foursquare place using the dedicated photos endpoint.
        Returns list of photo dicts with url, thumbnail_url, width, height.
        """
        url = f"{self.BASE_URL}/places/{fsq_place_id}/photos"

        params = {
            "limit": limit,
            "classifications": "outdoor,indoor"
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
            photos_data = response.json()

            photo_urls = []
            for photo in photos_data:
                if "prefix" in photo and "suffix" in photo:
                    photo_urls.append({
                        "url":           f"{photo['prefix']}original{photo['suffix']}",
                        "thumbnail_url": f"{photo['prefix']}300x200{photo['suffix']}",
                        "width":         photo.get("width", 0),
                        "height":        photo.get("height", 0),
                        "source":        "foursquare",
                        "attribution":   "Photo from Foursquare",
                        "alt_text":      "Foursquare venue photo"
                    })

            logger.info(f"  📸 Foursquare photos: {len(photo_urls)} for {fsq_place_id}")
            return photo_urls

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"⚠️ Rate limit on photos for {fsq_place_id}, waiting 2s...")
                time.sleep(2)
            else:
                logger.warning(f"⚠️ Photo fetch failed for {fsq_place_id}: {e}")
            return []

        except Exception as e:
            logger.error(f"❌ Unexpected photo error for {fsq_place_id}: {e}")
            return []

    def _normalize_name(self, name: str) -> str:
        """
        Normalize place name for better fuzzy matching.
        Handles apostrophes, accents, branch suffixes, common abbreviations.
        """
        import re
        import unicodedata

        # Lowercase
        name = name.lower().strip()

        # Normalize unicode (é → e, ü → u, etc.)
        name = unicodedata.normalize("NFKD", name)
        name = "".join(c for c in name if not unicodedata.combining(c))

        # Remove apostrophes and special chars
        name = re.sub(r"[''`]", "", name)

        # Remove branch identifiers: "- Andheri", "(Bandra)", "– Fort"
        name = re.sub(r"[-–—]\s*[a-z\s]+$", "", name)
        name = re.sub(r"\([^)]+\)", "", name)

        # Normalize common abbreviations
        abbreviations = {
            "mcdonalds":   "mcdonald",
            "dominos":     "domino",
            "kfc":         "kfc",
            "ccd":         "cafe coffee day",
            "bk":          "burger king",
            "wh smith":    "wh smith",
            "dr ":         "doctor ",
            "st ":         "saint ",
        }
        for abbr, full in abbreviations.items():
            name = name.replace(abbr, full)

        # Collapse extra whitespace
        name = re.sub(r"\s+", " ", name).strip()

        return name


    def match_poi_to_foursquare(
        self,
        poi: POI,
        max_distance: int = 250
    ) -> Optional[Dict]:
        """
        Match an OSM POI to a Foursquare place
        
        Args:
            poi: POI object from MongoDB
            max_distance: Maximum distance in meters for matching
        
        Returns:
            Best matching Foursquare place dict or None
        """
        fsq_category = self.CATEGORY_MAPPING.get(poi.category)
        poi_name_norm = self._normalize_name(poi.name)

        # ── Pass 1: 150m radius ──────────────────────────────────────
        places = self.search_places(
            latitude=poi.location.coordinates[1],
            longitude=poi.location.coordinates[0],
            query=poi.name,
            categories=fsq_category,
            radius=max_distance,
            limit=10                  # ← increased from 5 to 10
        )

        # ── Pass 2: 300m radius if pass 1 returns nothing ───────────
        if not places:
            logger.info(f"  Pass 1 empty → widening to 300m for '{poi.name}'")
            places = self.search_places(
                latitude=poi.location.coordinates[1],
                longitude=poi.location.coordinates[0],
                query=poi.name,
                categories=None,      # ← drop category filter in wide search
                radius=300,
                limit=10
            )

        if not places:
            return None

        best_match = None
        best_score = 0.0

        for place in places:
            place_name      = place.get("name", "")
            place_name_norm = self._normalize_name(place_name)

            # ── Name similarity (normalized) ─────────────────────────
            from difflib import SequenceMatcher
            similarity = SequenceMatcher(
                None, poi_name_norm, place_name_norm
            ).ratio()

            # ── Bonus: one name contains the other ───────────────────
            contains_bonus = 0.0
            if poi_name_norm in place_name_norm or place_name_norm in poi_name_norm:
                contains_bonus = 0.15

            # ── Distance score ───────────────────────────────────────
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

            distance_score = max(0.0, 1.0 - (distance / 300))

            # ── Combined score ───────────────────────────────────────
            combined_score = (
                0.65 * (similarity + contains_bonus) +
                0.35 * distance_score
            )

            logger.debug(
                f"  '{place_name}' → sim={similarity:.2f} "
                f"dist={distance:.0f}m score={combined_score:.2f}"
            )

            # ── Threshold: lowered from 0.6 → 0.45 ──────────────────
            if combined_score > best_score and combined_score > 0.45:
                best_score = combined_score
                best_match = {
                    **place,
                    "match_confidence":  combined_score,
                    "distance_meters":   distance
                }

        if best_match:
            logger.info(
                f"  ✅ Matched '{poi.name}' → '{best_match.get('name')}' "
                f"(confidence: {best_match['match_confidence']:.2f}, "
                f"dist: {best_match['distance_meters']:.0f}m)"
            )
        else:
            logger.info(f"  ❌ No match found for '{poi.name}'")

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
        logger.info(f"  🔑 fsq_place_id raw: '{fsq_place_id}' (len={len(fsq_place_id) if fsq_place_id else 0})")
        logger.info(f"✅ Matched to Foursquare: {fsq_place.get('name')} (confidence: {fsq_place['match_confidence']:.2f})")
        
        # Get detailed place info with tips
        place_details = self.get_place_details(fsq_place_id)
        time.sleep(0.5)  # Rate limiting
        if not place_details:
            logger.warning(f"Could not fetch details for {fsq_place_id}")
            return None
        
        # ✅ NEW: Extract data from new API response structure
        tips_data = place_details.get("tips", [])
        rating     = place_details.get("rating")
        popularity = place_details.get("popularity")

        # Format tips
        formatted_tips = []
        for tip in tips_data[:5]:  # Limit to 5 tips
            formatted_tips.append({
                "text": tip.get("text", ""),
                "created_at": tip.get("created_at", ""),
                "agree_count": tip.get("agree_count", 0)
            })
        
        # Fetch photos from dedicated endpoint
        photo_urls = []
        try:
            logger.info(f"  🔑 Calling get_place_photos with: '{fsq_place_id}' (len={len(fsq_place_id) if fsq_place_id else 0})")
            photos_raw = self.get_place_photos(fsq_place_id, limit=8)
            photo_urls = [p["url"] for p in photos_raw]
            logger.info(f"  📸 Fetched {len(photo_urls)} photos for {fsq_place_id}")
        except Exception as e:
            logger.warning(f"  ⚠️ Could not fetch photos for {fsq_place_id}: {e}")
            photo_urls = []
        
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
