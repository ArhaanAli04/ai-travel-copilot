"""
Test MongoDB connection with different SSL configurations
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import certifi

load_dotenv()

MONGO_URL = os.getenv("MONGODB_URL")


async def test_connection():
    """Test MongoDB connection"""
    
    print("="*70)
    print("Testing MongoDB Connection")
    print("="*70)
    
    # Test 1: With certifi
    print("\n1. Testing with certifi SSL certificates...")
    try:
        client = AsyncIOMotorClient(
            MONGO_URL,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=5000
        )
        await client.admin.command('ping')
        print("   ✅ Success with certifi!")
        client.close()
        return
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 2: With relaxed SSL
    print("\n2. Testing with relaxed SSL...")
    try:
        client = AsyncIOMotorClient(
            MONGO_URL,
            tls=True,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=5000
        )
        await client.admin.command('ping')
        print("   ✅ Success with relaxed SSL!")
        client.close()
        return
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 3: Default SSL
    print("\n3. Testing with default SSL...")
    try:
        client = AsyncIOMotorClient(
            MONGO_URL,
            serverSelectionTimeoutMS=5000
        )
        await client.admin.command('ping')
        print("   ✅ Success with default SSL!")
        client.close()
        return
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    print("\n❌ All connection methods failed!")
    print("\nTroubleshooting:")
    print("1. Check MongoDB Atlas IP whitelist (allow 0.0.0.0/0)")
    print("2. Verify username/password in MONGODB_URL")
    print("3. Check if MongoDB cluster is running")
    print("4. Try updating Python SSL: pip install --upgrade certifi")


if __name__ == "__main__":
    asyncio.run(test_connection())
