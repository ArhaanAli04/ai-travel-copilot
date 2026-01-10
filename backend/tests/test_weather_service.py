import pytest
from datetime import date, datetime
from app.services.weather_service import weather_service, WeatherService


@pytest.mark.asyncio
async def test_get_forecast():
    """Test fetching weather forecast"""
    service = WeatherService()
    
    # Test with Paris
    forecast = await service.get_forecast(
        city="Paris",
        start_date=date.today(),
        end_date=date.today()
    )
    
    assert forecast is not None
    assert forecast.city == "Paris"
    assert len(forecast.daily_forecasts) >= 1
    assert forecast.latitude is not None
    assert forecast.longitude is not None


@pytest.mark.asyncio
async def test_weather_caching():
    """Test 24-hour weather caching"""
    service = WeatherService()
    
    # First call - cache miss
    forecast1 = await service.get_forecast(
        city="Tokyo",
        start_date=date.today(),
        end_date=date.today()
    )
    
    # Second call - should hit cache
    forecast2 = await service.get_forecast(
        city="Tokyo",
        start_date=date.today(),
        end_date=date.today()
    )
    
    assert forecast1.cached_at == forecast2.cached_at  # Same cached object


@pytest.mark.asyncio
async def test_invalid_city():
    """Test handling of invalid city name"""
    service = WeatherService()
    
    forecast = await service.get_forecast(
        city="InvalidCityXYZ123",
        start_date=date.today(),
        end_date=date.today()
    )
    
    # Should return None for invalid city
    assert forecast is None


def test_weather_code_conversion():
    """Test weather code to condition/icon conversion"""
    service = WeatherService()
    
    # Test clear sky
    assert service._weather_code_to_condition(0) == "Clear sky"
    assert service._weather_code_to_icon(0) == "☀️"
    
    # Test rain
    assert service._weather_code_to_condition(61) == "Slight rain"
    assert service._weather_code_to_icon(61) == "🌧️"
    
    # Test snow
    assert service._weather_code_to_condition(71) == "Slight snow"
    assert service._weather_code_to_icon(71) == "❄️"


def test_temperature_formatting():
    """Test temperature formatting"""
    service = WeatherService()
    
    # Test Celsius + Fahrenheit
    formatted = service.format_temperature(20.0, include_fahrenheit=True)
    assert "20°C" in formatted
    assert "68°F" in formatted
    
    # Test Celsius only
    formatted = service.format_temperature(20.0, include_fahrenheit=False)
    assert "20°C" in formatted
    assert "°F" not in formatted


@pytest.mark.asyncio
async def test_get_day_weather():
    """Test extracting weather for specific date"""
    service = WeatherService()
    
    target_date = date.today()
    forecast = await service.get_forecast(
        city="London",
        start_date=target_date,
        end_date=target_date
    )
    
    if forecast:
        day_weather = service.get_day_weather(forecast, target_date)
        assert day_weather is not None
        assert day_weather.date == target_date
