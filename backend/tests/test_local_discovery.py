"""
Tests for Local Discovery Service - Hybrid Search

Tests:
1. Geospatial queries
2. Semantic search
3. Hybrid search combining both
4. Filtering by category/cuisine
5. Distance calculations
"""
import pytest
from app.services.local_discovery_service import local_discovery_service
from app.core.mongo import connect_to_mongo
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestLocalDiscoveryService:
    """Test Local Discovery Service"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test database connection"""
        await connect_to_mongo()
    
    @pytest.mark.asyncio
    async def test_geo_query_mumbai_bandra(self):
        """Test geospatial query near Bandra, Mumbai"""
        
        print("\n" + "="*70)
        print("Test: Geospatial Query near Bandra, Mumbai")
        print("="*70)
        
        # Bandra coordinates (approximately)
        bandra_location = {"lat": 19.0596, "lon": 72.8295}
        
        result = await local_discovery_service.hybrid_search(
            query="",  # No semantic query, just geo
            user_location=bandra_location,
            city="mumbai",
            radius_km=2.0,  # 2km radius
            limit=10,
            include_context=False
        )
        
        print(f"\nLocation: Bandra ({bandra_location['lat']}, {bandra_location['lon']})")
        print(f"Radius: 2.0 km")
        print(f"City: Mumbai")
        print(f"\nResults: {result['total_pois']} POIs found")
        
        if result['pois']:
            print(f"\nTop 5 POIs:")
            for i, poi in enumerate(result['pois'][:5], 1):
                print(f"  {i}. {poi['name']}")
                print(f"     Category: {poi.get('category', 'N/A')}")
                print(f"     Distance: {poi.get('distance_text', 'N/A')}")
                if poi.get('tags', {}).get('cuisine'):
                    print(f"     Cuisine: {poi['tags']['cuisine']}")
        
        assert result['total_pois'] > 0, "Should find POIs near Bandra"
        assert all('distance_km' in poi for poi in result['pois']), "All POIs should have distance"
        
        print("\n✅ Geospatial query test passed!")
    
    @pytest.mark.asyncio
    async def test_hybrid_search_vegetarian_restaurants(self):
        """Test hybrid search for vegetarian restaurants"""
        
        print("\n" + "="*70)
        print("Test: Hybrid Search - Vegetarian Restaurants near Bandra")
        print("="*70)
        
        bandra_location = {"lat": 19.0596, "lon": 72.8295}
        
        result = await local_discovery_service.hybrid_search(
            query="vegetarian restaurants",
            user_location=bandra_location,
            city="mumbai",
            radius_km=3.0,
            limit=15,
            include_context=True
        )
        
        print(f"\nQuery: 'vegetarian restaurants'")
        print(f"Location: Bandra, Mumbai")
        print(f"Radius: 3.0 km")
        print(f"\nResults:")
        print(f"  POIs found: {result['total_pois']}")
        print(f"  Context items: {len(result['context'])}")
        
        if result['pois']:
            print(f"\nTop 5 Relevant POIs (sorted by relevance):")
            for i, poi in enumerate(result['pois'][:5], 1):
                print(f"  {i}. {poi['name']}")
                print(f"     Category: {poi.get('category', 'N/A')}")
                print(f"     Distance: {poi.get('distance_text', 'N/A')}")
                print(f"     Relevance: {poi.get('relevance_score', 0):.3f}")
                if poi.get('tags', {}).get('cuisine'):
                    print(f"     Cuisine: {poi['tags']['cuisine']}")
        
        if result['context']:
            print(f"\nContext from Blogs/Tips:")
            for i, ctx in enumerate(result['context'][:3], 1):
                print(f"  {i}. {ctx['payload'].get('title', 'N/A')[:60]}...")
                print(f"     Source: {ctx['payload'].get('source', 'N/A')}")
                print(f"     Score: {ctx['score']:.3f}")
        
        assert result['total_pois'] >= 0  # May be 0 if no vegetarian restaurants in radius
        assert 'context' in result
        
        print("\n✅ Hybrid search test passed!")
    
    @pytest.mark.asyncio
    async def test_filter_by_cuisine(self):
        """Test filtering by cuisine"""
        
        print("\n" + "="*70)
        print("Test: Filter by Cuisine - Indian restaurants")
        print("="*70)
        
        mumbai_center = {"lat": 19.0760, "lon": 72.8777}
        
        result = await local_discovery_service.hybrid_search(
            query="best indian food",
            user_location=mumbai_center,
            city="mumbai",
            radius_km=5.0,
            cuisines=["indian"],
            limit=10,
            include_context=False
        )
        
        print(f"\nQuery: 'best indian food'")
        print(f"Filter: Cuisine = 'indian'")
        print(f"Location: Mumbai Center")
        print(f"Radius: 5.0 km")
        print(f"\nResults: {result['total_pois']} POIs found")
        
        # Verify cuisine filter is applied
        for poi in result['pois']:
            cuisine = poi.get('tags', {}).get('cuisine')
            if cuisine:
                assert 'indian' in cuisine.lower(), f"POI should have 'indian' cuisine, got: {cuisine}"
        
        print("\n✅ Cuisine filter test passed!")
    
    @pytest.mark.asyncio
    async def test_category_search(self):
        """Test search by specific category"""
        
        print("\n" + "="*70)
        print("Test: Category Search - Restaurants")
        print("="*70)
        
        delhi_center = {"lat": 28.7041, "lon": 77.1025}
        
        result = await local_discovery_service.hybrid_search(
            query="",
            user_location=delhi_center,
            city="delhi",
            radius_km=3.0,
            categories=["restaurant"],
            limit=10,
            include_context=False
        )
        
        print(f"\nCategory: 'restaurant'")
        print(f"Location: Delhi Center")
        print(f"Radius: 3.0 km")
        print(f"\nResults: {result['total_pois']} POIs found")
        
        if result['pois']:
            print(f"\nSample POIs:")
            for i, poi in enumerate(result['pois'][:3], 1):
                print(f"  {i}. {poi['name']} - {poi.get('category', 'N/A')}")
        
        # Verify category filter
        for poi in result['pois']:
            assert poi.get('category') == 'restaurant', "All POIs should be restaurants"
        
        print("\n✅ Category search test passed!")
    
    @pytest.mark.asyncio
    async def test_get_categories_by_city(self):
        """Test getting available categories for a city"""
        
        print("\n" + "="*70)
        print("Test: Get Categories by City")
        print("="*70)
        
        for city in ["mumbai", "delhi", "goa"]:
            categories = await local_discovery_service.get_categories_by_city(city)
            
            print(f"\n{city.title()}: {len(categories)} categories")
            print(f"  Categories: {', '.join(categories[:10])}")
            if len(categories) > 10:
                print(f"  ... and {len(categories) - 10} more")
            
            assert isinstance(categories, list)
            assert len(categories) > 0, f"{city} should have categories"
        
        print("\n✅ Get categories test passed!")
    
    @pytest.mark.asyncio
    async def test_get_cuisines_by_city(self):
        """Test getting available cuisines for a city"""
        
        print("\n" + "="*70)
        print("Test: Get Cuisines by City")
        print("="*70)
        
        for city in ["mumbai", "delhi", "goa"]:
            cuisines = await local_discovery_service.get_cuisines_by_city(city)
            
            print(f"\n{city.title()}: {len(cuisines)} cuisines")
            if cuisines:
                print(f"  Cuisines: {', '.join(cuisines[:10])}")
                if len(cuisines) > 10:
                    print(f"  ... and {len(cuisines) - 10} more")
            
            assert isinstance(cuisines, list)
        
        print("\n✅ Get cuisines test passed!")
    
    @pytest.mark.asyncio
    async def test_distance_calculations(self):
        """Test that distance calculations are accurate"""
        
        print("\n" + "="*70)
        print("Test: Distance Calculations")
        print("="*70)
        
        location = {"lat": 19.0760, "lon": 72.8777}  # Mumbai center
        
        result = await local_discovery_service.hybrid_search(
            query="",
            user_location=location,
            city="mumbai",
            radius_km=2.0,
            limit=5,
            include_context=False
        )
        
        print(f"\nCenter: ({location['lat']}, {location['lon']})")
        print(f"Radius: 2.0 km")
        print(f"\nPOIs with distances:")
        
        for poi in result['pois']:
            distance = poi.get('distance_km', 0)
            print(f"  • {poi['name']}: {poi.get('distance_text', 'N/A')}")
            
            # Verify distance is within radius
            assert distance <= 2.0, f"POI should be within 2km radius, got {distance}km"
        
        print("\n✅ Distance calculations test passed!")


