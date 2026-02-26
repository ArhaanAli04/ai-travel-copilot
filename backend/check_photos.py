import asyncio
import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL     = os.getenv("MONGODB_URL")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "travel_copilot")

async def check():
    print(f"Connecting to MongoDB...")
    print(f"DB Name: {MONGODB_DB_NAME}")

    client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
    db     = client[MONGODB_DB_NAME]

    # ── foursquare_tips collection ──────────────────────────────
    total = await db.foursquare_tips.count_documents({})
    print(f"\n── foursquare_tips collection ──")
    print(f"Total documents: {total}")

    if total == 0:
        print("❌ Empty — Foursquare enrichment was never run")
    else:
        with_photos = await db.foursquare_tips.count_documents(
            {"photos": {"$exists": True, "$not": {"$size": 0}}}
        )
        print(f"With photos stored: {with_photos} / {total}")

        sample = await db.foursquare_tips.find_one(
            {"photos": {"$exists": True, "$not": {"$size": 0}}}
        )
        if sample:
            print(f"\nSample with photos:")
            print(f"  fsq_name:     {sample.get('fsq_name')}")
            print(f"  poi_id:       {sample.get('poi_id')}")
            print(f"  fsq_place_id: {sample.get('fsq_place_id')}")
            print(f"  photos ({len(sample.get('photos', []))}): {sample.get('photos', [])}")
        else:
            print("⚠️  Tips exist but photos array is empty on all documents")

        # Show a sample with no photos to understand the structure
        no_photo_sample = await db.foursquare_tips.find_one({})
        if no_photo_sample:
            print(f"\nSample doc keys: {list(no_photo_sample.keys())}")
            print(f"  fsq_name:     {no_photo_sample.get('fsq_name')}")
            print(f"  fsq_place_id: {no_photo_sample.get('fsq_place_id')}")
            print(f"  photos:       {no_photo_sample.get('photos', 'FIELD MISSING')}")

    # ── pois collection ─────────────────────────────────────────
    print(f"\n── pois collection ──")
    total_pois = await db.pois.count_documents({})
    print(f"Total POIs: {total_pois}")

    pois_with_fsq = await db.pois.count_documents(
        {"fsq_place_id": {"$exists": True}}
    )
    print(f"POIs with fsq_place_id stored: {pois_with_fsq}")

    # Show sample POI structure
    sample_poi = await db.pois.find_one({})
    if sample_poi:
        print(f"Sample POI keys: {list(sample_poi.keys())}")
        print(f"Sample POI name: {sample_poi.get('name')}")
        print(f"Sample POI category: {sample_poi.get('category')}")

    client.close()

asyncio.run(check())
