from fastapi import APIRouter, Depends, HTTPException
from fastapi import Path as PathParam
from sqlalchemy.orm import Session
from typing import List
from app.core.postgres import get_db
from app.models.trip import Trip
from app.models.hotel import Hotel
from app.schemas.hotel import (
    HotelSearchRequest,
    HotelSearchResponse,
    HotelSelect,
    HotelResponse,
)
from app.services.hotel_service import search_hotels_serpapi
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trips", tags=["Hotels"])


@router.post("/{trip_id}/hotels/search", response_model=List[HotelSearchResponse])
async def search_hotels(
    trip_id: int = PathParam(...),
    search_params: HotelSearchRequest = None,
    db: Session = Depends(get_db),
):
    """Search hotels for a trip using SerpAPI Google Hotels"""
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")

        # Auto-generate params from trip if none provided
        if not search_params:
            if not trip.destinations or len(trip.destinations) == 0:
                raise HTTPException(status_code=400, detail="Trip has no destinations")

            search_params = HotelSearchRequest(
                city=trip.destinations[0],
                check_in_date=trip.start_date.strftime("%Y-%m-%d"),
                check_out_date=trip.end_date.strftime("%Y-%m-%d"),
                adults=trip.traveler_count or 2,
                sort_by=trip.hotel_preferences.get("sort_by", "relevance") if trip.hotel_preferences else "relevance",
                max_price=trip.hotel_preferences.get("max_price") if trip.hotel_preferences else None,
                min_rating=trip.hotel_preferences.get("min_rating") if trip.hotel_preferences else None,
            )

        hotels = search_hotels_serpapi(
            city=search_params.city,
            check_in_date=search_params.check_in_date,
            check_out_date=search_params.check_out_date,
            adults=search_params.adults,
            sort_by=search_params.sort_by or "relevance",
            max_price=search_params.max_price,
            min_rating=search_params.min_rating,
        )

        logger.info(f"✅ Found {len(hotels)} hotels for trip {trip_id}")
        return hotels

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Hotel search failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to search hotels: {str(e)}")


@router.post("/{trip_id}/hotels/select", response_model=HotelResponse, status_code=201)
async def select_hotel(
    trip_id: int = PathParam(...),
    hotel_select: HotelSelect = None,
    db: Session = Depends(get_db),
):
    """Select and save a hotel to the trip"""
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")

        h = hotel_select.hotel_data

        db_hotel = Hotel(
            trip_id=trip_id,
            name=h.name,
            property_type=h.property_type,
            city=h.city,
            address=h.address,
            coordinates=h.coordinates,
            rating=h.rating,
            reviews_count=h.reviews_count,
            rating_breakdown=h.rating_breakdown,
            price_per_night=h.price_per_night,
            price_currency=h.price_currency,
            total_price=h.total_price,
            check_in_date=h.check_in_date,
            check_out_date=h.check_out_date,
            nights=h.nights,
            thumbnail=h.thumbnail,
            images=h.images,
            amenities=h.amenities,
            highlights=h.highlights,
            is_selected=True,
            booking_url=h.booking_url,
            source=h.source,
            serpapi_property_id=h.serpapi_property_id,
            raw_data=None,  # don't persist raw_data to save space
        )

        db.add(db_hotel)
        db.commit()
        db.refresh(db_hotel)

        logger.info(f"✅ Selected hotel {db_hotel.id} for trip {trip_id}")
        return db_hotel

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to select hotel: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to select hotel: {str(e)}")


@router.delete("/{trip_id}/hotels/{hotel_id}", status_code=204)
async def delete_hotel(
    trip_id: int = PathParam(...),
    hotel_id: int = PathParam(...),
    db: Session = Depends(get_db),
):
    """Delete a selected hotel from a trip"""
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")

        hotel = db.query(Hotel).filter(
            Hotel.id == hotel_id,
            Hotel.trip_id == trip_id
        ).first()

        if not hotel:
            raise HTTPException(status_code=404, detail=f"Hotel {hotel_id} not found in trip {trip_id}")

        db.delete(hotel)
        db.commit()

        logger.info(f"🗑️ Deleted hotel {hotel_id} from trip {trip_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to delete hotel: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete hotel: {str(e)}")


@router.get("/{trip_id}/hotels", response_model=List[HotelResponse])
async def get_trip_hotels(
    trip_id: int = PathParam(...),
    db: Session = Depends(get_db),
):
    """Get all selected hotels for a trip"""
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")

        hotels = db.query(Hotel).filter(Hotel.trip_id == trip_id).all()
        logger.info(f"📋 Retrieved {len(hotels)} hotels for trip {trip_id}")
        return hotels

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get hotels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get hotels: {str(e)}")
