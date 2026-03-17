from typing import List, Optional
from datetime import datetime, date
from serpapi import GoogleSearch
from app.schemas.hotel import HotelSearchResponse
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

SORT_MAP = {
    "relevance": None,       # default, don't send sort_by
    "lowest_price": "3",
    "highest_rating": "8",
    "most_reviewed": "13",
}


def search_hotels_serpapi(
    city: str,
    check_in_date: str,
    check_out_date: str,
    adults: int = 2,
    sort_by: str = "relevance",
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    currency: str = "USD",
) -> List[HotelSearchResponse]:
    """
    Search hotels using SerpAPI Google Hotels API
    """
    if not settings.SERPAPI_KEY:
        logger.error("❌ SERPAPI_KEY not configured")
        raise ValueError("SerpAPI key not configured")

    params = {
        "engine": "google_hotels",
        "q": city,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "adults": adults,
        "currency": currency,
        "hl": "en",
        "api_key": settings.SERPAPI_KEY,
    }

    sort_value = SORT_MAP.get(sort_by)
    if sort_value:
        params["sort_by"] = sort_value

    logger.info(f"🔍 Searching hotels in {city} | {check_in_date} → {check_out_date} | {adults} adults")

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        if "error" in results:
            logger.error(f"❌ SerpAPI error: {results['error']}")
            raise Exception(f"SerpAPI error: {results['error']}")

        properties = results.get("properties", [])

        if not properties:
            logger.warning(f"⚠️ No hotels found for {city}")
            return []

        # Calculate nights
        nights = _calculate_nights(check_in_date, check_out_date)

        parsed = []
        for prop in properties[:8]:  # limit to 8 results
            try:
                hotel = parse_serpapi_hotel(
                    prop, city, check_in_date, check_out_date, nights,
                    currency=currency, 
                )
                if hotel is None:
                    continue
                # Apply client-side filters
                if max_price and hotel.price_per_night > max_price:
                    continue
                if min_rating and (hotel.rating or 0) < min_rating:
                    continue
                parsed.append(hotel)
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse hotel: {e}")
                continue

        logger.info(f"✅ Parsed {len(parsed)} hotels for {city}")
        return parsed

    except Exception as e:
        logger.error(f"❌ Hotel search failed: {e}")
        raise Exception(f"Failed to search hotels: {str(e)}")


def parse_serpapi_hotel(
    prop: dict,
    city: str,
    check_in_date: str,
    check_out_date: str,
    nights: int,
    currency: str = "USD",
) -> Optional[HotelSearchResponse]:
    """Parse a single SerpAPI hotel property into HotelSearchResponse"""
    try:
        # Price — SerpAPI returns rate.extracted_lowest or rate.lowest
        rate = prop.get("rate_per_night", {})
        price_per_night = rate.get("extracted_lowest") or rate.get("lowest")

        # Skip if no price
        if not price_per_night:
            return None

        # Rating
        rating = prop.get("overall_rating")
        reviews_count = prop.get("reviews")

        # Images
        images = []
        thumbnail = None
        raw_images = prop.get("images", [])
        if raw_images:
            thumbnail = raw_images[0].get("thumbnail") or raw_images[0].get("original_image")
            images = [
                img.get("original_image") or img.get("thumbnail")
                for img in raw_images[:6]
                if img.get("original_image") or img.get("thumbnail")
            ]

        # Amenities — from "amenities" key or "nearby_places"
        amenities = []
        raw_amenities = prop.get("amenities", [])
        for a in raw_amenities:
            if isinstance(a, str):
                amenities.append(a.lower())
            elif isinstance(a, dict):
                name = a.get("name", "")
                if name:
                    amenities.append(name.lower())

        # Highlights — from "highlights" or "description"
        highlights = prop.get("highlights", [])
        if not highlights:
            desc = prop.get("description", "")
            if desc:
                highlights = [desc[:120]]

        # GPS coordinates
        gps = prop.get("gps_coordinates", {})
        coordinates = None
        if gps:
            coordinates = {
                "lat": gps.get("latitude"),
                "lng": gps.get("longitude")
            }

        # Booking link
        booking_url = prop.get("link") or prop.get("serpapi_property_link", "https://www.google.com/travel/hotels")

        return HotelSearchResponse(
            name=prop.get("name", "Unknown Hotel"),
            property_type=prop.get("type", "hotel").lower(),
            city=city,
            address=prop.get("address"),
            coordinates=coordinates,
            rating=float(rating) if rating else None,
            reviews_count=int(reviews_count) if reviews_count else None,
            price_per_night=float(price_per_night),
            price_currency=currency,
            total_price=round(float(price_per_night) * nights, 2) if nights else None,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            nights=nights,
            thumbnail=thumbnail,
            images=images if images else None,
            amenities=amenities if amenities else None,
            highlights=highlights if highlights else None,
            booking_url=booking_url,
            source="serpapi",
            serpapi_property_id=str(prop.get("property_token") or prop.get("id", "")),
            raw_data=prop,
        )

    except Exception as e:
        logger.error(f"❌ Error parsing hotel property: {e}")
        return None


def _calculate_nights(check_in: str, check_out: str) -> int:
    """Calculate number of nights between check-in and check-out"""
    try:
        ci = date.fromisoformat(check_in)
        co = date.fromisoformat(check_out)
        return max((co - ci).days, 1)
    except Exception:
        return 1
