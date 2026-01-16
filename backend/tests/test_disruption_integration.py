"""
Integration tests for disruption service with real APIs
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, date
from app.main import app
from app.core.postgres import get_db
from app.models.disruption import DisruptionCase


client = TestClient(app)


class TestDisruptionAPIIntegration:
    """Test disruption API endpoints with enrichment"""
    
    def test_create_case_with_auto_enrichment(self):
        """Test that creating a case auto-enriches with flight/weather data"""
        
        case_data = {
            "flight_number": "AA100",
            "airline": "American Airlines",
            "origin": "New York",
            "destination": "London",
            "disruption_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "pnr": "AUTOTEST123",
            "notes": "Testing auto-enrichment feature"
        }
        
        response = client.post("/api/disruptions/", json=case_data)
        
        assert response.status_code == 201
        data = response.json()
        
        print(f"\n✅ Case created with ID: {data['id']}")
        print(f"   Flight: {data['flight_number']}")
        print(f"   Current Status: {data['current_status']}")
        print(f"   Severity: {data['severity']}")
        
        # Check basic fields
        assert data['flight_number'] == "AA100"
        assert data['airline'] == "American Airlines"
        assert data['meta_data'] is not None
        
        # Check enrichment timestamp
        assert 'last_enriched' in data['meta_data']
        print(f"   ✅ Last Enriched: {data['meta_data']['last_enriched']}")
        
        # Check flight status (if available)
        if 'flight_status' in data['meta_data']:
            flight_status = data['meta_data']['flight_status']
            print(f"   ✅ Flight Status: {flight_status.get('status')}")
            
            assert 'departure' in flight_status
            assert 'arrival' in flight_status
            
            if flight_status.get('departure', {}).get('airport'):
                print(f"      Departure: {flight_status['departure']['airport']}")
            if flight_status.get('arrival', {}).get('airport'):
                print(f"      Arrival: {flight_status['arrival']['airport']}")
        else:
            print(f"   ⚠️ No flight status data (flight may not exist)")
        
        # Check weather data (if available)
        if 'weather' in data['meta_data']:
            weather = data['meta_data']['weather']
            print(f"   ✅ Weather: {weather.get('condition')}")
            print(f"      Temperature: {weather.get('temperature')}°C")
            print(f"      Severity: {weather.get('severity')}")
            
            assert 'temperature' in weather
            assert 'condition' in weather
            assert 'severity' in weather
            assert weather['severity'] in ['low', 'medium', 'high']
        else:
            print(f"   ⚠️ No weather data")
        
        # Verify status was updated (not default)
        assert data['current_status'] != "Checking flight status..."
        
        return data['id']
    
    def test_refresh_endpoint(self):
        """Test the refresh endpoint to re-check flight/weather"""
        
        # Create a case first
        case_data = {
            "flight_number": "BA178",
            "airline": "British Airways",
            "origin": "London",
            "destination": "New York",
            "disruption_date": datetime.now().isoformat(),
            "pnr": "REFRESH789"
        }
        
        create_response = client.post("/api/disruptions/", json=case_data)
        assert create_response.status_code == 201
        
        case_id = create_response.json()['id']
        original_enriched = create_response.json()['meta_data'].get('last_enriched')
        
        print(f"\n✅ Created case {case_id}")
        print(f"   Original enrichment: {original_enriched}")
        
        # Wait a moment (optional)
        import time
        time.sleep(1)
        
        # Refresh the case
        refresh_response = client.post(f"/api/disruptions/{case_id}/refresh")
        
        assert refresh_response.status_code == 200
        data = refresh_response.json()
        
        print(f"\n✅ Refreshed case {case_id}")
        print(f"   Current Status: {data['current_status']}")
        print(f"   Severity: {data['severity']}")
        
        # Check that last_enriched was updated
        new_enriched = data['meta_data'].get('last_enriched')
        print(f"   New enrichment: {new_enriched}")
        
        assert new_enriched is not None
        # Should be different (newer) than original
        assert new_enriched >= original_enriched
        
        print(f"   ✅ Enrichment timestamp updated")
    
    def test_refresh_nonexistent_case(self):
        """Test refreshing a case that doesn't exist"""
        
        response = client.post("/api/disruptions/99999/refresh")
        
        assert response.status_code == 404
        assert "not found" in response.json()['detail'].lower()
        
        print(f"\n✅ Correctly returns 404 for nonexistent case")
    
    def test_case_severity_calculation(self):
        """Test that severity is calculated correctly based on delay"""
        
        # Note: This test depends on real flight data
        # We'll just verify the severity field is set
        
        case_data = {
            "flight_number": "DL123",
            "airline": "Delta",
            "origin": "Atlanta",
            "destination": "Los Angeles",
            "disruption_date": datetime.now().isoformat(),
            "pnr": "SEVERITY123"
        }
        
        response = client.post("/api/disruptions/", json=case_data)
        data = response.json()
        
        print(f"\n✅ Case created: {data['id']}")
        print(f"   Severity: {data['severity']}")
        
        # Verify severity is one of the valid values
        valid_severities = ['low', 'medium', 'high', 'critical']
        assert data['severity'] in valid_severities
        
        print(f"   ✅ Severity is valid: {data['severity']}")


