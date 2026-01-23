"""
MongoDB models for Local Discovery feature (POIs, Reddit posts, Blog posts)
These are Pydantic models, NOT SQLAlchemy (MongoDB doesn't need migrations)
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Annotated
from pydantic import BaseModel, Field, BeforeValidator
from bson import ObjectId


# ✅ PYDANTIC V2 COMPATIBLE PyObjectId
def validate_object_id(v: Any) -> ObjectId:
    """Validator for ObjectId"""
    if isinstance(v, ObjectId):
        return v
    if ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


# Use Annotated type for Pydantic v2
PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class GeoJSONPoint(BaseModel):
    """GeoJSON Point for MongoDB geospatial queries"""
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "Point",
                "coordinates": [72.8777, 19.0760]
            }
        }
    }


class POI(BaseModel):
    """
    Point of Interest model from OpenStreetMap
    Stored in MongoDB 'pois' collection
    """
    id: Optional[PyObjectId] = Field(default_factory=lambda: ObjectId(), alias="_id")
    name: str
    location: GeoJSONPoint
    category: str
    tags: Dict[str, str] = Field(default_factory=dict)
    osm_id: str
    osm_type: str
    hours: Optional[str] = None
    city: str
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    source: str = "osm"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    user_feedback_count: int = 0
    average_rating: float = 0.0

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "name": "Cafe Madras",
                "location": {"type": "Point", "coordinates": [72.8311, 18.9220]},
                "category": "restaurant",
                "tags": {"cuisine": "south_indian", "diet:vegetarian": "yes"},
                "osm_id": "123456789",
                "osm_type": "node",
                "city": "mumbai"
            }
        }
    }


class RedditPost(BaseModel):
    """Reddit post model for local recommendations"""
    id: Optional[PyObjectId] = Field(default_factory=lambda: ObjectId(), alias="_id")
    title: str
    body: str
    subreddit: str
    reddit_id: str
    upvotes: int = 0
    url: str
    author: Optional[str] = None
    created_at: datetime
    city: str
    keywords: List[str] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class BlogPost(BaseModel):
    """Blog post from RSS feeds"""
    id: Optional[PyObjectId] = Field(default_factory=lambda: ObjectId(), alias="_id")
    title: str
    content: str
    author: Optional[str] = None
    url: str
    published_at: datetime
    blog_name: str
    city: str
    tags: List[str] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class UserFeedback(BaseModel):
    """User feedback on POIs"""
    id: Optional[PyObjectId] = Field(default_factory=lambda: ObjectId(), alias="_id")
    poi_id: str
    user_id: Optional[int] = None
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    visited_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }


class IngestionMetadata(BaseModel):
    """Metadata tracking for data ingestion jobs"""
    id: Optional[PyObjectId] = Field(default_factory=lambda: ObjectId(), alias="_id")
    source: str
    city: str
    last_scraped_at: datetime
    records_processed: int = 0
    status: str = "success"
    error_message: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }
