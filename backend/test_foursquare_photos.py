"""
Test script to check Foursquare photo availability for MongoDB POIs
"""

import asyncio
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import certifi

async def test_poi_structure():
    """Test 1: Check MongoDB POI structure"""
    print("\n" + "="*60)
    print("TEST 1: Checking MongoDB POI Structure")
    print("="*60)
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        tlsCAFile=certifi.where()
    )
    db = client.get_database("travel_copilot")
    pois_collection = db["pois"]
    
    # Get sample POIs
    sample_pois = await pois_collection.find().limit(10).to_list(10)
    
    print(f"\n✅ Found {len(sample_pois)} sample POIs")
    print("\n📊 POI Structure Analysis:")
    
    has_fsq_id = 0
    has_osm_id = 0
    has_name = 0
    
    for poi in sample_pois:
        if 'fsq_id' in poi or 'foursquare_id' in poi:
            has_fsq_id += 1
        if 'osm_id' in poi:
            has_osm_id += 1
        if 'name' in poi:
            has_name += 1
    
    print(f"  • POIs with name: {has_name}/{len(sample_pois)}")
    print(f"  • POIs with Foursquare ID: {has_fsq_id}/{len(sample_pois)}")
    print(f"  • POIs with OSM ID: {has_osm_id}/{len(sample_pois)}")
    
    # Show first POI structure
    if sample_pois:
        print("\n📝 Sample POI Structure:")
        first_poi = sample_pois[0]
        print(f"  Name: {first_poi.get('name', 'N/A')}")
        print(f"  Foursquare ID: {first_poi.get('fsq_id') or first_poi.get('foursquare_id', 'N/A')}")
        print(f"  OSM ID: {first_poi.get('osm_id', 'N/A')}")
        print(f"  Category: {first_poi.get('category', 'N/A')}")
        print(f"  All keys: {list(first_poi.keys())}")
    
    client.close()
    return sample_pois


async def test_foursquare_photos_api(sample_pois):
    """Test 2: Test Foursquare Photos API"""
    print("\n" + "="*60)
    print("TEST 2: Testing Foursquare Photos API")
    print("="*60)
    
    # Get Foursquare API key
    fsq_api_key = settings.FOURSQUARE_API_KEY
    
    if not fsq_api_key:
        print("\n❌ ERROR: FOURSQUARE_API_KEY not found in .env")
        return
    
    print(f"\n✅ API Key found: {fsq_api_key[:20]}...")
    
    # Find POI with Foursquare ID
    test_poi = None
    for poi in sample_pois:
        fsq_id = poi.get('fsq_id') or poi.get('foursquare_id')
        if fsq_id:
            test_poi = poi
            break
    
    if not test_poi:
        print("\n❌ No POIs with Foursquare ID found!")
        print("\n💡 Your POIs might not have Foursquare IDs stored.")
        print("   This could mean:")
        print("   1. POIs were ingested from OSM only (no Foursquare data)")
        print("   2. Foursquare ID field name is different")
        return
    
    fsq_id = test_poi.get('fsq_id') or test_poi.get('foursquare_id')
    print(f"\n🧪 Testing with POI: {test_poi.get('name')}")
    print(f"   Foursquare ID: {fsq_id}")
    
    # Test Foursquare Photos API
    url = f"https://api.foursquare.com/v3/places/{fsq_id}/photos"
    headers = {
        "Authorization": fsq_api_key,
        "Accept": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"\n📡 Calling: {url}")
            response = await client.get(url, headers=headers, timeout=10)
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                photos = response.json()
                print(f"\n✅ SUCCESS! Found {len(photos)} photos")
                
                # Show first 3 photos
                for i, photo in enumerate(photos[:3], 1):
                    photo_url = f"{photo['prefix']}original{photo['suffix']}"
                    print(f"\n   Photo {i}:")
                    print(f"     URL: {photo_url}")
                    print(f"     Size: {photo.get('width', 'N/A')}x{photo.get('height', 'N/A')}")
                    print(f"     Created: {photo.get('created_at', 'N/A')}")
                
                return len(photos)
            
            elif response.status_code == 401:
                print("\n❌ ERROR: Invalid API Key")
                print("   Check your FOURSQUARE_API_KEY in .env")
            
            elif response.status_code == 404:
                print("\n⚠️  No photos found for this venue")
                print("   This is normal - not all venues have photos")
            
            else:
                print(f"\n❌ ERROR: {response.status_code}")
                print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


async def test_multiple_pois(sample_pois):
    """Test 3: Check photo availability across multiple POIs"""
    print("\n" + "="*60)
    print("TEST 3: Photo Availability Analysis")
    print("="*60)
    
    fsq_api_key = settings.FOURSQUARE_API_KEY
    
    if not fsq_api_key:
        print("\n⚠️  Skipping (no API key)")
        return
    
    results = {
        'total': 0,
        'with_fsq_id': 0,
        'with_photos': 0,
        'photo_counts': []
    }
    
    async with httpx.AsyncClient() as client:
        for poi in sample_pois:
            results['total'] += 1
            
            fsq_id = poi.get('fsq_id') or poi.get('foursquare_id')
            
            if not fsq_id:
                continue
            
            results['with_fsq_id'] += 1
            
            # Try to get photos
            try:
                url = f"https://api.foursquare.com/v3/places/{fsq_id}/photos"
                headers = {
                    "Authorization": fsq_api_key,
                    "Accept": "application/json"
                }
                
                response = await client.get(url, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    photos = response.json()
                    photo_count = len(photos)
                    
                    if photo_count > 0:
                        results['with_photos'] += 1
                        results['photo_counts'].append(photo_count)
                        print(f"✅ {poi.get('name', 'Unknown')[:30]:<30} - {photo_count} photos")
                    else:
                        print(f"⚠️  {poi.get('name', 'Unknown')[:30]:<30} - No photos")
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
            
            except Exception as e:
                print(f"❌ {poi.get('name', 'Unknown')[:30]:<30} - Error: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"Total POIs tested: {results['total']}")
    print(f"POIs with Foursquare ID: {results['with_fsq_id']} ({results['with_fsq_id']/results['total']*100:.1f}%)")
    print(f"POIs with photos: {results['with_photos']}")
    
    if results['photo_counts']:
        avg_photos = sum(results['photo_counts']) / len(results['photo_counts'])
        print(f"Average photos per POI: {avg_photos:.1f}")
        print(f"Max photos: {max(results['photo_counts'])}")
        print(f"Min photos: {min(results['photo_counts'])}")
    
    print("\n💡 Photo Coverage Rate:")
    if results['with_fsq_id'] > 0:
        coverage = results['with_photos'] / results['with_fsq_id'] * 100
        print(f"   {coverage:.1f}% of POIs with Foursquare IDs have photos")
        
        if coverage > 70:
            print("   ✅ EXCELLENT - Good photo coverage!")
        elif coverage > 40:
            print("   ⚠️  MODERATE - Consider fallback images")
        else:
            print("   ❌ LOW - Need fallback image strategy")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 FOURSQUARE PHOTOS API TEST SUITE")
    print("="*60)
    
    try:
        # Test 1: Check POI structure
        sample_pois = await test_poi_structure()
        
        if not sample_pois:
            print("\n❌ No POIs found in MongoDB!")
            return
        
        # Test 2: Test Foursquare API
        await test_foursquare_photos_api(sample_pois)
        
        # Test 3: Check multiple POIs
        await test_multiple_pois(sample_pois)
        
        print("\n" + "="*60)
        print("✅ TESTING COMPLETE!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
