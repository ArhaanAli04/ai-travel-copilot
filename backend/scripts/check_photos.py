"""
Check what Foursquare photo data exists in MongoDB.
Run from backend/ directory:
    python scripts/check_photos.py
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv()

def get_db_name_from_url(url: str) -> str:
    try:
        path   = url.split("/")[-1]
        db_name = path.split("?")[0]
        return db_name if db_name else "travel_copilot"
    except Exception:
        return "travel_copilot"

async def check():
    mongo_url = os.getenv("MONGODB_URL", "")
    db_name   = get_db_name_from_url(mongo_url)

    print(f"Connecting to MongoDB...")
    print(f"Database: {db_name}")

    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
    db= client[db_name]

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
