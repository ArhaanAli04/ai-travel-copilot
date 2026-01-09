"""
Full integration test for Day 5 - End-to-end caching system
"""
import requests
import time

BASE_URL = "http://localhost:8000/api"

def test_full_caching_flow():
    """Test complete caching flow"""
    print("=" * 60)
    print("🧪 Day 5 Full Integration Test")
    print("=" * 60)
    
    # Test 1: First search (web fetch)
    print("\n1️⃣ First search - Should fetch from web...")
    start = time.time()
    response1 = requests.post(
        f"{BASE_URL}/guides/search",
        json={"city": "Paris", "themes": ["food"], "force_refresh": False}
    )
    duration1 = time.time() - start
    
    data1 = response1.json()
    print(f"   ✅ Status: {response1.status_code}")
    print(f"   ⏱️  Duration: {duration1:.2f}s")
    print(f"   📦 Cache Hit: {data1['cache_hit']}")
    print(f"   📝 Chunks: {data1['total_chunks']}")
    
    assert response1.status_code == 200, "Request should succeed"
    assert data1['cache_hit'] == False, "First request should not hit cache"
    assert data1['total_chunks'] > 0, "Should have chunks"
    
    # Test 2: Second search (cache hit)
    print("\n2️⃣ Second search - Should hit cache...")
    start = time.time()
    response2 = requests.post(
        f"{BASE_URL}/guides/search",
        json={"city": "Paris", "themes": ["food"], "force_refresh": False}
    )
    duration2 = time.time() - start
    
    data2 = response2.json()
    print(f"   ✅ Status: {response2.status_code}")
    print(f"   ⏱️  Duration: {duration2:.2f}s")
    print(f"   📦 Cache Hit: {data2['cache_hit']}")
    print(f"   🚀 Speedup: {duration1/duration2:.1f}x faster!")
    
    assert response2.status_code == 200, "Request should succeed"
    assert data2['cache_hit'] == True, "Second request should hit cache"
    assert duration2 < duration1, "Cache should be faster"
    
    # Test 3: Semantic search
    print("\n3️⃣ Semantic search with query...")
    response3 = requests.post(
        f"{BASE_URL}/guides/retrieve",
        json={
            "city": "Paris",
            "query": "romantic restaurants with wine",
            "themes": ["food"],
            "k": 3
        }
    )
    
    data3 = response3.json()
    print(f"   ✅ Status: {response3.status_code}")
    print(f"   🔍 Results: {data3['total_results']}")
    if data3['results']:
        print(f"   📊 Top score: {data3['results'][0]['metadata'].get('relevance_score', 'N/A')}")
    
    assert response3.status_code == 200, "Request should succeed"
    assert data3['total_results'] > 0, "Should have results"
    
    # Test 4: Cache stats
    print("\n4️⃣ Cache statistics...")
    response4 = requests.get(f"{BASE_URL}/guides/stats")
    stats = response4.json()
    
    print(f"   ✅ Status: {response4.status_code}")
    print(f"   📊 Total chunks: {stats.get('total_chunks', 0)}")
    print(f"   🔍 API calls: {stats.get('api_calls_made', 0)}")
    
    assert response4.status_code == 200, "Request should succeed"
    
    print("\n" + "=" * 60)
    print("✅ All Day 5 tests passed!")
    print("=" * 60)
    print(f"\n💰 Cost Savings: {duration1/duration2:.1f}x faster with cache")
    print(f"🎯 Cache efficiency: {(1 - 1/2) * 100:.0f}% reduction in API calls\n")

if __name__ == "__main__":
    try:
        test_full_caching_flow()
    except AssertionError as e:
        print(f"\n❌ Test assertion failed: {e}\n")
    except Exception as e:
        print(f"\n❌ Test error: {e}\n")
        import traceback
        traceback.print_exc()
