"""
Tests for disruption service
"""
import pytest
from datetime import date, datetime
from app.services.disruption_service import disruption_service


class TestAirportCoordinates:
    """Test airport coordinates lookup"""
    
    def test_load_airports_database(self):
        """Test that airports database is loaded successfully"""
        assert disruption_service.airports_db is not None
        assert len(disruption_service.airports_db) > 0
        print(f"\n✅ Loaded {len(disruption_service.airports_db)} airports")
    
    def test_get_coordinates_valid_airport(self):
        """Test getting coordinates for valid airport codes"""
        # Test JFK (New York)
        jfk = disruption_service._get_airport_coordinates("JFK")
        assert jfk is not None
        assert "lat" in jfk
        assert "lon" in jfk
        assert jfk["lat"] is not None
        assert jfk["lon"] is not None
        assert isinstance(jfk["lat"], (int, float))
        assert isinstance(jfk["lon"], (int, float))
        print(f"\n✅ JFK coordinates: {jfk}")
    
    def test_get_coordinates_multiple_airports(self):
        """Test multiple major airports"""
        test_airports = {
            "JFK": {"name": "New York JFK", "expected_lat_range": (40, 41)},
            "LAX": {"name": "Los Angeles", "expected_lat_range": (33, 34)},
            "LHR": {"name": "London Heathrow", "expected_lat_range": (51, 52)},
            "BOM": {"name": "Mumbai", "expected_lat_range": (19, 20)},
            "DEL": {"name": "Delhi", "expected_lat_range": (28, 29)},
            "DXB": {"name": "Dubai", "expected_lat_range": (25, 26)},
        }
        
        print("\n📍 Testing Multiple Airports:")
        for code, info in test_airports.items():
            coords = disruption_service._get_airport_coordinates(code)
            
            assert coords is not None, f"Airport {code} not found"
            assert "lat" in coords
            assert "lon" in coords
            
            # Verify latitude is in expected range
            lat = coords["lat"]
            expected_range = info["expected_lat_range"]
            assert expected_range[0] <= lat <= expected_range[1], \
                f"{code} latitude {lat} not in expected range {expected_range}"
            
            print(f"  ✅ {code} ({info['name']}): lat={coords['lat']}, lon={coords['lon']}")
    
    def test_get_coordinates_case_insensitive(self):
        """Test that airport lookup is case-insensitive"""
        jfk_upper = disruption_service._get_airport_coordinates("JFK")
        jfk_lower = disruption_service._get_airport_coordinates("jfk")
        jfk_mixed = disruption_service._get_airport_coordinates("jFk")
        
        assert jfk_upper == jfk_lower == jfk_mixed
        print(f"\n✅ Case-insensitive lookup working: {jfk_upper}")
    
    def test_get_coordinates_invalid_airport(self):
        """Test getting coordinates for invalid airport code"""
        invalid = disruption_service._get_airport_coordinates("INVALID")
        assert invalid is None
        print("\n✅ Invalid airport returns None")
    
    def test_get_coordinates_empty_string(self):
        """Test empty airport code"""
        empty = disruption_service._get_airport_coordinates("")
        assert empty is None
        print("\n✅ Empty airport code returns None")
    
    def test_coordinates_values_are_valid(self):
        """Test that coordinates are within valid ranges"""
        coords = disruption_service._get_airport_coordinates("JFK")
        
        assert coords is not None
        
        # Latitude must be between -90 and 90
        assert -90 <= coords["lat"] <= 90, "Latitude out of valid range"
        
        # Longitude must be between -180 and 180
        assert -180 <= coords["lon"] <= 180, "Longitude out of valid range"
        
        print(f"\n✅ Coordinates within valid ranges: {coords}")
    
    def test_indian_airports(self):
        """Test Indian airports specifically"""
        indian_airports = ["BOM", "DEL", "BLR", "MAA", "HYD", "CCU", "GOI"]
        
        print("\n🇮🇳 Testing Indian Airports:")
        for code in indian_airports:
            coords = disruption_service._get_airport_coordinates(code)
            
            if coords:  # Some might not be in database
                # Indian airports should have lat between 8-35 and lon between 68-97
                assert 8 <= coords["lat"] <= 35, f"{code} not in India latitude range"
                assert 68 <= coords["lon"] <= 97, f"{code} not in India longitude range"
                
                print(f"  ✅ {code}: lat={coords['lat']}, lon={coords['lon']}")
            else:
                print(f"  ⚠️ {code}: Not found in database")


