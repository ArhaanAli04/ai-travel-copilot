import asyncio
from datetime import date, timedelta
from app.services.weather_service import weather_service


async def test_weather():
    """Manual test of weather service"""
    print("🌤️ Testing Weather Service\n")
    
    # Test 1: Paris weather
    print("=" * 60)
    print("Test 1: Paris 7-day forecast")
    print("=" * 60)
    
    forecast = await weather_service.get_forecast(
        city="Paris",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=6)
    )
    
    if forecast:
        print(f"✅ City: {forecast.city}")
        print(f"✅ Coordinates: {forecast.latitude}, {forecast.longitude}")
        print(f"✅ Forecasts: {len(forecast.daily_forecasts)} days\n")
        
        for day in forecast.daily_forecasts:
            temp_str = weather_service.format_temperature(
                (day.temp_min + day.temp_max) / 2
            )
            print(f"  {day.date} {day.icon} {day.condition}")
            print(f"    Temp: {temp_str}")
            print(f"    Precipitation: {day.precipitation_probability:.0f}%\n")
    else:
        print("❌ Failed to fetch weather")
    
    # Test 2: Cache hit
    print("\n" + "=" * 60)
    print("Test 2: Cache hit (same request)")
    print("=" * 60)
    
    forecast2 = await weather_service.get_forecast(
        city="Paris",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=6)
    )
    
    if forecast2:
        print(f"✅ Cache age: {(forecast2.cached_at - forecast.cached_at).total_seconds()}s")
        print("✅ Should be 0 (cache hit)")
    
    # Test 3: Different city
    print("\n" + "=" * 60)
    print("Test 3: Tokyo weather")
    print("=" * 60)
    
    forecast3 = await weather_service.get_forecast(
        city="Tokyo",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=2)
    )
    
    if forecast3:
        print(f"✅ City: {forecast3.city}")
        print(f"✅ Days: {len(forecast3.daily_forecasts)}")


if __name__ == "__main__":
    asyncio.run(test_weather())
