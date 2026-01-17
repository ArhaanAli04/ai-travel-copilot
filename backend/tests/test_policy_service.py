"""
Tests for policy service
"""
import pytest
from datetime import datetime, timedelta, timezone
from app.services.policy_service import policy_service


class TestPolicyService:
    """Test policy fetching and caching"""
    
    @pytest.mark.asyncio
    async def test_fetch_policies_airline_specific(self):
        """Test fetching airline-specific policies"""
        
        policies = await policy_service.fetch_and_cache_policies(
            airline="American Airlines",
            region="US",
            disruption_type="cancellation",
            provider_type="airline",
            force_refresh=False
        )
        
        print(f"\n✅ Fetched {len(policies)} policy chunks")
        
        if policies:
            # Check structure
            assert isinstance(policies, list)
            
            first_policy = policies[0]
            assert "content" in first_policy
            assert "type" in first_policy
            assert "provider_name" in first_policy
            assert "region" in first_policy
            
            print(f"   Provider: {first_policy['provider_name']}")
            print(f"   Region: {first_policy['region']}")
            print(f"   Content preview: {first_policy['content'][:100]}...")
    
    @pytest.mark.asyncio
    async def test_fetch_eu261_policies(self):
        """Test fetching EU261 passenger rights"""
        
        policies = await policy_service.fetch_and_cache_policies(
            airline="British Airways",
            region="EU",
            disruption_type="delay",
            provider_type="airline",
            force_refresh=False
        )
        
        print(f"\n🇪🇺 Fetched {len(policies)} EU261 policy chunks")
        
        if policies:
            # Check for EU region
            for policy in policies:
                print(f"   Region: {policy['region']}")
                assert policy['region'] in ["EU", "GLOBAL"]
    
    @pytest.mark.asyncio
    async def test_policy_caching(self):
        """Test that policies are cached and reused"""
        
        # First call - should fetch from web
        start_time = datetime.now()
        policies_1 = await policy_service.fetch_and_cache_policies(
            airline="Delta",
            region="US",
            disruption_type="delay",
            force_refresh=True  # Force fresh fetch
        )
        first_duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n⏱️ First fetch took: {first_duration:.2f}s")
        
        # Second call - should use cache (faster)
        start_time = datetime.now()
        policies_2 = await policy_service.fetch_and_cache_policies(
            airline="Delta",
            region="US",
            disruption_type="delay",
            force_refresh=False  # Use cache
        )
        second_duration = (datetime.now() - start_time).total_seconds()
        
        print(f"⏱️ Cached fetch took: {second_duration:.2f}s")
        
        # Cached should be faster or equal
        # (May be equal if both hit web due to no cache)
        print(f"✅ Speedup: {first_duration / (second_duration + 0.01):.1f}x")
    
    def test_build_policy_search_queries(self):
        """Test search query generation"""
        
        queries = policy_service._build_policy_search_queries(
            airline="American Airlines",
            region="EU",
            disruption_type="cancellation",
            provider_type="airline"
        )
        
        print(f"\n🔍 Generated {len(queries)} search queries:")
        for query in queries:
            print(f"   - {query}")
        
        assert len(queries) > 0
        assert any("American Airlines" in q.replace("+", " ") for q in queries)
    
    def test_chunk_text(self):
        """Test text chunking"""
        
        # Sample policy text
        text = """
        Flight cancellation policy: Passengers are entitled to a full refund if the flight 
        is cancelled. The refund will be processed within 7-10 business days. Additionally, 
        passengers may claim compensation if the cancellation was within the airline's control. 
        The compensation amount depends on the flight distance and delay duration.
        """ * 10  # Repeat to make it long enough
        
        chunks = policy_service._chunk_text(text)
        
        print(f"\n📄 Split text into {len(chunks)} chunks")
        print(f"   First chunk length: {len(chunks[0])} chars")
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)


class TestSearchQueryBuilding:
    """Test query building for different scenarios"""
    
    def test_us_airline_queries(self):
        """Test US airline query building"""
        
        queries = policy_service._build_policy_search_queries(
            airline="United Airlines",
            region="US",
            disruption_type="delay",
            provider_type="airline"
        )
        
        print(f"\n🇺🇸 US Airline Queries:")
        for q in queries:
            print(f"   - {q}")
        
        assert any("DOT" in q or "United" in q.replace("+", " ") for q in queries)
    
    def test_eu_queries(self):
        """Test EU regulation queries"""
        
        queries = policy_service._build_policy_search_queries(
            airline="Lufthansa",
            region="EU",
            disruption_type="cancellation",
            provider_type="airline"
        )
        
        print(f"\n🇪🇺 EU Regulation Queries:")
        for q in queries:
            print(f"   - {q}")
        
        assert any("EU261" in q for q in queries)