class TestFlightStatus:
    """Test flight status API integration"""
    
    @pytest.mark.asyncio
    async def test_check_flight_status_structure(self):
        """Test that flight status returns correct structure"""
        # Using a common flight number (might not have real-time data)
        result = await disruption_service.check_flight_status(
            flight_number="AA100",
            flight_date=date.today()
        )
        
        # Result can be None if flight not found (that's okay)
        if result:
            assert "flight_number" in result
            assert "status" in result
            assert "departure" in result
            assert "arrival" in result
            assert "fetched_at" in result
            
            # Check departure structure
            assert "airport" in result["departure"]
            assert "scheduled" in result["departure"]
            
            print(f"\n✅ Flight status structure valid: {result['flight_number']}")
            print(f"   Status: {result['status']}")
        else:
            print("\n⚠️ No flight data returned (expected for test flight number)")


class TestWeatherAlerts:
    """Test weather API integration"""
    
    @pytest.mark.asyncio
    async def test_check_weather_alerts_structure(self):
        """Test that weather alerts return correct structure"""
        result = await disruption_service.check_weather_alerts(
            airport_code="JFK",
            check_date=date.today()
        )
        
        if result:
            assert "airport_code" in result
            assert "temperature" in result
            assert "condition" in result
            assert "severity" in result
            assert "fetched_at" in result
            
            # Check severity is valid
            assert result["severity"] in ["low", "medium", "high"]
            
            print(f"\n✅ Weather data structure valid for JFK")
            print(f"   Temperature: {result['temperature']}°C")
            print(f"   Condition: {result['condition']}")
            print(f"   Severity: {result['severity']}")
        else:
            print("\n⚠️ No weather data returned")
    
    @pytest.mark.asyncio
    async def test_check_weather_for_multiple_airports(self):
        """Test weather for different airports"""
        airports = ["JFK", "BOM", "LHR"]
        
        print("\n🌦️ Testing Weather for Multiple Airports:")
        for code in airports:
            result = await disruption_service.check_weather_alerts(
                airport_code=code,
                check_date=date.today()
            )
            
            if result:
                print(f"  ✅ {code}: {result['condition']}, {result['temperature']}°C")
            else:
                print(f"  ⚠️ {code}: No weather data")


class TestHelperMethods:
    """Test helper methods"""
    
    def test_weather_code_to_condition(self):
        """Test weather code conversion"""
        # Test clear weather
        assert disruption_service._weather_code_to_condition(1000) == "Clear"
        
        # Test cloudy
        assert disruption_service._weather_code_to_condition(1001) == "Cloudy"
        
        # Test rain
        assert disruption_service._weather_code_to_condition(4001) == "Rain"
        
        # Test thunderstorm
        assert disruption_service._weather_code_to_condition(8000) == "Thunderstorm"
        
        # Test unknown
        assert disruption_service._weather_code_to_condition(9999) == "Unknown"
        
        print("\n✅ Weather code conversion working")
    
    def test_determine_weather_severity(self):
        """Test weather severity calculation"""
        # High severity: Heavy rain
        high_severity = disruption_service._determine_weather_severity({
            "weatherCode": 4201,  # Heavy rain
            "windSpeed": 10,
            "visibility": 5,
            "precipitationProbability": 50
        })
        assert high_severity == "high"
        
        # Medium severity: Moderate rain
        medium_severity = disruption_service._determine_weather_severity({
            "weatherCode": 4001,  # Rain
            "windSpeed": 18,
            "visibility": 4,
            "precipitationProbability": 75
        })
        assert medium_severity == "medium"
        
        # Low severity: Clear
        low_severity = disruption_service._determine_weather_severity({
            "weatherCode": 1000,  # Clear
            "windSpeed": 5,
            "visibility": 10,
            "precipitationProbability": 10
        })
        assert low_severity == "low"
        
        print("\n✅ Weather severity calculation working")
    
    def test_calculate_severity_from_delay(self):
        """Test disruption severity from delay"""
        from app.models.disruption import DisruptionSeverity
        
        # Low: < 2 hours
        assert disruption_service._calculate_severity_from_delay(60) == DisruptionSeverity.LOW
        
        # Medium: 2-4 hours
        assert disruption_service._calculate_severity_from_delay(180) == DisruptionSeverity.MEDIUM
        
        # High: 4-8 hours
        assert disruption_service._calculate_severity_from_delay(300) == DisruptionSeverity.HIGH
        
        # Critical: > 8 hours
        assert disruption_service._calculate_severity_from_delay(500) == DisruptionSeverity.CRITICAL
        
        print("\n✅ Delay severity calculation working")
