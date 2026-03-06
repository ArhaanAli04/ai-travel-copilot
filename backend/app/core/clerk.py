import httpx
import jwt
import logging
from jwt.algorithms import RSAAlgorithm
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

JWKS_URL = "https://api.clerk.com/v1/jwks"
_jwks_cache: Optional[dict] = None


async def get_jwks() -> dict:
    """Fetch Clerk's public keys (cached)."""
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"}
        response = await client.get(JWKS_URL, headers=headers)
        response.raise_for_status()
        _jwks_cache = response.json()
        return _jwks_cache


async def verify_clerk_token(token: str) -> dict:
    """
    Verify a Clerk JWT and return the decoded payload.
    Raises jwt.InvalidTokenError if invalid.
    """
    jwks = await get_jwks()

    # Decode header to get key ID
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    # Find matching key
    public_key = None
    for key_data in jwks.get("keys", []):
        if key_data.get("kid") == kid:
            public_key = RSAAlgorithm.from_jwk(key_data)
            break

    if not public_key:
        raise jwt.InvalidTokenError("No matching public key found")

    # Verify and decode
    payload = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        options={"verify_aud": False},  # Clerk doesn't set aud by default
    )
    return payload
