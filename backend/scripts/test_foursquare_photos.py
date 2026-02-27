"""
Test Foursquare photos endpoint directly.
Run: python scripts/test_foursquare_photos.py
"""
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from dotenv import load_dotenv
load_dotenv()

API_KEY      = os.getenv("FOURSQUARE_API_KEY")
BASE_URL     = "https://places-api.foursquare.com"
API_VERSION  = "2025-06-17"

# Use the exact fsq_place_id from your DB
FSQ_PLACE_ID = "55b0ada7498eb6db61956210"   # Cafe Andora

headers = {
    "Accept":             "application/json",
    "Authorization":      f"Bearer {API_KEY}",
    "X-Places-Api-Version": API_VERSION
}

print(f"API Key: {API_KEY[:10]}...")
print(f"Testing place ID: {FSQ_PLACE_ID}")
print()

# Test 1: Place details
print("── Test 1: GET /places/{id} ──────────────────────────")
r = requests.get(
    f"{BASE_URL}/places/{FSQ_PLACE_ID}",
    headers=headers,
    params={"fields": "fsq_place_id,name,rating,photos,tips"},
    timeout=10
)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")
print()

# Test 2: Dedicated photos endpoint
print("── Test 2: GET /places/{id}/photos ───────────────────")
r2 = requests.get(
    f"{BASE_URL}/places/{FSQ_PLACE_ID}/photos",
    headers=headers,
    params={"limit": 5},
    timeout=10
)
print(f"Status: {r2.status_code}")
print(f"Response: {r2.text[:500]}")
print()

# Test 3: Search endpoint (verify API key works at all)
print("── Test 3: GET /places/search (verify key works) ─────")
r3 = requests.get(
    f"{BASE_URL}/places/search",
    headers=headers,
    params={"ll": "18.9220,72.8311", "query": "cafe", "limit": 1},
    timeout=10
)
print(f"Status: {r3.status_code}")
print(f"Response: {r3.text[:300]}")
