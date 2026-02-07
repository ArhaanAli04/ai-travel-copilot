"""
Script to fix timestamps for existing sessions
"""
import asyncio
from datetime import datetime,timezone
from motor.motor_asyncio import AsyncIOMotorClient
import certifi
import os
from dotenv import load_dotenv

load_dotenv()

async def fix_timestamps():
    """Update all sessions with correct updated_at timestamps"""
    
    # Connect to MongoDB
    mongodb_url = os.getenv("MONGODB_URL")
    client = AsyncIOMotorClient(
        mongodb_url,
        tlsCAFile=certifi.where()
    )
    
    db = client.get_database("travel_copilot")
    sessions_collection = db["chat_sessions"]
    
    # Get all sessions
    sessions = await sessions_collection.find({}).to_list(length=None)
    
    print(f"Found {len(sessions)} sessions to update")
    
    for session in sessions:
        session_id = session["_id"]
        
        # Get the timestamp of the last message (if any)
        messages = session.get("messages", [])
        
        if messages:
            # Use the last message's timestamp
            last_message = messages[-1]
            updated_at = last_message.get("timestamp", datetime.now(timezone.utc))
        else:
            # No messages, use created_at or current time
            updated_at = session.get("created_at", datetime.now(timezone.utc))
        
        # Update the session
        result = await sessions_collection.update_one(
            {"_id": session_id},
            {"$set": {"updated_at": updated_at}}
        )
        
        print(f"✅ Updated session {session_id}: {session.get('title', 'Untitled')}")
    
    print(f"\n✅ Successfully updated {len(sessions)} sessions!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_timestamps())
