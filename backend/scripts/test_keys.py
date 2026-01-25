"""Test new Foursquare Places API authentication"""
import requests
from app.core.config import settings

api_key = settings.FOURSQUARE_API_KEY

print(f"Testing Foursquare Places API...")
print(f"API Key preview: {api_key[:15]}...")
print(f"API Key length: {len(api_key)}")

# Test 1: With X-Places-Api-Key header
print("\n=== Test 1: X-Places-Api-Key header ===")
url = "https://places-api.foursquare.com/places/search"
headers = {
    "Accept": "application/json",
    "X-Places-Api-Key": api_key,
    "X-Places-Api-Version": "2025-06-17"
}
params = {
    "ll": "18.9220,72.8311",
    "radius": 1000,
    "limit": 1
}

response = requests.get(url, headers=headers, params=params)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")

# Test 2: With Authorization header (Bearer format)
print("\n=== Test 2: Authorization Bearer ===")
headers2 = {
    "Accept": "application/json",
    "Authorization": f"Bearer {api_key}",
    "X-Places-Api-Version": "2025-06-17"
}

response2 = requests.get(url, headers=headers2, params=params)
print(f"Status: {response2.status_code}")
print(f"Response: {response2.text[:200]}")

# Test 3: Query parameter
print("\n=== Test 3: API key as query param ===")
headers3 = {
    "Accept": "application/json",
    "X-Places-Api-Version": "2025-06-17"
}
params3 = {
    **params,
    "apiKey": api_key
}

response3 = requests.get(url, headers=headers3, params=params3)
print(f"Status: {response3.status_code}")
print(f"Response: {response3.text[:200]}")

# Test 4: Just Authorization with key directly
print("\n=== Test 4: Authorization with key directly ===")
headers4 = {
    "Accept": "application/json",
    "Authorization": api_key,
    "X-Places-Api-Version": "2025-06-17"
}

response4 = requests.get(url, headers=headers4, params=params)
print(f"Status: {response4.status_code}")
print(f"Response: {response4.text[:200]}")
