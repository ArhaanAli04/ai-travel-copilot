"""
Photo Service - Fetches real place photos from Wikimedia Commons + Unsplash fallback
"""
import httpx
import logging
import time
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# IN-MEMORY CACHE
# ============================================================================

_photo_cache: dict = {}  # { cache_key: { "photos": [...], "cached_at": timestamp, "source": "..." } }


# ============================================================================
# CATEGORY → UNSPLASH QUERY MAPPING
# ============================================================================

CATEGORY_QUERY_MAP = {
    # Food & Drink
    "restaurant":       "restaurant interior dining food",
    "cafe":             "cafe coffee shop interior",
    "coffee":           "coffee shop cozy interior",
    "bar":              "bar cocktails drinks interior",
    "pub":              "pub interior drinks",
    "bakery":           "bakery pastries fresh bread",
    "street_food":      "street food market vendor",
    "food_court":       "food court mall dining",
    "dessert":          "dessert sweets pastry shop",
    "ice_cream":        "ice cream shop colorful",
    "fast_food":        "fast food restaurant burger fries",
    "fast_food_restaurant": "fast food restaurant interior",
    "pizza":            "pizza restaurant italian food",
    "burger":           "burger restaurant fast food",
    "sandwich":         "sandwich deli cafe food",
    "chinese":          "chinese restaurant asian food interior",
    "indian":           "indian restaurant curry spices food",
    "italian":          "italian restaurant pasta pizza interior",
    "mexican":          "mexican restaurant tacos food",
    "japanese":         "japanese restaurant sushi ramen",
    "thai":             "thai restaurant asian cuisine food",
    "seafood":          "seafood restaurant fish ocean dining",
    "steak":            "steakhouse restaurant meat grill",
    "vegetarian":       "vegetarian restaurant healthy food",
    "vegan":            "vegan restaurant plant based food",
    "juice_bar":        "juice bar smoothie healthy drinks",
    "tea":              "tea shop chai indian tea",
    "food":             "restaurant food dining interior",
    "dining":           "restaurant dining elegant food",

    # Shopping
    "shopping_mall":    "shopping mall interior stores",
    "mall":             "shopping mall modern interior",
    "market":           "outdoor market bazaar colorful",
    "boutique":         "boutique fashion clothing store",
    "bookstore":        "bookstore shelves cozy",
    "supermarket":      "supermarket grocery store",
    "electronics":      "electronics store gadgets technology",
    "clothing":         "clothing store fashion retail",
    "jewelry":          "jewelry store luxury accessories",
    "pharmacy":         "pharmacy medicine store health",
    "grocery":          "grocery store supermarket fresh food",
    "convenience":      "convenience store retail shop",
    "department_store": "department store shopping retail",

    # Attractions
    "tourist_attraction": "famous tourist attraction landmark",
    "landmark":         "famous city landmark architecture",
    "museum":           "museum art gallery interior",
    "art_gallery":      "art gallery paintings exhibition",
    "temple":           "temple religious architecture",
    "mosque":           "mosque architecture islamic",
    "church":           "church architecture interior",
    "monument":         "monument historical architecture",
    "park":             "city park green nature",
    "garden":           "botanical garden flowers nature",
    "beach":            "tropical beach ocean waves",
    "viewpoint":        "scenic city viewpoint panorama",
    "aquarium":         "aquarium fish marine life underwater",   # ← ADD THIS LINE
    "zoo":              "zoo animals wildlife enclosure",

    # Entertainment
    "cinema":           "movie theater cinema interior",
    "theater":          "theater stage performance hall",
    "nightclub":        "nightclub music lights dance",
    "arcade":           "arcade games entertainment",
    "bowling":          "bowling alley lanes",
    "sports":           "sports facility stadium",
    "gym":              "gym fitness workout",

    # Wellness
    "spa":              "spa wellness relaxation",
    "salon":            "hair salon beauty",
    "beauty":           "beauty salon cosmetics spa",
    "laundry":          "laundry service clean",
    "repair":           "repair shop service center",

    # Accommodation
    "hotel":            "hotel lobby interior luxury",
    "hostel":           "hostel common room travel",

    # Transport & Services
    "hospital":         "hospital building medical",
    "pharmacy":         "pharmacy medicine store",
    "bank":             "bank finance building",

    # Default fallback
    "default":          "city local place travel"
}

