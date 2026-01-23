"""
OSM Service for fetching POIs from OpenStreetMap via Overpass API
"""
import requests
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from app.models.poi import POI, GeoJSONPoint
from app.core.mongo import get_database
from app.services.embedding_service import embedding_service
import logging


logger = logging.getLogger(__name__)


class OSMService:
    """Service for fetching POIs from OpenStreetMap via Overpass API"""
    
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    
    # City bounding boxes: [min_lat, min_lon, max_lat, max_lon]
    CITY_BBOXES = {
        "mumbai": [18.8900, 72.7760, 19.2700, 73.0360],
        "goa": [15.2000, 73.7000, 15.6000, 74.0000],
        "delhi": [28.4000, 76.8400, 28.8800, 77.3500],
    }
    
    # POI categories to fetch from OSM
    POI_QUERIES = {
        "restaurant": '[amenity=restaurant]',
        "cafe": '[amenity=cafe]',
        "bar": '[amenity=bar]',
        "fast_food": '[amenity=fast_food]',
        "attraction": '[tourism~"attraction|museum|gallery|viewpoint"]',
        "park": '[leisure=park]',
        "garden": '[leisure=garden]',
        "monument": '[historic=monument]',
        "market": '[amenity=marketplace]',
    }
    
    def __init__(self):
        """Initialize OSM service (database connection done lazily)"""
        self._db = None
        self._pois_collection = None
    
    @property
    def db(self):
        """Lazy database connection"""
        if self._db is None:
            self._db = get_database()
        return self._db
    
    @property
    def pois_collection(self):
        """Lazy collection access"""
        if self._pois_collection is None:
            self._pois_collection = self.db["pois"]
        return self._pois_collection
    
    def fetch_overpass_pois(
        self,
        city: str,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        categories: Optional[List[str]] = None
    ) -> List[POI]:
        """
        Fetch POIs from Overpass API for a given city
        
        Args:
            city: City name (lowercase)
            bbox: Optional custom bounding box [min_lat, min_lon, max_lat, max_lon]
            categories: Optional list of categories to fetch (default: all)
        
        Returns:
            List of POI objects
        """
        # Get bounding box
        if bbox is None:
            if city.lower() not in self.CITY_BBOXES:
                raise ValueError(f"City '{city}' not found. Available: {list(self.CITY_BBOXES.keys())}")
            bbox = self.CITY_BBOXES[city.lower()]
        
        # Determine categories to fetch
        if categories is None:
            categories = list(self.POI_QUERIES.keys())
        
        all_pois = []
        
        for category in categories:
            if category not in self.POI_QUERIES:
                logger.warning(f"Unknown category '{category}', skipping")
                continue
            
            logger.info(f"Fetching {category} POIs for {city}...")
            pois = self._query_overpass(city, bbox, category)
            all_pois.extend(pois)
            
            # Rate limiting: Overpass API fair use policy
            time.sleep(1)  # 1 second delay between queries
        
        logger.info(f"Total POIs fetched for {city}: {len(all_pois)}")
        return all_pois
    
    def _query_overpass(
        self,
        city: str,
        bbox: Tuple[float, float, float, float],
        category: str
    ) -> List[POI]:
        """Query Overpass API for a specific category"""
        query_filter = self.POI_QUERIES[category]
        
        # Overpass QL query
        overpass_query = f"""
        [out:json][timeout:60];
        (
          node{query_filter}({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          way{query_filter}({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        );
        out center tags;
        """
        
        try:
            response = requests.post(
                self.OVERPASS_URL,
                data={"data": overpass_query},
                timeout=90
            )
            response.raise_for_status()
            data = response.json()
            
            pois = []
            for element in data.get("elements", []):
                poi = self._parse_osm_element(element, city, category)
                if poi:
                    pois.append(poi)
            
            return pois
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying Overpass API: {e}")
            return []
    
    def _parse_osm_element(
        self,
        element: Dict,
        city: str,
        category: str
    ) -> Optional[POI]:
        """Parse OSM element into POI object"""
        tags = element.get("tags", {})
        
        # Extract name (required)
        name = tags.get("name") or tags.get("name:en")
        if not name:
            return None  # Skip POIs without names
        
        # Extract coordinates
        if element["type"] == "node":
            lat, lon = element["lat"], element["lon"]
        elif "center" in element:
            lat, lon = element["center"]["lat"], element["center"]["lon"]
        else:
            return None  # Skip if no coordinates
        
        # Generate description for embedding
        description = self._generate_poi_description(name, tags, city, category)
        
        # Create POI object
        poi = POI(
            name=name,
            location=GeoJSONPoint(coordinates=[lon, lat]),
            category=category,
            tags=tags,
            osm_id=str(element["id"]),
            osm_type=element["type"],
            hours=tags.get("opening_hours"),
            city=city.lower(),
            address=self._format_address(tags),
            phone=tags.get("phone"),
            website=tags.get("website"),
            description=description,
            source="osm"
        )
        
        return poi
    
    def _generate_poi_description(
        self,
        name: str,
        tags: Dict[str, str],
        city: str,
        category: str
    ) -> str:
        """Generate natural language description from OSM tags"""
        parts = [name]
        
        # Add cuisine/type info
        if "cuisine" in tags:
            parts.append(f"{tags['cuisine'].replace('_', ' ')} {category}")
        else:
            parts.append(category)
        
        # Add dietary info
        dietary = []
        if tags.get("diet:vegetarian") == "yes":
            dietary.append("vegetarian-friendly")
        if tags.get("diet:vegan") == "yes":
            dietary.append("vegan options")
        if tags.get("diet:halal") == "yes":
            dietary.append("halal")
        
        if dietary:
            parts.append(f"with {', '.join(dietary)}")
        
        # Add location context
        if "addr:suburb" in tags:
            parts.append(f"in {tags['addr:suburb']}, {city.title()}")
        else:
            parts.append(f"in {city.title()}")
        
        # Add special features
        if tags.get("outdoor_seating") == "yes":
            parts.append("Features outdoor seating")
        if tags.get("takeaway") == "yes":
            parts.append("Offers takeaway")
        
        return ". ".join(parts) + "."
    
    def _format_address(self, tags: Dict[str, str]) -> Optional[str]:
        """Format address from OSM tags"""
        addr_parts = []
        
        if "addr:housenumber" in tags:
            addr_parts.append(tags["addr:housenumber"])
        if "addr:street" in tags:
            addr_parts.append(tags["addr:street"])
        if "addr:suburb" in tags:
            addr_parts.append(tags["addr:suburb"])
        if "addr:postcode" in tags:
            addr_parts.append(tags["addr:postcode"])
        
        return ", ".join(addr_parts) if addr_parts else None
    
    async def store_pois(self, pois: List[POI]) -> int:
        """
        Store POIs in MongoDB (async upsert based on osm_id)
        
        Args:
            pois: List of POI objects
        
        Returns:
            Number of POIs inserted/updated
        """
        if not pois:
            return 0
        
        count = 0
        for poi in pois:
            # Upsert based on osm_id to avoid duplicates
            result = await self.pois_collection.update_one(
                {"osm_id": poi.osm_id},
                {"$set": poi.model_dump(by_alias=True, exclude={"id"})},
                upsert=True
            )
            if result.upserted_id or result.modified_count > 0:
                count += 1
        
        logger.info(f"Stored {count} POIs in MongoDB")
        return count
    
    async def get_poi_by_id(self, poi_id: str) -> Optional[POI]:
        """Fetch POI by MongoDB _id"""
        from bson import ObjectId
        doc = await self.pois_collection.find_one({"_id": ObjectId(poi_id)})
        return POI(**doc) if doc else None
    
    async def get_pois_by_city(self, city: str, limit: int = 100) -> List[POI]:
        """Fetch POIs for a city"""
        cursor = self.pois_collection.find({"city": city.lower()}).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [POI(**doc) for doc in docs]


# Singleton instance (lazy initialization)
osm_service = OSMService()
