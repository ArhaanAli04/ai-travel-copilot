"""
Clears all documents from foursquare_tips collection.
Use before re-running enrichment tests.

Run from backend/ directory:
    python scripts/clear_test_enrichment.py
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend root to path
sys.path.append(str(Path(__file__).parent.parent))

import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv()

def get_db_name_from_url(url: str) -> str:
    """Extract database name from MongoDB URL"""
    # mongodb+srv://user:pass@cluster.net/travel_copilot?retryWrites=...
    try:
        path = url.split("/")[-1]           # "travel_copilot?retryWrites=..."
        db_name = path.split("?")[0]        # "travel_copilot"
        return db_name if db_name else "travel_copilot"
    except Exception:
        return "travel_copilot"


async def clear():
    mongo_url = os.getenv("MONGODB_URL", "")

    if not mongo_url:
        print("❌ MONGODB_URL not found in .env")
        return

    db_name = get_db_name_from_url(mongo_url)
    print(f"Connecting to MongoDB...")
    print(f"Database: {db_name}")

    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
    db     = client[db_name]

    # Show current count before deletion
    count_before = await db.foursquare_tips.count_documents({})
    print(f"Documents in foursquare_tips: {count_before}")

    if count_before == 0:
        print("✅ Already empty — nothing to clear")
        client.close()
        return

    # Confirm before deleting
    confirm = input(f"Delete all {count_before} documents? (yes/no): ")
    if confirm.lower() != "yes":
        print("Cancelled.")
        client.close()
        return

    result = await db.foursquare_tips.delete_many({})
    print(f"✅ Deleted {result.deleted_count} documents from foursquare_tips")

    client.close()


asyncio.run(clear())