WIKIMEDIA_SUITABLE_CATEGORIES = {
    "tourist_attraction", "landmark", "museum", "art_gallery",
    "temple", "mosque", "church", "monument", "park", "garden",
    "beach", "viewpoint", "historical", "heritage", "fort",
    "palace", "stadium", "university", "library", "zoo",
    "aquarium", "national_park", "waterfall", "mountain"
}
# ============================================================================
# MAIN FUNCTION
# ============================================================================

async def get_poi_photos(poi: dict) -> dict:
    """
    Main function: Get photos for a POI.
    - Wikimedia: Only for landmarks/tourist attractions (high relevance)
    - Unsplash:  For all local businesses (cafes, restaurants, shops, etc.)
    - Placeholder: When both fail
    """
    poi_id   = str(poi.get("_id", poi.get("id", "unknown")))
    poi_name = poi.get("name", "")
    city     = poi.get("city", poi.get("location", {}).get("city", ""))
    category = poi.get("category", "default").lower()

    cache_key = f"{poi_name}:{city}".lower().replace(" ", "_")

    # --- Check cache first ---
    cached = _get_cached_photos(cache_key)
    if cached:
        logger.info(f"Cache HIT for POI: {poi_name}")
        return {
            "poi_id":   poi_id,
            "poi_name": poi_name,
            "photos":   cached["photos"],
            "total":    len(cached["photos"]),
            "source":   cached["source"],
            "cached":   True
        }

    logger.info(f"Cache MISS for POI: {poi_name} | category: {category}")

    photos = []
    source = "unsplash"

    # --- Only try Wikimedia for landmark-type categories ---
    if _is_wikimedia_suitable(category):
        logger.info(f"Category '{category}' → trying Wikimedia first")
        photos = await _search_wikimedia(poi_name, city)
        if photos:
            source = "wikimedia"
        else:
            logger.info(f"Wikimedia found nothing relevant → falling back to Unsplash")
    else:
        logger.info(f"Category '{category}' → skipping Wikimedia, using Unsplash directly")

    # --- Unsplash fallback (or direct for businesses) ---
    if not photos:
        photos = await _search_unsplash(category)
        source = "unsplash"

    # --- Final placeholder fallback ---
    if not photos:
        photos = _get_placeholder(category, poi_name)
        source = "placeholder"

    _cache_photos(cache_key, photos, source)

    return {
        "poi_id":   poi_id,
        "poi_name": poi_name,
        "photos":   photos,
        "total":    len(photos),
        "source":   source,
        "cached":   False
    }


# ============================================================================
# WIKIMEDIA COMMONS SEARCH
# ============================================================================

def _is_wikimedia_suitable(category: str) -> bool:
    """
    Returns True only for landmark/attraction categories
    that are likely to have a dedicated Wikipedia page.
    Local businesses (cafes, restaurants) are skipped.
    """
    normalized = category.lower().strip()
    if normalized in WIKIMEDIA_SUITABLE_CATEGORIES:
        return True
    # Partial match
    for wcat in WIKIMEDIA_SUITABLE_CATEGORIES:
        if wcat in normalized:
            return True
    return False

def _is_relevant_result(page_title: str, poi_name: str, strict: bool = False) -> bool:
    """
    Check if a Wikipedia page title is relevant to the POI.

    strict=False (city+name query): 50% word overlap required
    strict=True  (name-only query): full POI name must appear in title
    """
    stop_words = {"the", "of", "in", "at", "a", "an", "and", "or", "for", "&"}

    poi_words   = {w.lower() for w in poi_name.split() if w.lower() not in stop_words and len(w) > 2}
    title_lower = page_title.lower()

    if not poi_words:
        return False

    if strict:
        # Full POI name must appear exactly in the title
        return poi_name.lower() in title_lower
    else:
        # 50% word overlap (relaxed for city+name queries)
        title_words = set(title_lower.split())
        overlap     = poi_words & title_words
        return len(overlap) / len(poi_words) >= 0.5
    
