"""
Weather Service - Fetch weather forecasts for trip planning
Uses Open-Meteo API (free, no API key required)
"""
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
import httpx
import logging
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class DailyWeather(BaseModel):
    """Daily weather forecast"""
    date: date
    temp_max: float  # Celsius
    temp_min: float  # Celsius
    condition: str  # "Clear", "Cloudy", "Rain", etc.
    condition_code: int  # WMO weather code
    precipitation_probability: float  # 0-100%
    icon: str  # Weather emoji


class WeatherForecast(BaseModel):
    """Complete weather forecast for a location"""
    city: str
    latitude: float
    longitude: float
    daily_forecasts: List[DailyWeather]
    cached_at: datetime


class WeatherService:
    """
    Weather service using Open-Meteo API
    
    Features:
    - Free API, no key required
    - 7-day forecast
    - 24-hour caching to minimize API calls
    - Geocoding for city names
    """
    
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.cache: Dict[str, WeatherForecast] = {}
        self.cache_ttl_hours = 24
    
    async def get_forecast(
        self, 
        city: str, 
        start_date: date, 
        end_date: date
    ) -> Optional[WeatherForecast]:
        """
        Get weather forecast for a city and date range
        
        Args:
            city: City name (e.g., "Paris", "Tokyo")
            start_date: Start date of trip
            end_date: End date of trip
            
        Returns:
            WeatherForecast object or None if error
        """
        logger.info(f"🌤️ Fetching weather for {city} ({start_date} to {end_date})")
        
        # Check cache first
        cache_key = f"{city}:{start_date}:{end_date}"
        if cache_key in self.cache:
            cached_forecast = self.cache[cache_key]
            age_hours = (datetime.now() - cached_forecast.cached_at).total_seconds() / 3600
            
            if age_hours < self.cache_ttl_hours:
                logger.info(f"✅ Weather cache hit for {city} (age: {age_hours:.1f}h)")
                return cached_forecast
            else:
                logger.info(f"⚠️ Weather cache expired for {city}")
        
        # Cache miss → fetch fresh data
        try:
            # Step 1: Geocode city name to coordinates
            coords = await self._geocode_city(city)
            if not coords:
                logger.error(f"❌ Could not geocode city: {city}")
                return None
            
            # Step 2: Fetch weather forecast
            forecast = await self._fetch_forecast(
                city=city,
                latitude=coords["latitude"],
                longitude=coords["longitude"],
                start_date=start_date,
                end_date=end_date
            )
            
            if forecast:
                # Cache the result
                self.cache[cache_key] = forecast
                logger.info(f"✅ Weather forecast cached for {city}")
            
            return forecast
            
        except Exception as e:
            logger.error(f"❌ Weather fetch failed for {city}: {e}")
            return None
    
    async def _geocode_city(self, city: str) -> Optional[Dict]:
        """
        Convert city name to coordinates using Open-Meteo Geocoding API
        
        Args:
            city: City name
            
        Returns:
            Dict with latitude, longitude, or None
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.geocoding_url,
                    params={
                        "name": city,
                        "count": 1,
                        "language": "en",
                        "format": "json"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if not data.get("results"):
                    logger.warning(f"⚠️ No geocoding results for {city}")
                    return None
                
                result = data["results"][0]
                logger.info(f"✅ Geocoded {city}: {result['latitude']}, {result['longitude']}")
                
                return {
                    "latitude": result["latitude"],
                    "longitude": result["longitude"],
                    "name": result.get("name", city),
                    "country": result.get("country", "")
                }
                
        except Exception as e:
            logger.error(f"❌ Geocoding failed for {city}: {e}")
            return None
    
    async def _fetch_forecast(
        self,
        city: str,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date
    ) -> Optional[WeatherForecast]:
        """
        Fetch weather forecast from Open-Meteo API
        
        Args:
            city: City name
            latitude: Latitude
            longitude: Longitude
            start_date: Start date
            end_date: End date
            
        Returns:
            WeatherForecast object or None
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "latitude": latitude,
                        "longitude": longitude,
                        "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_probability_max",
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "timezone": "auto"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # Parse daily forecasts
                daily_forecasts = []
                daily_data = data.get("daily", {})
                
                for i, date_str in enumerate(daily_data.get("time", [])):
                    forecast_date = datetime.fromisoformat(date_str).date()
                    
                    weather_code = daily_data["weathercode"][i]
                    condition = self._weather_code_to_condition(weather_code)
                    icon = self._weather_code_to_icon(weather_code)
                    
                    daily_forecasts.append(DailyWeather(
                        date=forecast_date,
                        temp_max=daily_data["temperature_2m_max"][i],
                        temp_min=daily_data["temperature_2m_min"][i],
                        condition=condition,
                        condition_code=weather_code,
                        precipitation_probability=daily_data["precipitation_probability_max"][i],
                        icon=icon
                    ))
                
                forecast = WeatherForecast(
                    city=city,
                    latitude=latitude,
                    longitude=longitude,
                    daily_forecasts=daily_forecasts,
                    cached_at=datetime.now()
                )
                
                logger.info(f"✅ Fetched {len(daily_forecasts)} days of weather for {city}")
                return forecast
                
        except Exception as e:
            logger.error(f"❌ Weather API request failed: {e}")
            return None
    
    def _weather_code_to_condition(self, code: int) -> str:
        """
        Convert WMO weather code to readable condition
        
        WMO Weather interpretation codes (WW):
        https://open-meteo.com/en/docs
        """
        code_map = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        return code_map.get(code, "Unknown")
    
    def _weather_code_to_icon(self, code: int) -> str:
        """Convert weather code to emoji icon"""
        if code == 0:
            return "☀️"
        elif code in [1, 2]:
            return "⛅"
        elif code == 3:
            return "☁️"
        elif code in [45, 48]:
            return "🌫️"
        elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
            return "🌧️"
        elif code in [71, 73, 75, 77, 85, 86]:
            return "❄️"
        elif code in [95, 96, 99]:
            return "⛈️"
        else:
            return "🌤️"
    
    def get_day_weather(
        self, 
        forecast: WeatherForecast, 
        target_date: date
    ) -> Optional[DailyWeather]:
        """
        Extract weather for a specific date from forecast
        
        Args:
            forecast: WeatherForecast object
            target_date: Date to get weather for
            
        Returns:
            DailyWeather for that date or None
        """
        for daily in forecast.daily_forecasts:
            if daily.date == target_date:
                return daily
        return None
    
    def format_temperature(self, temp_celsius: float, include_fahrenheit: bool = True) -> str:
        """
        Format temperature string
        
        Args:
            temp_celsius: Temperature in Celsius
            include_fahrenheit: Whether to include Fahrenheit
            
        Returns:
            Formatted temperature string
        """
        if include_fahrenheit:
            temp_fahrenheit = (temp_celsius * 9/5) + 32
            return f"{temp_celsius:.0f}°C / {temp_fahrenheit:.0f}°F"
        else:
            return f"{temp_celsius:.0f}°C"
    
    def clear_cache(self):
        """Clear weather cache"""
        self.cache.clear()
        logger.info("🗑️ Weather cache cleared")


# Global instance
weather_service = WeatherService()