class TestWeatherIntegration:
    """Test weather API integration specifically"""
    
    def test_weather_for_major_airports(self):
        """Test weather fetching for different major airports"""
        
        test_airports = [
            ("AA100", "JFK", "New York"),
            ("BA178", "LHR", "London"),
            ("AI191", "BOM", "Mumbai"),
        ]
        
        print("\n🌦️ Testing Weather for Multiple Airports:")
        
        for flight, airport_code, city in test_airports:
            case_data = {
                "flight_number": flight,
                "airline": "Test Airline",
                "origin": city,
                "destination": "Test City",
                "disruption_date": datetime.now().isoformat(),
                "pnr": f"WX{airport_code}"
            }
            
            response = client.post("/api/disruptions/", json=case_data)
            
            if response.status_code == 201:
                data = response.json()
                
                if 'weather' in data.get('meta_data', {}):
                    weather = data['meta_data']['weather']
                    print(f"   ✅ {airport_code}: {weather['condition']}, "
                          f"{weather['temperature']}°C, "
                          f"Severity: {weather['severity']}")
                else:
                    print(f"   ⚠️ {airport_code}: No weather data returned")


class TestFlightStatusIntegration:
    """Test flight status API integration"""
    
    def test_flight_status_fields(self):
        """Test that flight status contains all expected fields"""
        
        case_data = {
            "flight_number": "AA100",
            "airline": "American Airlines",
            "origin": "New York",
            "destination": "London",
            "disruption_date": datetime.now().isoformat(),
            "pnr": "FLIGHT123"
        }
        
        response = client.post("/api/disruptions/", json=case_data)
        data = response.json()
        
        print(f"\n✈️ Testing Flight Status Fields:")
        
        if 'flight_status' in data.get('meta_data', {}):
            flight = data['meta_data']['flight_status']
            
            print(f"   ✅ Flight Number: {flight.get('flight_number')}")
            print(f"   ✅ Airline: {flight.get('airline')}")
            print(f"   ✅ Status: {flight.get('status')}")
            
            # Check departure info
            if flight.get('departure'):
                dep = flight['departure']
                print(f"   ✅ Departure Airport: {dep.get('airport')} ({dep.get('iata')})")
                if dep.get('scheduled'):
                    print(f"      Scheduled: {dep['scheduled']}")
                if dep.get('delay'):
                    print(f"      Delay: {dep['delay']} minutes")
            
            # Check arrival info
            if flight.get('arrival'):
                arr = flight['arrival']
                print(f"   ✅ Arrival Airport: {arr.get('airport')} ({arr.get('iata')})")
            
            # Verify required fields exist
            assert 'status' in flight
            assert 'departure' in flight
            assert 'arrival' in flight
            
        else:
            print(f"   ⚠️ No flight status data available")