async def _search_wikimedia(name: str, city: str) -> list:
    """
    Search Wikipedia for page images by POI name + city.
    Only returns results where the page title is relevant to the POI name.
    """
    if not name:
        return []

    headers = {
        "User-Agent": "AiTravelCopilot/1.0 (AI travel assistant; contact@aitravelcopilot.com)"
    }

    search_queries = [f"{name} {city}", name] if city else [name]

    async with httpx.AsyncClient() as client:
        for i, search_query in enumerate(search_queries):
            is_fallback_query = (i > 0)  # True when searching name-only (no city)
            try:
                # Step 1: Search Wikipedia
                search_resp = await client.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action":   "query",
                        "list":     "search",
                        "srsearch": search_query,
                        "srlimit":  5,
                        "format":   "json",
                        "origin":   "*"
                    },
                    headers=headers,
                    timeout=settings.WIKIMEDIA_TIMEOUT
                )

                if search_resp.status_code != 200:
                    continue

                search_results = search_resp.json().get("query", {}).get("search", [])

                if not search_results:
                    continue

                # Step 2: Filter to only RELEVANT page titles
                relevant_titles = [
                    r["title"] for r in search_results
                    if _is_relevant_result(r["title"], name, strict=is_fallback_query)
                ]

                if not relevant_titles:
                    logger.info(f"Wikimedia: No relevant pages for '{search_query}' — skipping")
                    continue

                logger.info(f"Wikimedia: Relevant pages found: {relevant_titles}")

                # Step 3: Fetch images for relevant pages
                image_resp = await client.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action":       "query",
                        "titles":       "|".join(relevant_titles[:3]),
                        "prop":         "pageimages",
                        "piprop":       "original|thumbnail",
                        "pithumbsize":  800,
                        "format":       "json",
                        "origin":       "*"
                    },
                    headers=headers,
                    timeout=settings.WIKIMEDIA_TIMEOUT
                )

                if image_resp.status_code != 200:
                    continue

                pages  = image_resp.json().get("query", {}).get("pages", {})
                photos = []

                for page in pages.values():
                    # Main thumbnail
                    if "original" in page:
                        orig  = page["original"]
                        thumb = page.get("thumbnail", {})
                        photos.append({
                            "url":           orig.get("source", ""),
                            "thumbnail_url": thumb.get("source", orig.get("source", "")),
                            "width":         orig.get("width", 0),
                            "height":        orig.get("height", 0),
                            "source":        "wikimedia",
                            "attribution":   f"© Wikimedia Commons | {page.get('title', name)}",
                            "alt_text":      f"{name} - {page.get('title', '')}"
                        })
                     # If no original but thumbnail exists, use that
                    elif "thumbnail" in page:
                        thumb = page["thumbnail"]
                        photos.append({
                            "url":           thumb.get("source", ""),
                            "thumbnail_url": thumb.get("source", ""),
                            "width":         thumb.get("width", 0),
                            "height":        thumb.get("height", 0),
                            "source":        "wikimedia",
                            "attribution":   f"© Wikimedia Commons | {page.get('title', name)}",
                            "alt_text":      f"{name} - {page.get('title', '')}"
                        })    

                # Deduplicate and limit
                seen, unique = set(), []
                for p in photos:
                    if p["url"] and p["url"] not in seen:
                        seen.add(p["url"])
                        unique.append(p)
                    if len(unique) >= settings.MAX_PHOTOS_PER_POI:
                        break

                if unique:
                    logger.info(f"Wikimedia: {len(unique)} relevant photos for '{name}'")
                    return unique

            except httpx.TimeoutException:
                logger.warning(f"Wikimedia timeout for '{search_query}'")
                continue
            except Exception as e:
                logger.error(f"Wikimedia error: {e}")
                continue

    return []

# ============================================================================
# UNSPLASH SEARCH
# ============================================================================

