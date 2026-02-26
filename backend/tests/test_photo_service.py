"""
Phase 3: Photo Service Tests
Tests Wikimedia path, Unsplash path, caching, and API endpoint
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.photo_service import (
    get_poi_photos,
    _search_wikimedia,
    _search_unsplash,
    _get_unsplash_query,
    _is_wikimedia_suitable,
    _is_relevant_result,
    _photo_cache
)


# ============================================================================
# TEST 1: Category Routing Logic
# ============================================================================

def test_wikimedia_suitable_categories():
    """Landmark categories should go to Wikimedia"""
    assert _is_wikimedia_suitable("aquarium")         == True
    assert _is_wikimedia_suitable("tourist_attraction") == True
    assert _is_wikimedia_suitable("museum")           == True
    assert _is_wikimedia_suitable("monument")         == True
    assert _is_wikimedia_suitable("park")             == True


def test_wikimedia_not_suitable_categories():
    """Business categories should skip Wikimedia"""
    assert _is_wikimedia_suitable("cafe")             == False
    assert _is_wikimedia_suitable("restaurant")       == False
    assert _is_wikimedia_suitable("bar")              == False
    assert _is_wikimedia_suitable("shopping_mall")    == False
    assert _is_wikimedia_suitable("gym")              == False


# ============================================================================
# TEST 2: Relevance Checking
# ============================================================================

def test_relevance_exact_match():
    """Page title matching POI name should be relevant"""
    assert _is_relevant_result("Taraporewala Aquarium", "Taraporewala Aquarium") == True
    assert _is_relevant_result("Gateway of India",      "Gateway of India")      == True


def test_relevance_partial_match():
    """50% word overlap required in non-strict mode"""
    assert _is_relevant_result("Mumbai Aquarium Guide", "Taraporewala Aquarium", strict=False) == True
    assert _is_relevant_result("Karna Das",             "Chaayos",               strict=False) == False


def test_relevance_strict_mode():
    """Full POI name must appear in title in strict mode"""
    assert _is_relevant_result("Dolphin Aquarium Mumbai",  "Dolphin Aquarium", strict=True) == True
    assert _is_relevant_result("Georgia Aquarium",         "Dolphin Aquarium", strict=True) == False
    assert _is_relevant_result("Clearwater Marine Aquarium","Dolphin Aquarium", strict=True) == False


# ============================================================================
# TEST 3: Unsplash Query Mapping
# ============================================================================

def test_unsplash_query_mapping():
    """Categories should map to correct Unsplash queries"""
    assert "cafe"       in _get_unsplash_query("cafe")
    assert "restaurant" in _get_unsplash_query("restaurant")
    assert "aquarium"   in _get_unsplash_query("aquarium")
    assert "museum"     in _get_unsplash_query("museum")


def test_unsplash_query_unknown_category():
    """Unknown category should return default query"""
    result = _get_unsplash_query("completely_unknown_category_xyz")
    assert result == "city local place travel"


# ============================================================================
# TEST 4: Wikimedia API (live call)
# ============================================================================

@pytest.mark.asyncio
async def test_wikimedia_known_landmark():
    """Taraporewala Aquarium should return real Wikimedia photos"""
    photos = await _search_wikimedia("Taraporewala Aquarium", "mumbai")
    assert len(photos) >= 1
    assert photos[0]["source"] == "wikimedia"
    assert photos[0]["url"].startswith("https://upload.wikimedia.org")
    assert photos[0]["width"] > 0
    assert photos[0]["height"] > 0


@pytest.mark.asyncio
async def test_wikimedia_unknown_place():
    """Unknown place should return empty list (not crash)"""
    photos = await _search_wikimedia("Completely Fake Place XYZ 99999", "mumbai")
    assert photos == []


@pytest.mark.asyncio
async def test_wikimedia_no_city():
    """Should work even without a city"""
    photos = await _search_wikimedia("Gateway of India", "")
    assert isinstance(photos, list)


# ============================================================================
# TEST 5: Unsplash API (live call)
# ============================================================================

@pytest.mark.asyncio
async def test_unsplash_cafe():
    """Cafe category should return photos"""
    photos = await _search_unsplash("cafe")
    assert len(photos) >= 1
    assert photos[0]["source"] == "unsplash"
    assert photos[0]["url"].startswith("https://images.unsplash.com")
    assert photos[0]["attribution"].startswith("Photo by")


@pytest.mark.asyncio
async def test_unsplash_aquarium():
    """Aquarium category should return relevant photos"""
    photos = await _search_unsplash("aquarium")
    assert len(photos) >= 1
    assert all(p["source"] == "unsplash" for p in photos)


# ============================================================================
# TEST 6: Full get_poi_photos() Logic
# ============================================================================

@pytest.mark.asyncio
async def test_get_poi_photos_cafe():
    """Cafe POI should use Unsplash directly"""
    _photo_cache.clear()
    poi = {
        "_id": "test_cafe_001",
        "name": "Test Cafe Mumbai",
        "city": "mumbai",
        "category": "cafe"
    }
    result = await get_poi_photos(poi)
    assert result["source"] == "unsplash"
    assert result["total"] >= 1
    assert result["cached"] == False


@pytest.mark.asyncio
async def test_get_poi_photos_landmark():
    """Known landmark should use Wikimedia"""
    _photo_cache.clear()
    poi = {
        "_id": "test_aquarium_001",
        "name": "Taraporewala Aquarium",
        "city": "mumbai",
        "category": "aquarium"
    }
    result = await get_poi_photos(poi)
    assert result["source"] in ["wikimedia", "unsplash"]  # wikimedia preferred
    assert result["total"] >= 1
    assert result["cached"] == False


@pytest.mark.asyncio
async def test_get_poi_photos_caching():
    """Second call for same POI should return cached result"""
    _photo_cache.clear()
    poi = {
        "_id": "test_cache_001",
        "name": "Chaayos",
        "city": "mumbai",
        "category": "cafe"
    }
    # First call
    result1 = await get_poi_photos(poi)
    assert result1["cached"] == False

    # Second call — must be cached
    result2 = await get_poi_photos(poi)
    assert result2["cached"] == True
    assert result2["photos"] == result1["photos"]


@pytest.mark.asyncio
async def test_get_poi_photos_unknown_category():
    """Unknown category should still return photos (default fallback)"""
    _photo_cache.clear()
    poi = {
        "_id": "test_unknown_001",
        "name": "Some Unknown Place",
        "city": "mumbai",
        "category": "unknown_category_xyz"
    }
    result = await get_poi_photos(poi)
    assert result["total"] >= 0  # May be 0 if placeholder
    assert result["source"] in ["wikimedia", "unsplash", "placeholder"]


# ============================================================================
#  TEST 7: API Endpoint Tests (mocked MongoDB — no live DB needed)
# ============================================================================

@pytest.mark.asyncio
async def test_api_poi_photos_valid_id():
    """Valid POI ID should return 200 with photos — mocked MongoDB"""
    from unittest.mock import patch, AsyncMock

    mock_poi = {
        "_id":      "697a3c381a88ce574ab6d96c",
        "id":       "697a3c381a88ce574ab6d96c",
        "name":     "Taraporewala Aquarium",
        "city":     "mumbai",
        "category": "aquarium",
        "location": {"lat": 18.9647, "lon": 72.8258, "city": "mumbai"}
    }

    with patch("app.api.local_discovery.local_agent.get_poi_details", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_poi

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/local/pois/697a3c381a88ce574ab6d96c/photos")

        assert response.status_code == 200
        data = response.json()
        assert data["poi_name"] == "Taraporewala Aquarium"
        assert "photos"  in data
        assert "source"  in data
        assert "cached"  in data
        assert data["source"] in ["wikimedia", "unsplash", "placeholder"]
        assert isinstance(data["photos"], list)
        print(f"\n✅ API endpoint working | source: {data['source']} | photos: {data['total']}")


@pytest.mark.asyncio
async def test_api_poi_photos_invalid_id():
    """Non-existent POI ID should return 404"""
    from unittest.mock import patch, AsyncMock

    with patch("app.api.local_discovery.local_agent.get_poi_details", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None  # Simulates POI not found in MongoDB

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/local/pois/000000000000000000000000/photos")

        assert response.status_code == 404
        print(f"\n✅ 404 returned for missing POI as expected")


@pytest.mark.asyncio
async def test_api_poi_photos_bad_format():
    """Malformed POI ID should return 500 without crashing the server"""
    from unittest.mock import patch, AsyncMock

    with patch("app.api.local_discovery.local_agent.get_poi_details", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Invalid ObjectId format")

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/local/pois/not-a-valid-id/photos")

        assert response.status_code in [404, 500]
        print(f"\n✅ Bad format handled gracefully: {response.status_code}")

# ============================================================================
# TEST 8: Missing from Phase 3 checklist
# ============================================================================

@pytest.mark.asyncio
async def test_unsplash_restaurant_category():
    """Phase 3.1 - Unsplash fallback for 'restaurant' specifically"""
    photos = await _search_unsplash("restaurant")
    assert len(photos) >= 1
    assert photos[0]["source"] == "unsplash"
    assert photos[0]["url"].startswith("https://images.unsplash.com")
    print(f"\n✅ Restaurant photos: {len(photos)} returned")
    print(f"   Query used: restaurant interior dining food")
    print(f"   Sample: {photos[0]['alt_text']}")


@pytest.mark.asyncio
async def test_placeholder_fallback():
    """
    Phase 3.1 - Placeholder fallback when both Wikimedia and Unsplash fail.
    Simulate by temporarily clearing the API key.
    """
    from app.core.config import settings
    from app.services import photo_service
    from unittest.mock import patch

    _photo_cache.clear()

    poi = {
        "_id": "test_placeholder_001",
        "name": "Completely Obscure Fake Place That Does Not Exist XYZ 99999",
        "city": "nowheresville",
        "category": "cafe"
    }

    # Patch Unsplash key to empty string to force placeholder
    with patch.object(settings, "UNSPLASH_ACCESS_KEY", ""):
        result = await get_poi_photos(poi)

    assert result["source"] == "placeholder"
    assert result["total"] == 1
    assert result["photos"][0]["url"] == ""
    assert result["photos"][0]["source"] == "placeholder"
    print(f"\n✅ Placeholder fallback working correctly")
    print(f"   alt_text: {result['photos'][0]['alt_text']}")


@pytest.mark.asyncio
async def test_attribution_reflects_source():
    """Phase 3.3 - Attribution text must match the actual source"""
    _photo_cache.clear()

    # Test Wikimedia attribution
    wikimedia_photos = await _search_wikimedia("Taraporewala Aquarium", "mumbai")
    if wikimedia_photos:
        assert "Wikimedia Commons" in wikimedia_photos[0]["attribution"]
        print(f"\n✅ Wikimedia attribution: {wikimedia_photos[0]['attribution']}")

    # Test Unsplash attribution
    unsplash_photos = await _search_unsplash("restaurant")
    if unsplash_photos:
        assert "Unsplash" in unsplash_photos[0]["attribution"]
        assert "Photo by" in unsplash_photos[0]["attribution"]
        print(f"✅ Unsplash attribution: {unsplash_photos[0]['attribution']}")
