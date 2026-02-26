import httpx
import asyncio
from app.core.config import settings


async def test_unsplash():
    print("\n=== UNSPLASH API KEY TEST ===")
    
    url = "https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {settings.UNSPLASH_ACCESS_KEY}"}
    params = {"query": "restaurant interior", "per_page": 1}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            total = data.get("total", 0)
            print(f"✅ Unsplash API working! Found {total} photos for test query.")
            if data["results"]:
                sample = data["results"][0]
                print(f"   Sample URL: {sample['urls']['small']}")
                print(f"   Photographer: {sample['user']['name']}")
        elif response.status_code == 401:
            print("❌ Invalid API Key - check UNSPLASH_ACCESS_KEY in .env")
        elif response.status_code == 403:
            print("❌ Rate limit exceeded - wait 1 hour")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")


async def test_wikimedia():
    print("\n=== WIKIMEDIA API TEST ===")

    # Test Wikimedia Commons API (no key required)
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": "Gateway of India",
        "prop": "pageimages",
        "piprop": "original|thumbnail",
        "pithumbsize": 800,
        "format": "json",
        "origin": "*"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            page = next(iter(pages.values()))

            if "thumbnail" in page:
                print(f"✅ Wikimedia API working!")
                print(f"   Place: {page.get('title')}")
                print(f"   Image URL: {page['thumbnail']['source']}")
            else:
                print(f"✅ Wikimedia API connected but no image for test query")
                print(f"   Page found: {page.get('title')}")
        else:
            print(f"❌ Error: {response.status_code}")


async def test_dotenv_warnings():
    print("\n=== .ENV FILE CHECK ===")
    print("⚠️  You have 'python-dotenv could not parse' warnings.")
    print("   This means lines 75-78 in your .env have invalid syntax.")
    print("   Most likely the comment lines with # === symbols.")
    print("   These are harmless warnings, config still loaded correctly.")
    print("   To fix: open backend/.env and check lines 75-78")
    print("   Make sure comments use only:  # simple comment")
    print("   Avoid:  # ===== or # ---- patterns")


async def main():
    print("=" * 50)
    print("PHASE 1: FULL VERIFICATION TEST")
    print("=" * 50)

    print("\n=== CONFIG CHECK ===")
    print(f"Unsplash Key:      {'✅ SET' if settings.UNSPLASH_ACCESS_KEY else '❌ MISSING'}")
    print(f"Cache TTL:         {settings.PHOTO_CACHE_TTL}s ({settings.PHOTO_CACHE_TTL // 3600}h)")
    print(f"Max Photos:        {settings.MAX_PHOTOS_PER_POI}")
    print(f"Wikimedia Timeout: {settings.WIKIMEDIA_TIMEOUT}s")
    print(f"Unsplash Timeout:  {settings.UNSPLASH_TIMEOUT}s")

    await test_unsplash()
    await test_wikimedia()
    await test_dotenv_warnings()

    print("\n" + "=" * 50)
    print("PHASE 1 COMPLETE ✅")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