async def _search_unsplash(category: str) -> list:
    """
    Search Unsplash by category keyword mapping.
    Uses Client-ID authentication (free tier: 50 req/hour).
    """
    if not settings.UNSPLASH_ACCESS_KEY:
        logger.warning("UNSPLASH_ACCESS_KEY not set — skipping Unsplash")
        return []

    query = _get_unsplash_query(category)

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.unsplash.com/search/photos",
                headers={"Authorization": f"Client-ID {settings.UNSPLASH_ACCESS_KEY}"},
                params={
                    "query":       query,
                    "per_page":    settings.MAX_PHOTOS_PER_POI,
                    "orientation": "landscape",
                    "content_filter": "high"
                },
                timeout=settings.UNSPLASH_TIMEOUT
            )

            if resp.status_code != 200:
                logger.warning(f"Unsplash API error: {resp.status_code}")
                return []

            data    = resp.json()
            results = data.get("results", [])
            photos  = []

            for item in results:
                urls = item.get("urls", {})
                user = item.get("user", {})
                photos.append({
                    "url":           urls.get("regular", ""),
                    "thumbnail_url": urls.get("small", ""),
                    "width":         item.get("width", 0),
                    "height":        item.get("height", 0),
                    "source":        "unsplash",
                    "attribution":   f"Photo by {user.get('name', 'Unknown')} on Unsplash",
                    "alt_text":      item.get("alt_description", query) or query
                })

            logger.info(f"Unsplash found {len(photos)} photos for query: '{query}'")
            return photos

    except httpx.TimeoutException:
        logger.warning(f"Unsplash timeout for query '{query}'")
        return []
    except Exception as e:
        logger.error(f"Unsplash error: {e}")
        return []


# ============================================================================
# PLACEHOLDER FALLBACK
# ============================================================================

def _get_placeholder(category: str, poi_name: str) -> list:
    """
    Return a single placeholder entry when both APIs fail.
    Frontend will show a category icon instead of a broken image.
    """
    return [{
        "url":           "",
        "thumbnail_url": "",
        "width":         0,
        "height":        0,
        "source":        "placeholder",
        "attribution":   "",
        "alt_text":      f"{poi_name} - no photo available"
    }]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _build_wikimedia_url(filename: str) -> str:
    """
    Build a direct Wikimedia Commons image URL from a filename.
    Uses the standard /wiki/Special:FilePath/ redirect.

    Example:
        "Gateway_of_India.jpg" → "https://commons.wikimedia.org/wiki/Special:FilePath/Gateway_of_India.jpg"
    """
    if not filename:
        return ""
    # Normalize: replace spaces with underscores
    clean = filename.strip().replace(" ", "_")
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{clean}"


def _get_unsplash_query(category: str) -> str:
    """
    Map a POI category string to the best Unsplash search query.
    Falls back to "default" if category not found.

    Example:
        "restaurant" → "restaurant interior dining food"
        "temple"     → "temple religious architecture"
    """
    normalized = category.lower().strip()

    # Direct match
    if normalized in CATEGORY_QUERY_MAP:
        return CATEGORY_QUERY_MAP[normalized]

    # Partial match (e.g. "fast_food_restaurant" matches "restaurant")
    for key in CATEGORY_QUERY_MAP:
        if key in normalized or normalized in key:
            return CATEGORY_QUERY_MAP[key]

    return CATEGORY_QUERY_MAP["default"]


# ============================================================================
# CACHE FUNCTIONS
# ============================================================================

def _get_cached_photos(key: str) -> Optional[dict]:
    """
    Get photos from in-memory cache if not expired.
    TTL is controlled by PHOTO_CACHE_TTL (default: 86400s = 24h).
    """
    if key not in _photo_cache:
        return None

    entry = _photo_cache[key]
    age   = time.time() - entry["cached_at"]

    if age > settings.PHOTO_CACHE_TTL:
        del _photo_cache[key]
        logger.info(f"Cache EXPIRED for key: {key}")
        return None

    return entry


def _cache_photos(key: str, photos: list, source: str) -> None:
    """
    Store photos in in-memory cache with current timestamp.
    """
    _photo_cache[key] = {
        "photos":    photos,
        "source":    source,
        "cached_at": time.time()
    }
    logger.info(f"Cached {len(photos)} photos for key: {key} (source: {source})")