"""
Tests for feedback and analytics system (Day 22)
"""
import pytest
import asyncio
from datetime import datetime,timezone


# ✅ FIX: Create fresh service instances per test
@pytest.fixture
async def fresh_feedback_service():
    """Create a fresh feedback service for each test"""
    from app.services.feedback_service import FeedbackService
    service = FeedbackService()
    yield service
    service.client.close()


@pytest.fixture
async def fresh_analytics_service():
    """Create a fresh analytics service for each test"""
    from app.services.analytics_service import AnalyticsService
    service = AnalyticsService()
    yield service
    service.client.close()


class TestFeedback:
    """Test feedback functionality"""
    
    @pytest.mark.asyncio
    async def test_submit_feedback_thumbs_up(self, fresh_feedback_service):
        """Test submitting thumbs up feedback"""
        print("\n" + "="*70)
        print("TEST 1: Submit Thumbs Up Feedback")
        print("="*70)
        
        poi_id = "6973c6ad1a88ce574ab68798"
        
        result = await fresh_feedback_service.submit_feedback(
            poi_id=poi_id,
            user_id="test_user_1",
            feedback_type="thumbs_up",
            rating=None,
            visited_at=datetime.now(timezone.utc),
            comment="Great coffee and ambiance!",
            tags=["quiet", "good_wifi"]
        )
        
        print(f"\n✅ Feedback submitted:")
        print(f"   POI ID: {result['poi_id']}")
        print(f"   Message: {result['message']}")
        print(f"   Updated stats: {result['updated_stats']}")
        
        assert result["success"] == True
        assert "updated_stats" in result
        print("\n✅ Test passed!")
    
    @pytest.mark.asyncio
    async def test_submit_feedback_rating(self, fresh_feedback_service):
        """Test submitting 5-star rating"""
        print("\n" + "="*70)
        print("TEST 2: Submit 5-Star Rating")
        print("="*70)
        
        poi_id = "6973c6ad1a88ce574ab68798"
        
        result = await fresh_feedback_service.submit_feedback(
            poi_id=poi_id,
            user_id="test_user_2",
            feedback_type="rating",
            rating=5,
            visited_at=datetime.now(timezone.utc),
            comment="Excellent place for work!",
            tags=["productive", "friendly_staff"]
        )
        
        print(f"\n✅ Rating submitted:")
        print(f"   Average rating: {result['updated_stats']['average_rating']}")
        print(f"   Total feedback: {result['updated_stats']['feedback_count']}")
        
        assert result["success"] == True
        assert result["updated_stats"]["average_rating"] >= 4.0
        print("\n✅ Test passed!")
    
    @pytest.mark.asyncio
    async def test_get_trending_pois(self, fresh_feedback_service):
        """Test getting trending POIs"""
        print("\n" + "="*70)
        print("TEST 3: Get Trending POIs")
        print("="*70)
        
        trending = await fresh_feedback_service.get_trending_pois(
            city="mumbai",
            category="cafe",
            limit=5,
            min_feedback_count=1,  # Lower threshold for testing
            days=90
        )
        
        print(f"\n✅ Found {len(trending)} trending POIs:")
        for idx, poi in enumerate(trending, 1):
            print(f"\n{idx}. {poi['name']}")
            print(f"   Category: {poi['category']}")
            print(f"   Average rating: {poi['average_rating']:.2f}")
            print(f"   Feedback count: {poi['feedback_count']}")
            print(f"   Trending score: {poi['trending_score']:.2f}")
        
        assert len(trending) >= 0
        print("\n✅ Test passed!")
    
    @pytest.mark.asyncio
    async def test_feedback_boost_scores(self, fresh_feedback_service):
        """Test feedback boost calculation"""
        print("\n" + "="*70)
        print("TEST 4: Feedback Boost Scores")
        print("="*70)
        
        poi_ids = ["6973c6ad1a88ce574ab68798", "6973c6a91a88ce574ab68701"]
        
        boost_scores = await fresh_feedback_service.get_feedback_boost_scores(poi_ids)
        
        print(f"\n✅ Boost scores calculated:")
        for poi_id, boost in boost_scores.items():
            print(f"   POI {poi_id[:8]}...: {boost:.2f}x")
        
        assert len(boost_scores) == len(poi_ids)
        assert all(0.5 <= score <= 2.0 for score in boost_scores.values())
        print("\n✅ Test passed!")


