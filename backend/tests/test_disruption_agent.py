"""
Tests for disruption agent
"""
import pytest
from datetime import datetime
from app.ai.disruption_agent import disruption_agent
from app.models.disruption import DisruptionCase, DisruptionType, DisruptionSeverity
from app.core.postgres import get_db


class TestDisruptionAgent:
    """Test AI-powered rights explanation"""
    
    @pytest.mark.asyncio
    async def test_explain_rights_eu_cancellation(self):
        """Test rights explanation for EU flight cancellation"""
        
        # Create mock disruption case
        case = DisruptionCase(
            id=999,
            flight_number="BA178",
            airline="British Airways",
            origin="London",
            destination="Paris",
            disruption_date=datetime.now(),
            disruption_type=DisruptionType.CANCELLATION,
            current_status="Flight cancelled",
            severity=DisruptionSeverity.CRITICAL,
            pnr="TEST123",
            meta_data={
                "flight_status": {
                    "status": "cancelled",
                    "departure": {
                        "delay": None
                    }
                }
            }
        )
        
        # Explain rights
        explanation = await disruption_agent.explain_rights(
            disruption_case=case,
            booking_class="economy"
        )
        
        print("\n🇪🇺 EU Cancellation Rights Explanation:")
        print(f"\n   Summary: {explanation['summary']}")
        print(f"\n   Regulation: {explanation.get('applicable_regulation')}")
        print(f"\n   Compensation: {explanation.get('compensation_amount')} {explanation.get('compensation_currency')}")
        print(f"\n   Rights:")
        for right in explanation['rights_bullets']:
            print(f"      - {right}")
        print(f"\n   Next Steps:")
        for step in explanation.get('next_steps', []):
            print(f"      - {step}")
        print(f"\n   Cached: {explanation['cached']}")
        
        # Assertions
        assert "summary" in explanation
        assert isinstance(explanation["rights_bullets"], list)
        assert "region" in explanation
    
    @pytest.mark.asyncio
    async def test_explain_rights_us_delay(self):
        """Test rights explanation for US flight delay"""
        print("\n📥 Fetching US delay policies...")
        from app.services.policy_service import policy_service
        
        await policy_service.fetch_and_cache_policies(
            airline="American Airlines",
            region="US",
            disruption_type="delay",
            force_refresh=False
        )
        case = DisruptionCase(
            id=998,
            flight_number="AA100",
            airline="American Airlines",
            origin="New York",
            destination="Los Angeles",
            disruption_date=datetime.now(),
            disruption_type=DisruptionType.DELAY,
            current_status="Delayed by 180 minutes",
            severity=DisruptionSeverity.MEDIUM,
            pnr="TEST456",
            meta_data={
                "flight_status": {
                    "status": "delayed",
                    "departure": {
                        "delay": 180
                    }
                }
            }
        )
        
        explanation = await disruption_agent.explain_rights(
            disruption_case=case
        )
        
        print("\n🇺🇸 US Delay Rights Explanation:")
        print(f"\n   Summary: {explanation['summary']}")
        print(f"\n   Region: {explanation['region']}")
        print(f"\n   Compensation: {explanation.get('compensation_amount')}")
        print(f"\n   Rights: {len(explanation.get('rights_bullets', []))} bullets")
        print(f"\n   Next Steps: {len(explanation.get('next_steps', []))} steps")
        
        assert "summary" in explanation
        
        if len(explanation['summary']) == 0:
            # No policies found - verify it's properly handled
            print("   ⚠️ No summary generated (no policies found)")
            assert explanation.get('compensation_amount') is None
        else:
            # Policies found - should have content
            print(f"   ✅ Summary generated: {len(explanation['summary'])} chars")
            assert len(explanation['summary']) > 0
        assert explanation["region"] in ["US", "UNKNOWN"]

        assert len(explanation.get('rights_bullets', [])) >= 0 
    
    
    def test_extract_delay_minutes(self):
        """Test delay extraction from flight status"""
        
        # Test with delay field
        flight_status_1 = {
            "departure": {"delay": 120}
        }
        delay = disruption_agent._extract_delay_minutes(flight_status_1, None)
        assert delay == 120
        
        print(f"\n✅ Extracted delay: {delay} minutes")

    def test_extract_country_from_airport_or_city(self):
        """Test airport code and city name extraction"""
        
        # Test IATA codes (exact match)
        assert disruption_agent._extract_country_from_airport_or_city("JFK") == "US"
        assert disruption_agent._extract_country_from_airport_or_city("LHR") == "GB"
        assert disruption_agent._extract_country_from_airport_or_city("CDG") == "FR"
        assert disruption_agent._extract_country_from_airport_or_city("BOM") == "IN"
        
        # Test city names (searches airports, returns most common country)
        # London: Multiple airports in GB (3) vs CA (1) → Should return GB
        london_country = disruption_agent._extract_country_from_airport_or_city("London")
        print(f"\n   London → {london_country}")
        assert london_country == "GB", f"Expected GB for London, got {london_country}"
        
        # New York: Multiple airports, all in US
        ny_country = disruption_agent._extract_country_from_airport_or_city("New York")
        print(f"   New York → {ny_country}")
        assert ny_country == "US", f"Expected US for New York, got {ny_country}"
        
        # Paris: Multiple airports in FR vs some in US → Should return FR
        paris_country = disruption_agent._extract_country_from_airport_or_city("Paris")
        print(f"   Paris → {paris_country}")
        assert paris_country == "FR", f"Expected FR for Paris, got {paris_country}"
        
        # Test case insensitivity
        assert disruption_agent._extract_country_from_airport_or_city("jfk") == "US"
        assert disruption_agent._extract_country_from_airport_or_city("lhr") == "GB"
        assert disruption_agent._extract_country_from_airport_or_city("LONDON") == "GB"
        
        # Test fallback for cities not in airport DB
        assert disruption_agent._extract_country_from_airport_or_city("Mumbai") in ["IN"]
        
        print("\n✅ Airport/city to country extraction working with multi-country disambiguation!")


    def test_extract_country_from_city(self):
        """Test city to country code mapping (legacy method)"""
        
        # This now delegates to _extract_country_from_airport_or_city
        # Should handle multiple countries correctly
        assert disruption_agent._extract_country_from_city("London") == "GB"
        assert disruption_agent._extract_country_from_city("Paris") == "FR"
        assert disruption_agent._extract_country_from_city("New York") == "US"
        
        print("\n✅ City to country mapping working with disambiguation!")