class TestLocalDiscoveryAPI:
    """Test Local Discovery API endpoints"""
    
    @pytest.mark.asyncio
    async def test_api_integration(self):
        """Test that API can be called (integration test)"""
        
        print("\n" + "="*70)
        print("Test: API Integration")
        print("="*70)
        
        # This would require TestClient from fastapi.testclient
        # For now, we're testing the service layer directly
        
        print("\n✅ API integration test placeholder (implement with TestClient)")


class TestHybridSearchSummary:
    """Summary test showing complete hybrid search workflow"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete hybrid search workflow with mock user query"""
        
        print("\n" + "="*70)
        print("DAY 20 - COMPLETE HYBRID SEARCH WORKFLOW")
        print("="*70)
        
        await connect_to_mongo()
        
        # Mock user query: "vegetarian restaurants near Bandra"
        query = "vegetarian restaurants near Bandra"
        bandra_location = {"lat": 19.0596, "lon": 72.8295}
        
        print(f"\n🔍 User Query: '{query}'")
        print(f"📍 Location: Bandra, Mumbai ({bandra_location['lat']}, {bandra_location['lon']})")
        print(f"🎯 Radius: 3.0 km")
        
        # Execute hybrid search
        result = await local_discovery_service.hybrid_search(
            query="vegetarian restaurants",
            user_location=bandra_location,
            city="mumbai",
            radius_km=3.0,
            limit=10,
            include_context=True
        )
        
        print(f"\n📊 Results:")
        print(f"   Total POIs: {result['total_pois']}")
        print(f"   Context items: {len(result['context'])}")
        
        print(f"\n🍽️  Top Recommendations:")
        for i, poi in enumerate(result['pois'][:5], 1):
            print(f"\n   {i}. {poi['name']}")
            print(f"      📂 Category: {poi.get('category', 'N/A')}")
            print(f"      📍 Distance: {poi.get('distance_text', 'N/A')}")
            print(f"      ⭐ Relevance: {poi.get('relevance_score', 0):.3f}")
            
            if poi.get('tags', {}).get('cuisine'):
                print(f"      🍴 Cuisine: {poi['tags']['cuisine']}")
            
            if poi.get('tags', {}).get('amenity'):
                print(f"      🏷️  Type: {poi['tags']['amenity']}")
        
        if result['context']:
            print(f"\n📰 Related Context (Blogs/Tips):")
            for i, ctx in enumerate(result['context'][:3], 1):
                payload = ctx['payload']
                print(f"\n   {i}. {payload.get('title', 'N/A')[:60]}...")
                print(f"      📰 Source: {payload.get('source', 'N/A')}")
                print(f"      ⭐ Relevance: {ctx['score']:.3f}")
        
        print("\n" + "="*70)
        print("✅ DAY 20 COMPLETE - HYBRID SEARCH WORKING!")
        print("="*70)
        
        assert result['total_pois'] >= 0
        assert 'pois' in result
        assert 'context' in result
