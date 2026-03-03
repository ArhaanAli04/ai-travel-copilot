"""
Disruption Service - Flight Status & Weather Integration
Enriches disruption cases with real-time data
"""
import httpx
import logging
from typing import Optional, Dict, List
from datetime import datetime, date,timezone
from sqlalchemy.orm import Session
import asyncio
from app.core.config import settings
from app.models.disruption import DisruptionCase, DisruptionSeverity
from app.services.web_search_service import web_search_service
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class DisruptionService:
    """
    Service for enriching disruption cases with real-time data
    
    Features:
    - Flight status checking via AviationStack
    - Weather alerts via Tomorrow.io
    - Travel alerts via web search
    - Auto-severity detection
    """
    
    def __init__(self):
        self.aviationstack_api_key = settings.AVIATIONSTACK_API_KEY
        self.tomorrow_io_api_key = settings.TOMORROW_IO_API_KEY
        self.aviationstack_base_url = "http://api.aviationstack.com/v1"
        self.tomorrow_io_base_url = "https://api.tomorrow.io/v4"
        self.airports_db = self._load_airports_db()
        self.api_calls = {
            "aviationstack": 0,
            "tomorrow_io": 0
        }
    
    def _load_airports_db(self) -> Dict:
        """Load airport database from JSON file"""
        try:
            airports_file = Path(__file__).parent.parent / "data" / "airports.json"
            
            logger.info(f"📁 Loading airports from: {airports_file}")
            
            if not airports_file.exists():
                logger.error(f"❌ Airports file not found at {airports_file}")
                return {}
            
            with open(airports_file, 'r', encoding='utf-8') as f:
                airports_data = json.load(f)
            
            logger.info(f"📖 Loaded JSON with {len(airports_data)} entries")
            
            # Build IATA lookup dictionary
            # JSON format: {"ICAO": {"iata": "JFK", "lat": 40.6, "lon": -73.7, ...}, ...}
            airports_dict = {}
            
            for icao_code, airport_info in airports_data.items():
                # Get IATA code
                iata = airport_info.get("iata", "").strip()
                
                # Skip if no IATA code
                if not iata:
                    continue
                
                # Skip if no coordinates
                lat = airport_info.get("lat")
                lon = airport_info.get("lon")
                
                if lat is None or lon is None:
                    continue
                
                # Add to dictionary with IATA as key
                airports_dict[iata.upper()] = {
                    "lat": float(lat),
                    "lon": float(lon),
                    "name": airport_info.get("name", ""),
                    "city": airport_info.get("city", ""),
                    "country": airport_info.get("country", ""),
                    "icao": icao_code,
                    "state": airport_info.get("state", "")
                }
            
            logger.info(f"✅ Loaded {len(airports_dict)} airports with valid IATA codes")
            
            # Log some examples
            if airports_dict:
                sample_codes = list(airports_dict.keys())[:10]
                logger.info(f"   Sample IATA codes: {sample_codes}")
            
            return airports_dict
            
        except FileNotFoundError:
            logger.error(f"❌ Airports file not found")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in airports file: {e}")
            return {}
        except Exception as e:
            logger.error(f"❌ Failed to load airports: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
    async def check_flight_status(
        self,
        flight_number: str,
        flight_date: date
    ) -> Optional[Dict]:
        """
        Check flight status using AviationStack API
        
        Args:
            flight_number: Flight number (e.g., "AA123")
            flight_date: Date of flight
            
        Returns:
            Dict with flight status info or None if error
        """
        try:
            self.api_calls["aviationstack"] += 1
            logger.info(f"🔍 Checking flight status for {flight_number} on {flight_date}")
            
            # AviationStack endpoint
            url = f"{self.aviationstack_base_url}/flights"
            
            params = {
                "access_key": self.aviationstack_api_key,
                "flight_iata": flight_number,  # e.g., AA123
                # Note: Free tier doesn't support date filtering
                # "flight_date": flight_date.isoformat()
            }
            
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Check if flight found
                if not data.get("data"):
                    logger.warning(f"⚠️ No flight data found for {flight_number}")
                    return None
                
                # Get first matching flight
                flight_info = data["data"][0]
                
                # Extract relevant info
                result = {
                    "flight_number": flight_info.get("flight", {}).get("iata"),
                    "airline": flight_info.get("airline", {}).get("name"),
                    "status": flight_info.get("flight_status"),  # scheduled, active, landed, cancelled, delayed
                    "departure": {
                        "airport": flight_info.get("departure", {}).get("airport"),
                        "iata": flight_info.get("departure", {}).get("iata"),
                        "scheduled": flight_info.get("departure", {}).get("scheduled"),
                        "estimated": flight_info.get("departure", {}).get("estimated"),
                        "actual": flight_info.get("departure", {}).get("actual"),
                        "delay": flight_info.get("departure", {}).get("delay"),
                        "terminal": flight_info.get("departure", {}).get("terminal"),
                        "gate": flight_info.get("departure", {}).get("gate"),
                    },
                    "arrival": {
                        "airport": flight_info.get("arrival", {}).get("airport"),
                        "iata": flight_info.get("arrival", {}).get("iata"),
                        "scheduled": flight_info.get("arrival", {}).get("scheduled"),
                        "estimated": flight_info.get("arrival", {}).get("estimated"),
                        "actual": flight_info.get("arrival", {}).get("actual"),
                        "delay": flight_info.get("arrival", {}).get("delay"),
                        "terminal": flight_info.get("arrival", {}).get("terminal"),
                        "gate": flight_info.get("arrival", {}).get("gate"),
                    },
                    "aircraft": flight_info.get("aircraft", {}).get("registration"),
                    "fetched_at": datetime.now(timezone.utc).isoformat() 
                }
                
                logger.info(f"✅ Flight status: {result['status']}")
                return result
        except httpx.TimeoutException:
            logger.error(f"⏱️ AviationStack API timeout for {flight_number}")
            return None        
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ AviationStack API error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Flight status check failed: {e}")
            return None
    
    async def check_weather_alerts(
        self,
        airport_code: str,
        check_date: date
    ) -> Optional[Dict]:
        """
        Check weather alerts using Tomorrow.io API
        
        Args:
            airport_code: Airport IATA code (e.g., "JFK")
            check_date: Date to check weather
            
        Returns:
            Dict with weather alerts or None if error
        """
        try:
            self.api_calls["tomorrow_io"] += 1
            logger.info(f"🌦️ Checking weather alerts for {airport_code} on {check_date}")
            
            # Get coordinates for airport (simplified mapping)
            # In production, use a proper airport database
            airport_coords = self._get_airport_coordinates(airport_code)
            
            if not airport_coords:
                logger.warning(f"⚠️ No coordinates found for airport {airport_code}")
                return None
            
            # Tomorrow.io realtime weather endpoint
            url = f"{self.tomorrow_io_base_url}/weather/realtime"
            
            params = {
                "location": f"{airport_coords['lat']},{airport_coords['lon']}",
                "apikey": self.tomorrow_io_api_key
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                values = data.get("data", {}).get("values", {})
                
                # Extract weather info
                result = {
                    "airport_code": airport_code,
                    "temperature": values.get("temperature"),
                    "temperature_apparent": values.get("temperatureApparent"),
                    "humidity": values.get("humidity"),
                    "wind_speed": values.get("windSpeed"),
                    "precipitation_probability": values.get("precipitationProbability", 0),
                    "weather_code": values.get("weatherCode"),
                    "visibility": values.get("visibility"),
                    "cloud_cover": values.get("cloudCover"),
                    "condition": self._weather_code_to_condition(values.get("weatherCode", 0)),
                    "severity": self._determine_weather_severity(values),
                    "fetched_at": datetime.now(timezone.utc).isoformat()
                }
                
                logger.info(f"✅ Weather: {result['condition']}, Severity: {result['severity']}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Tomorrow.io API error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Weather check failed: {e}")
            return None
    
    
    async def search_alternative_flights(
        self,
        origin_iata: str,
        destination_iata: str,
        departure_date: str,  # ISO format: "2026-01-18"
        cabin_class: str = "economy",
        max_results: int = 3
    ) -> List[Dict]:
        """
        Search for alternative flights using SerpAPI Google Flights
        
        Args:
            origin_iata: Origin airport IATA code (e.g., "LHR")
            destination_iata: Destination airport IATA code (e.g., "CDG")
            departure_date: Departure date in YYYY-MM-DD format
            cabin_class: Cabin class (economy, business, first)
            max_results: Maximum number of alternative flights to return
            
        Returns:
            List of flight dictionaries with details
        """
        try:
            logger.info(f"✈️ Searching alternative flights: {origin_iata} → {destination_iata} on {departure_date}")
            
            # Import flight service
            from app.services.flight_service import search_flights_serpapi
            
            # Search flights using existing SerpAPI integration
            flights = search_flights_serpapi(
                origin=origin_iata,
                destination=destination_iata,
                departure_date=departure_date,
                cabin_class=cabin_class,
                max_stops=0,  # Allow 1 stop for more options
                passengers=1,
                trip_type="one_way"
            )

            if not flights:
                logger.info("⚠️ No direct flights found, searching with 1 stop...")
                flights = search_flights_serpapi(
                    origin=origin_iata,
                    destination=destination_iata,
                    departure_date=departure_date,
                    cabin_class=cabin_class,
                    max_stops=1,
                    passengers=1,
                    trip_type="one_way"
                )
            
            # Convert to dict format
            alternative_flights = []
            
            for flight in flights[:max_results]:
                alternative_flights.append({
                    "flight_number": flight.flight_number,
                    "airline": flight.airline,
                    "airline_code": flight.airline_code,
                    "departure_time": flight.departure_time.isoformat(),
                    "arrival_time": flight.arrival_time.isoformat(),
                    "duration_minutes": flight.duration_minutes,
                    "stops": flight.stops,
                    "layover_airports": flight.layover_airports,
                    "cabin_class": flight.cabin_class,
                    "price_amount": flight.price_amount,
                    "price_currency": flight.price_currency,
                    "booking_url": flight.booking_url,
                    "aircraft_type": flight.aircraft_type,
                    "amenities": flight.amenities or [],
                    "source": "serpapi"
                })
            
            logger.info(f"✅ Found {len(alternative_flights)} alternative flights")
            return alternative_flights
            
        except Exception as e:
            logger.error(f"❌ Alternative flight search failed: {e}")
            # Return empty list instead of raising - allow other options to be generated
            return []

    async def get_airline_info(self, airline_name: str, db: Session) -> Dict:
        """
        Get airline contact info — DB first, SerpAPI on miss.
        """
        from app.models.airline import Airline

        # 1. Check DB cache
        existing = db.query(Airline).filter(
            Airline.name.ilike(f"%{airline_name}%")
        ).first()

        if existing:
            logger.info(f"⚡ DB CACHE HIT — airline info for {airline_name}")
            return {
                "name": existing.name,
                "website": existing.website,
                "customer_service_url": existing.customer_service_url,
                "phone": existing.phone,
                "iata_code": existing.iata_code,
            }

        # 2. Cache miss — fetch via SerpAPI Knowledge Graph
        logger.info(f"🌐 SERPAPI CALL — fetching airline info for {airline_name}")
        try:
            import httpx
            params = {
                "engine": "google",
                "q": f"{airline_name} airline official website customer service",
                "api_key": settings.SERPAPI_KEY,
                "num": 3
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://serpapi.com/search", params=params)
                data = response.json()

            # Extract from knowledge graph if available
            kg = data.get("knowledge_graph", {})
            website = kg.get("website") or kg.get("official_website")
            phone = kg.get("phone")

            # Fallback: grab first organic result URL as website
            if not website:
                organic = data.get("organic_results", [])
                if organic:
                    website = organic[0].get("link")

            # Save to DB
            airline_record = Airline(
                name=airline_name,
                website=website,
                customer_service_url=website,  # refine later if KG has specific CS url
                phone=phone,
            )
            db.add(airline_record)
            db.commit()
            db.refresh(airline_record)
            logger.info(f"💾 Saved airline info for {airline_name} to DB")

            return {
                "name": airline_name,
                "website": website,
                "customer_service_url": website,
                "phone": phone,
                "iata_code": None,
            }

        except Exception as e:
            logger.error(f"❌ Failed to fetch airline info for {airline_name}: {e}")
            return {"name": airline_name, "website": None, "phone": None}

    async def check_travel_alerts(
        self,
        origin: str,
        destination: str,
        check_date: date
    ) -> Optional[List[Dict]]:
        """
        Check for travel alerts (strikes, closures) using web search
        
        Args:
            origin: Origin city/airport
            destination: Destination city/airport
            check_date: Date of travel
            
        Returns:
            List of alert dicts or None if error
        """
        try:
            logger.info(f"📰 Checking travel alerts for {origin} → {destination}")
            
            # Search for travel disruptions
            queries = [
                f"{origin} airport strike {check_date.year}",
                f"{destination} airport closure {check_date.year}",
                f"travel disruption {origin} {destination}"
            ]
            
            alerts = []
            
            for query in queries:
                try:
                    results = await web_search_service.search(query, num_results=2)
                    
                    for result in results:
                        # Check if result mentions strikes, closures, or disruptions
                        content_lower = (result.get("snippet", "") + result.get("title", "")).lower()
                        
                        is_alert = any(keyword in content_lower for keyword in [
                            "strike", "closure", "closed", "disruption", "cancelled",
                            "emergency", "protest", "shutdown"
                        ])
                        
                        if is_alert:
                            alerts.append({
                                "title": result.get("title"),
                                "snippet": result.get("snippet"),
                                "url": result.get("url"),
                                "source": result.get("source"),
                                "alert_type": "travel_disruption"
                            })
                
                except Exception as e:
                    logger.warning(f"⚠️ Web search failed for '{query}': {e}")
                    continue
            
            if alerts:
                logger.info(f"✅ Found {len(alerts)} travel alerts")
            else:
                logger.info(f"✅ No travel alerts found")
            
            return alerts if alerts else None
            
        except Exception as e:
            logger.error(f"❌ Travel alerts check failed: {e}")
            return None
    
    async def enrich_disruption_case(
        self,
        case: DisruptionCase,
        db: Session
    ) -> DisruptionCase:
        """
        Enrich disruption case with real-time data
        
        Args:
            case: DisruptionCase to enrich
            db: Database session
            
        Returns:
            Updated DisruptionCase
        """
        try:
            logger.info(f"🔄 Enriching disruption case {case.id}")
            
            # Initialize metadata if None
            if not case.meta_data:
                case.meta_data = {}
            
            # ✅ 1. Check flight status with timeout
            logger.info(f"✈️ Checking flight status for {case.flight_number}...")
            try:
                flight_status = await asyncio.wait_for(
                    self.check_flight_status(
                        case.flight_number,
                        case.disruption_date.date() if isinstance(case.disruption_date, datetime) else case.disruption_date
                    ),
                    timeout=10.0  # 10 second timeout
                )
                
                if flight_status:
                    case.meta_data["flight_status"] = flight_status
                    logger.info(f"✅ Flight status: {flight_status.get('status', 'unknown')}")
                    
                    # Update current_status based on flight status
                    status = flight_status.get("status", "").lower()
                    delay_minutes = flight_status.get("departure", {}).get("delay", 0) or 0
                    
                    if status == "cancelled":
                        case.current_status = "Flight cancelled"
                        case.severity = DisruptionSeverity.CRITICAL
                    elif status == "delayed":
                        case.current_status = f"Delayed by {delay_minutes} minutes"
                        case.severity = self._calculate_severity_from_delay(delay_minutes)
                    elif status == "active":
                        case.current_status = "Flight is active (in air)"
                    elif status == "landed":
                        case.current_status = "Flight has landed"
                    else:
                        case.current_status = f"Flight status: {status}"
                else:
                    logger.warning(f"⚠️ No flight status data returned")
                    case.current_status = "Unable to verify flight status"
                    
            except asyncio.TimeoutError:
                logger.warning(f"⏱️ Flight status check timeout (>10s)")
                case.current_status = "Flight status check timed out"
            except Exception as e:
                logger.warning(f"⚠️ Flight status check failed: {e}")
                case.current_status = "Unable to check flight status"
            
            # ✅ 2. Check weather alerts with timeout
           
            
            # ✅ 4. Update timestamp
            case.meta_data["last_enriched"] = datetime.now(timezone.utc).isoformat()
            case.updated_at = datetime.now(timezone.utc)
            
            db.commit()
            db.refresh(case)
            
            logger.info(f"✅ Case {case.id} enriched successfully")
            return case
            
        except Exception as e:
            logger.error(f"❌ Case enrichment failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            db.rollback()
            # Don't raise - return case even if enrichment fails
            case.current_status = "Created (enrichment failed)"
            db.commit()
            return case

    

    # ===== Helper Methods =====
    
    def _get_airport_coordinates(self, airport_code: str) -> Optional[Dict]:
        """Get coordinates from local database"""
        airport = self.airports_db.get(airport_code.upper())
        
        if not airport:
            logger.warning(f"⚠️ Airport {airport_code} not found")
            return None
        
        return {
            "lat": airport["lat"],
            "lon": airport["lon"]
        }
    
    def _weather_code_to_condition(self, code: int) -> str:
        """Convert Tomorrow.io weather code to readable condition"""
        # Simplified mapping
        weather_codes = {
            0: "Unknown",
            1000: "Clear",
            1100: "Mostly Clear",
            1101: "Partly Cloudy",
            1102: "Mostly Cloudy",
            1001: "Cloudy",
            2000: "Fog",
            2100: "Light Fog",
            4000: "Drizzle",
            4001: "Rain",
            4200: "Light Rain",
            4201: "Heavy Rain",
            5000: "Snow",
            5001: "Flurries",
            5100: "Light Snow",
            5101: "Heavy Snow",
            6000: "Freezing Drizzle",
            6001: "Freezing Rain",
            7000: "Ice Pellets",
            8000: "Thunderstorm",
        }
        return weather_codes.get(code, "Unknown")
    
    def _determine_weather_severity(self, weather_values: Dict) -> str:
        """Determine weather severity for flight operations"""
        precip_prob = weather_values.get("precipitationProbability", 0)
        wind_speed = weather_values.get("windSpeed", 0)
        visibility = weather_values.get("visibility", 10)
        weather_code = weather_values.get("weatherCode", 1000)
        
        # High severity conditions
        if weather_code in [4201, 5101, 6001, 8000]:  # Heavy rain/snow, freezing rain, thunderstorm
            return "high"
        if wind_speed > 25:  # Strong winds
            return "high"
        if visibility < 1:  # Low visibility
            return "high"
        
        # Medium severity
        if precip_prob > 70:
            return "medium"
        if wind_speed > 15:
            return "medium"
        if visibility < 5:
            return "medium"
        
        # Low severity
        return "low"
    
    def _calculate_severity_from_delay(self, delay_minutes: int) -> DisruptionSeverity:
        """Calculate disruption severity based on delay duration"""
        if delay_minutes < 120:  # < 2 hours
            return DisruptionSeverity.LOW
        elif delay_minutes < 240:  # 2-4 hours
            return DisruptionSeverity.MEDIUM
        elif delay_minutes < 480:  # 4-8 hours
            return DisruptionSeverity.HIGH
        else:  # > 8 hours
            return DisruptionSeverity.CRITICAL


# Singleton instance
disruption_service = DisruptionService()
