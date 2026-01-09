"""
API integration tests for Day 5 - Travel Guides with RAG Caching
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_guide_search():
    """Test guide search with caching"""
    print("=" * 60)
    print("🧪 Test 1: Search for Paris food guides")
    print("=" * 60)
    
    # First request (should fetch from web)
    response = requests.post(
        f"{BASE_URL}/guides/search",
        json={
            "city": "Paris",
            "themes": ["food"],
            "force_refresh": False
        }
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Cache Hit: {data['cache_hit']}")
    print(f"Total Chunks: {data['total_chunks']}")
    print(f"Sources: {len(data['sources'])}")
    print(f"\nFirst chunk preview:")
    if data['chunks']:
        print(f"  {data['chunks'][0]['content'][:200]}...")
    
    print("\n" + "=" * 60)
    print("🧪 Test 2: Same search again (should hit cache)")
    print("=" * 60)
    
    # Second request (should use cache)
    response2 = requests.post(
        f"{BASE_URL}/guides/search",
        json={
            "city": "Paris",
            "themes": ["food"],
            "force_refresh": False
        }
    )
    
    data2 = response2.json()
    print(f"Cache Hit: {data2['cache_hit']}")
    print(f"Total Chunks: {data2['total_chunks']}")
    
    assert data2['cache_hit'] == True, "Second request should hit cache!"
    print("✅ Cache working correctly!")

def test_semantic_search():
    """Test semantic search with query"""
    print("\n" + "=" * 60)
    print("🧪 Test 3: Semantic search with query")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/guides/retrieve",
        json={
            "city": "Paris",
            "query": "romantic dinner spots with wine",
            "themes": ["food"],
            "k": 3
        }
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Query: {data['query']}")
    print(f"Results: {data['total_results']}")
    print(f"\nTop result:")
    if data['results']:
        print(f"  Content: {data['results'][0]['content'][:200]}...")
        print(f"  Score: {data['results'][0]['metadata'].get('relevance_score', 'N/A')}")

def test_cache_stats():
    """Test cache statistics"""
    print("\n" + "=" * 60)
    print("🧪 Test 4: Cache statistics")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/guides/stats")
    
    print(f"Status: {response.status_code}")
    stats = response.json()
    print(json.dumps(stats, indent=2))

def test_get_endpoint():
    """Test GET endpoint (browser-friendly)"""
    print("\n" + "=" * 60)
    print("🧪 Test 5: GET endpoint")
    print("=" * 60)
    
    response = requests.get(
        f"{BASE_URL}/guides/search",
        params={
            "city": "Tokyo",
            "themes": "culture,food",
            "force_refresh": False
        }
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"City: {data['city']}")
    print(f"Themes: {data['themes']}")
    print(f"Cache Hit: {data['cache_hit']}")
    print(f"Total Chunks: {data['total_chunks']}")

if __name__ == "__main__":
    print("\n🚀 Starting Day 5 API Tests\n")
    
    try:
        test_guide_search()
        test_semantic_search()
        test_cache_stats()
        test_get_endpoint()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