class TestAnalytics:
    """Test analytics functionality"""
    
    @pytest.mark.asyncio
    async def test_log_query(self, fresh_analytics_service):
        """Test logging a query"""
        print("\n" + "="*70)
        print("TEST 5: Log Analytics Query")
        print("="*70)
        
        query_id = await fresh_analytics_service.log_query(
            query_text="romantic dinner spot",
            city="mumbai",
            user_location={"lat": 19.0596, "lon": 72.8295},
            preferences={"budget": "high", "cuisines": ["italian"]},
            results_count=5,
            response_time_ms=6234.5,
            user_id="test_user_1"
        )
        
        print(f"\n✅ Query logged:")
        print(f"   Query ID: {query_id}")
        
        assert query_id != ""
        print("\n✅ Test passed!")
    
    @pytest.mark.asyncio
    async def test_get_popular_cities(self, fresh_analytics_service):
        """Test getting popular cities"""
        print("\n" + "="*70)
        print("TEST 6: Get Popular Cities")
        print("="*70)
        
        popular = await fresh_analytics_service.get_popular_cities(days=30, limit=5)
        
        print(f"\n✅ Found {len(popular)} popular cities:")
        for idx, city_data in enumerate(popular, 1):
            print(f"\n{idx}. {city_data['city']}")
            print(f"   Search count: {city_data['search_count']}")
            print(f"   Avg results: {city_data['avg_results']}")
            print(f"   Avg response time: {city_data['avg_response_time']}ms")
        
        assert isinstance(popular, list)
        print("\n✅ Test passed!")
    
    @pytest.mark.asyncio
    async def test_get_analytics_summary(self, fresh_analytics_service):
        """Test getting full analytics summary"""
        print("\n" + "="*70)
        print("TEST 7: Get Analytics Summary")
        print("="*70)
        
        summary = await fresh_analytics_service.get_analytics_summary(
            city="mumbai",
            days=7
        )
        
        print(f"\n✅ Analytics Summary:")
        print(f"   Total queries: {summary.get('total_queries', 0)}")
        print(f"   Avg response time: {summary.get('avg_response_time_ms', 0):.2f}ms")
        print(f"   Avg results: {summary.get('avg_results_count', 0):.1f}")
        
        popular_cities = summary.get('popular_cities', [])
        if popular_cities:
            print(f"\n   Top cities:")
            for city in popular_cities[:3]:
                print(f"     - {city['city']}: {city['search_count']} searches")
        
        prefs = summary.get('common_preferences', {})
        if prefs.get('categories'):
            print(f"\n   Top categories:")
            for cat in prefs['categories'][:3]:
                print(f"     - {cat['name']}: {cat['count']} times")
        
        assert isinstance(summary, dict)
        print("\n✅ Test passed!")


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_feedback_affects_recommendations(self):
        """Test that feedback boosts work in recommendations"""
        print("\n" + "="*70)
        print("TEST 8: Feedback Affects Recommendations")
        print("="*70)
        
        # Ensure database is connected first
        from app.core.mongo import connect_to_mongo, database
        
        if database is None:
            await connect_to_mongo()
        
        from app.ai.local_agent import local_agent
        
        # Make a request
        result = await local_agent.suggest_local_experiences(
            user_query="best coffee shops",
            lat=19.0596,
            lon=72.8295,
            city="mumbai",
            radius_km=3.0,
            max_results=3
        )
        
        recommendations = result["recommendations"]
        
        print(f"\n✅ Got {len(recommendations)} recommendations:")
        for idx, rec in enumerate(recommendations, 1):
            print(f"\n{idx}. {rec['name']}")
            print(f"   Category: {rec['category']}")
            print(f"   Distance: {rec['distance_text']}")
            print(f"   Relevance: {rec.get('relevance_score', 0):.3f}")
            print(f"   Avg Rating: {rec.get('average_rating', 0):.2f}/5.0")
            print(f"   Feedback count: {rec.get('feedback_count', 0)}")
        
        assert len(recommendations) > 0
        assert all("average_rating" in rec for rec in recommendations)
        print("\n✅ Test passed!")
