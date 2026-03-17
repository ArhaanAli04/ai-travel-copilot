"""
PlannerAgent - AI-powered itinerary generation
Uses Gemini + TravelGuideRetriever + WeatherService
"""
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta, time
from sqlalchemy.orm import Session
import json
import logging
from google import genai
from google.genai import types

from app.core.config import settings
from app.models.trip import Trip
from app.models.trip_day import TripDay
from app.models.activity import Activity
from app.services.weather_service import weather_service
from app.ai.retrievers import create_travel_guide_retriever
from app.ai.prompts import (
    ITINERARY_SYSTEM_PROMPT,
    create_day_planning_prompt,
    format_guide_context
)


logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    AI agent for generating travel itineraries
    
    Features:
    - Weather-aware activity suggestions
    - RAG-based local recommendations
    - Budget-conscious planning
    - Personalized to user preferences
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-2.5-flash-lite"
        self.config = types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=2048,
        )
    
    async def generate_itinerary(self, trip_id: int) -> Trip:
        """
        Generate complete day-by-day itinerary for a trip
        
        Args:
            trip_id: ID of the trip to plan
            
        Returns:
            Updated Trip object with days and activities
        """
        logger.info(f"🎯 Generating itinerary for trip {trip_id}")
        
        # Load trip
        trip = self.db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise ValueError(f"Trip {trip_id} not found")
        
        # Check if itinerary already exists
        existing_days = self.db.query(TripDay).filter(TripDay.trip_id == trip_id).count()
        if existing_days > 0:
            logger.info(f"🗑️ Deleting {existing_days} existing days for trip {trip_id} to regenerate")
            
            try:
                # Delete activities first (foreign key constraint)
                deleted_activities = self.db.query(Activity).filter(
                    Activity.trip_day_id.in_(
                        self.db.query(TripDay.id).filter(TripDay.trip_id == trip_id)
                    )
                ).delete(synchronize_session=False)
                
                # Delete days
                deleted_days = self.db.query(TripDay).filter(TripDay.trip_id == trip_id).delete(synchronize_session=False)
                
                self.db.commit()
                logger.info(f"✅ Deleted {deleted_days} days and {deleted_activities} activities for trip {trip_id}")
                
            except Exception as e:
                self.db.rollback()
                logger.error(f"❌ Failed to delete existing itinerary: {e}")
                raise
        
        try:
            # Step 1: Fetch weather forecast for all trip dates
            weather_forecast = await self._fetch_weather(trip)
            
            # Step 2: Calculate budget per day
            budget_per_day = self._calculate_daily_budget(trip)
            
            # Step 3: Calculate total days
            current_date = trip.start_date.date() if isinstance(trip.start_date, datetime) else trip.start_date
            end_date = trip.end_date.date() if isinstance(trip.end_date, datetime) else trip.end_date
            total_days = (end_date - current_date).days + 1
            
            logger.info(f"📅 Planning {total_days} days from {current_date} to {end_date}")
            
            # Step 4: Generate day plans
            trip_days = []
            day_number = 1
            
            while current_date <= end_date:
                # Determine city for this day (cycle through destinations)
                city = trip.destinations[(day_number - 1) % len(trip.destinations)]
                
                logger.info(f"📅 Planning Day {day_number}/{total_days}: {city} on {current_date}")
                
                # Generate day plan
                day = await self._generate_day_plan(
                    trip=trip,
                    day_number=day_number,
                    date=current_date,
                    city=city,
                    weather_forecast=weather_forecast,
                    budget_per_day=budget_per_day
                )
                
                if day:
                    trip_days.append(day)
                
                current_date += timedelta(days=1)
                day_number += 1
            
            # Step 5: Update trip status
            trip.status = "planned"


            self.db.commit()
            
            logger.info(f"✅ Generated {len(trip_days)} days for trip {trip_id}")
            
            # Refresh to load relationships
            self.db.refresh(trip)
            return trip
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Itinerary generation failed: {e}")
            raise

    
    async def _fetch_weather(self, trip: Trip) -> Optional[Dict]:
        """Fetch weather forecast for trip"""
        try:
            # Use first destination for weather (can be enhanced later)
            city = trip.destinations[0] if trip.destinations else "Unknown"
            
            start_date = trip.start_date.date() if isinstance(trip.start_date, datetime) else trip.start_date
            end_date = trip.end_date.date() if isinstance(trip.end_date, datetime) else trip.end_date
            
            forecast = await weather_service.get_forecast(
                city=city,
                start_date=start_date,
                end_date=end_date
            )
            
            return forecast
            
        except Exception as e:
            logger.warning(f"⚠️ Weather fetch failed: {e}")
            return None
    
    def _calculate_daily_budget(self, trip: Trip) -> float:
        """Calculate budget per day"""
        currency = trip.budget_currency or "USD"

        # Currency-aware default daily budget
        DAILY_DEFAULTS = {
            "USD": 100.0,
            "EUR": 90.0,
            "GBP": 80.0,
            "INR": 3000.0,
            "JPY": 10000.0,
            "AUD": 150.0,
            "CAD": 130.0,
            "SGD": 130.0,
            "AED": 370.0,
            "THB": 3500.0,
        }

        if not trip.budget:
            return DAILY_DEFAULTS.get(currency, 100.0)
        
        start = trip.start_date.date() if isinstance(trip.start_date, datetime) else trip.start_date
        end = trip.end_date.date() if isinstance(trip.end_date, datetime) else trip.end_date
        days = (end - start).days + 1
        
        # Reserve 30% for accommodation/transport
        daily_activities_budget = (trip.budget * 0.7) / days
        
        return daily_activities_budget
    
    async def _generate_day_plan(
        self,
        trip: Trip,
        day_number: int,
        date: date,
        city: str,
        weather_forecast: Optional[Dict],
        budget_per_day: float
    ) -> Optional[TripDay]:
        """
        Generate plan for a single day
        
        Args:
            trip: Trip object
            day_number: Day number
            date: Date for this day
            city: City name
            weather_forecast: Weather forecast object
            budget_per_day: Budget per day
            
        Returns:
            TripDay object with activities
        """
        try:
            # Get weather for this specific day
            weather_data = self._get_day_weather(weather_forecast, date)
            
            # Fetch relevant travel guide content
            guide_context,guide_documents = await self._fetch_guide_context(
                city=city,
                interests=trip.interests or []
            )
            
            # Create prompt
            user_prompt = create_day_planning_prompt(
                day_number=day_number,
                date_str=date.isoformat(),
                city=city,
                weather=weather_data,
                budget_per_day=budget_per_day,
                budget_currency=trip.budget_currency or "USD",
                interests=trip.interests or [],
                preferences=trip.preferences or {},
                guide_context=guide_context,
                trip_type=trip.trip_type,
                traveler_count=trip.traveler_count
            )
            
            # Combine system prompt and user prompt
            full_prompt = f"{ITINERARY_SYSTEM_PROMPT}\n\n{user_prompt}"
            
            # Call Gemini using modern SDK
            logger.info(f"🤖 Calling Gemini for Day {day_number} plan...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=self.config
            )
            
            # Parse response
            day_plan = self._parse_gemini_response(response.text)
            
            if not day_plan:
                logger.warning(f"⚠️ Failed to parse Gemini response for Day {day_number}")
                return None
            
            # Create TripDay record
            trip_day = TripDay(
                trip_id=trip.id,
                day_number=day_number,
                date=date,
                city=city,
                theme=day_plan.get("day_theme"),
                description=day_plan.get("day_description"),
                weather_temp_high=weather_data.get("temp_high"),
                weather_temp_low=weather_data.get("temp_low"),
                weather_condition=weather_data.get("condition"),
                weather_icon=weather_data.get("icon"),
                weather_precipitation_prob=weather_data.get("precipitation_prob")
            )
            
            self.db.add(trip_day)
            self.db.flush()  # Get trip_day.id
            
            # Create Activity records
            activities = day_plan.get("activities", [])
            for idx, activity_data in enumerate(activities, 1):
                activity = self._create_activity(
                    trip_day_id=trip_day.id,
                    order=idx,
                    activity_data=activity_data,
                    guide_documents=guide_documents,
                    budget_currency=trip.budget_currency or "USD",
                )
                self.db.add(activity)
            
            self.db.commit()
            logger.info(f"✅ Created Day {day_number} with {len(activities)} activities")
            
            return trip_day
            
        except Exception as e:
            logger.error(f"❌ Day plan generation failed: {e}")
            return None
    
    def _get_day_weather(self, forecast: Optional[Dict], target_date: date) -> Dict:
        """Extract weather for specific date"""
        default_weather = {
            "temp_high": 20.0,
            "temp_low": 15.0,
            "condition": "Unknown",
            "icon": "🌤️",
            "precipitation_prob": 0.0
        }
        
        if not forecast:
            return default_weather
        
        day_weather = weather_service.get_day_weather(forecast, target_date)
        
        if not day_weather:
            return default_weather
        
        return {
            "temp_high": day_weather.temp_max,
            "temp_low": day_weather.temp_min,
            "condition": day_weather.condition,
            "icon": day_weather.icon,
            "precipitation_prob": day_weather.precipitation_probability
        }
    
    async def _fetch_guide_context(self, city: str, interests: List[str]) -> tuple[str,List]:
        """Fetch relevant travel guide content
            Returns:
        Tuple of (formatted_context_string, list_of_documents)
        """
        try:
            # Map interests to themes
            theme_map = {
                "culture": "culture",
                "food": "food",
                "nightlife": "nightlife",
                "adventure": "attractions",
                "relaxation": "attractions",
                "shopping": "attractions"
            }
            
            themes = list(set(theme_map.get(i.lower(), "attractions") for i in interests))
            if not themes:
                themes = ["attractions", "food"]
            
            # Create retriever
            retriever = create_travel_guide_retriever(
                city=city,
                themes=themes,
                k=5,
                use_cache=True
            )
            
            # Query for general recommendations
            query = f"best things to do in {city}"
            documents = retriever._get_relevant_documents(query)
            
            # Format into context string
            context = format_guide_context(documents)
            
            return context,documents
            
        except Exception as e:
            logger.warning(f"⚠️ Guide context fetch failed: {e}")
            return f"Use general knowledge of {city}"
    


    def _parse_gemini_response(self, response_text: str) -> Optional[Dict]:
        """Parse Gemini JSON response"""
        try:
            # Remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            text = text.strip()
            
            # Parse JSON
            data = json.loads(text)
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parse error: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            return None
    
    def _create_activity(
        self,
        trip_day_id: int,
        order: int,
        activity_data: Dict,
        guide_documents: List = None,
        budget_currency: str = "USD",
    ) -> Activity:
        """Create Activity record from parsed data
           Args:
        trip_day_id: ID of the trip day
        order: Activity order in the day
        activity_data: Parsed activity data from Gemini
        guide_documents: List of guide documents used for this day's planning
        """
        
        # Parse start time
        start_time_str = activity_data.get("start_time", "09:00")
        try:
            hour, minute = map(int, start_time_str.split(":"))
            start_time = time(hour=hour, minute=minute)
        except:
            start_time = None
        
        # Calculate end time
        duration = activity_data.get("duration_minutes", 60)
        end_time = None
        if start_time and duration:
            start_dt = datetime.combine(date.today(), start_time)
            end_dt = start_dt + timedelta(minutes=duration)
            end_time = end_dt.time()
        
        source_refs = None
        if guide_documents:
            source_refs = {
                "sources": [
                    {
                        "city": doc.metadata.get("city"),
                        "theme": doc.metadata.get("theme"),
                        "source_url": doc.metadata.get("source_url"),
                        "source_title": doc.metadata.get("source_title"),
                        "relevance_score": doc.metadata.get("relevance_score"),
                        "content_snippet": doc.page_content[:200]  # First 200 chars
                    }
                    for doc in guide_documents[:3]  # Top 3 most relevant
                ],
                "query_city": guide_documents[0].metadata.get("city") if guide_documents else None
            }

        return Activity(
            trip_day_id=trip_day_id,
            title=activity_data.get("title", "Untitled Activity"),
            description=activity_data.get("description"),
            category=activity_data.get("category", "sightseeing"),
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration,
            order=order,
            location=activity_data.get("location"),
            estimated_cost=activity_data.get("estimated_cost", 0.0),
            cost_currency=budget_currency,
            source_refs=source_refs,
            ai_reasoning=activity_data.get("reasoning"),
            is_booked=False
        )


# Factory function
def create_planner_agent(db: Session) -> PlannerAgent:
    """Create PlannerAgent instance"""
    return PlannerAgent(db)
