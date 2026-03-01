"""
MongoDB service for Disruption Knowledge Base

Handles read/write operations for:
- passenger_rights collection
- draft_message_templates collection

All methods are async using Motor, following the same pattern as local_discovery services.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from app.core.mongo import get_database

logger = logging.getLogger(__name__)

# Collection name constants
RIGHTS_COLLECTION = "passenger_rights"
TEMPLATES_COLLECTION = "draft_message_templates"


async def get_rights(region: str, disruption_type: str) -> Optional[Dict[str, Any]]:
    """
    Look up pre-ingested passenger rights from MongoDB.

    Args:
        region: Region code (EU, US, UK, IN, CA, AU, AE, GENERAL)
        disruption_type: Disruption type (delay, cancellation, overbooking, etc.)

    Returns:
        Rights document as dict (ready to return as ExplainRightsResponse), or None on miss
    """
    try:
        db = get_database()
        if db is None:
            logger.warning("⚠️ MongoDB not connected, skipping rights lookup")
            return None

        collection = db[RIGHTS_COLLECTION]

        doc = await collection.find_one(
            {"region": region, "disruption_type": disruption_type},
            {"_id": 0}  # Exclude MongoDB _id from result
        )

        if doc:
            logger.info(f"✅ MongoDB rights HIT: region={region}, disruption_type={disruption_type}")

            # Resolve compensation: prefer tiers, fall back to flat amount
            compensation_amount = doc.get("default_compensation_amount")
            compensation_currency = doc.get("default_compensation_currency", "USD")

            tiers = doc.get("compensation_tiers", [])
            if tiers:
                # Use the highest tier as the headline figure (most visible to user)
                highest_tier = max(tiers, key=lambda t: t.get("amount", 0))
                compensation_amount = highest_tier.get("amount")
                compensation_currency = highest_tier.get("currency", compensation_currency)

            # Build source_links list from stored format
            source_links = [
                {
                    "title": s.get("title", ""),
                    "url": s.get("url", ""),
                    "type": s.get("type", "regulation"),
                    "region": s.get("region", region)
                }
                for s in doc.get("source_links", [])
            ]

            return {
                "summary": doc.get("summary", ""),
                "rights_bullets": doc.get("rights_bullets", []),
                "compensation_amount": compensation_amount,
                "compensation_currency": compensation_currency,
                "next_steps": doc.get("next_steps", []),
                "source_links": source_links,
                "cached": True,
                "region": region,
                "applicable_regulation": doc.get("applicable_regulation", ""),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }

        logger.info(f"❌ MongoDB rights MISS: region={region}, disruption_type={disruption_type}")
        return None

    except Exception as e:
        logger.error(f"❌ MongoDB rights lookup failed: {e}")
        return None


async def save_rights(region: str, disruption_type: str, rights_data: dict) -> None:
    """
    Save AI-generated rights to MongoDB so future requests hit cache.
    Uses upsert — safe to call multiple times.

    Args:
        region: Region code
        disruption_type: Disruption type
        rights_data: The full rights dict returned by Gemini (ExplainRightsResponse shape)
    """
    try:
        db = get_database()
        if db is None:
            logger.warning("⚠️ MongoDB not connected, skipping rights save")
            return

        collection = db[RIGHTS_COLLECTION]

        # Build document to save — map from ExplainRightsResponse shape to storage shape
        document = {
            "region": region,
            "disruption_type": disruption_type,
            "regulation_name": rights_data.get("applicable_regulation", ""),
            "applicable_regulation": rights_data.get("applicable_regulation", ""),
            "enforcement_body": "",
            "summary": rights_data.get("summary", ""),
            "rights_bullets": rights_data.get("rights_bullets", []),
            "compensation_tiers": [],
            "default_compensation_amount": rights_data.get("compensation_amount"),
            "default_compensation_currency": rights_data.get("compensation_currency", "USD"),
            "next_steps": rights_data.get("next_steps", []),
            "source_links": rights_data.get("source_links", []),
            "version": 1,
            "last_updated": datetime.now(timezone.utc),
            "source": "gemini_generated"  # Flag so we know this wasn't manually ingested
        }

        await collection.update_one(
            {"region": region, "disruption_type": disruption_type},  # Filter
            {"$set": document},                                        # Update
            upsert=True                                                # Insert if not exists
        )

        logger.info(f"✅ Saved AI-generated rights to MongoDB: region={region}, disruption_type={disruption_type}")

    except Exception as e:
        logger.error(f"❌ Failed to save rights to MongoDB: {e}")
        # Don't raise — this is a non-critical background save


async def get_draft_template(
    recipient_type: str,
    message_type: str,
    tone: str
) -> Optional[Dict[str, Any]]:
    """
    Look up a pre-ingested draft message template from MongoDB.

    Args:
        recipient_type: "airline", "hotel", "insurance"
        message_type: "refund", "rebooking", "cancellation", "claim", "alternative_flight"
        tone: "formal", "firm", "friendly"

    Returns:
        Template document as dict with body_template, subject_template, etc., or None on miss
    """
    try:
        db = get_database()
        if db is None:
            logger.warning("⚠️ MongoDB not connected, skipping template lookup")
            return None

        collection = db[TEMPLATES_COLLECTION]

        doc = await collection.find_one(
            {
                "recipient_type": recipient_type.lower(),
                "message_type": message_type.lower(),
                "tone": tone.lower()
            },
            {"_id": 0}
        )

        if doc:
            logger.info(
                f"✅ MongoDB template HIT: "
                f"{recipient_type}/{message_type}/{tone}"
            )
            return doc

        logger.info(
            f"❌ MongoDB template MISS: "
            f"{recipient_type}/{message_type}/{tone}"
        )
        return None

    except Exception as e:
        logger.error(f"❌ MongoDB template lookup failed: {e}")
        return None


async def save_draft_template(template_data: dict) -> None:
    """
    Upsert a draft message template into MongoDB.
    Called by the ingestion script — safe to re-run (idempotent).

    Args:
        template_data: Full template document matching DraftMessageTemplateDocument shape
    """
    try:
        db = get_database()
        if db is None:
            logger.warning("⚠️ MongoDB not connected, skipping template save")
            return

        collection = db[TEMPLATES_COLLECTION]

        filter_key = {
            "recipient_type": template_data["recipient_type"],
            "message_type": template_data["message_type"],
            "tone": template_data["tone"]
        }

        await collection.update_one(
            filter_key,
            {"$set": {**template_data, "last_updated": datetime.now(timezone.utc)}},
            upsert=True
        )

        logger.info(
            f"✅ Saved template: "
            f"{template_data['recipient_type']}/"
            f"{template_data['message_type']}/"
            f"{template_data['tone']}"
        )

    except Exception as e:
        logger.error(f"❌ Failed to save template: {e}")
        raise  # Raise here — ingestion script needs to know if saves fail


async def ensure_indexes() -> None:
    """
    Create MongoDB indexes for efficient lookups.
    Called once by the ingestion script before ingesting data.
    Safe to call multiple times (indexes are created only if they don't exist).
    """
    try:
        db = get_database()
        if db is None:
            logger.warning("⚠️ MongoDB not connected, skipping index creation")
            return

        # Unique compound index on passenger_rights
        await db[RIGHTS_COLLECTION].create_index(
            [("region", 1), ("disruption_type", 1)],
            unique=True,
            name="region_disruption_type_unique"
        )
        logger.info("✅ Index created: passenger_rights(region, disruption_type)")

        # Unique compound index on draft_message_templates
        await db[TEMPLATES_COLLECTION].create_index(
            [("recipient_type", 1), ("message_type", 1), ("tone", 1)],
            unique=True,
            name="recipient_message_tone_unique"
        )
        logger.info("✅ Index created: draft_message_templates(recipient_type, message_type, tone)")

    except Exception as e:
        logger.error(f"❌ Failed to create indexes: {e}")
        raise
