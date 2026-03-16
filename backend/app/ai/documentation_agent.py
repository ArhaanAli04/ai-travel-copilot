"""
DocumentationAgent - AI-powered legal and travel documentation generation
Uses Gemini to generate visa requirements, entry rules, legal advisories,
and emergency contacts for each destination in a trip.
"""
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from google import genai
from google.genai import types
from google.genai.types import Tool, GoogleSearch
import json
import logging
import re
from app.core.config import settings
from app.models.trip import Trip
from app.models.documentation import TripDocumentation
from app.ai.prompts import (
    DOCUMENTATION_SYSTEM_PROMPT,
    create_documentation_prompt,
)

logger = logging.getLogger(__name__)


class DocumentationAgent:
    """
    AI agent for generating legal and travel documentation for a trip.

    Generates:
    - Document checklist (visa type, cost, procedure, required docs)
    - Entry requirements (health, customs, restricted items, minors)
    - Legal advisories (drug laws, LGBTQ+, drones, photography)
    - Emergency contacts (embassy, police, ambulance, hospitals)

    Mirrors PlannerAgent structure exactly.
    Uses temperature=0.3 for factual accuracy (vs 0.7 for creative itinerary).
    """

    def __init__(self, db: Session):
        self.db = db
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-2.5-flash"
        self.grounding_tool = Tool(google_search=GoogleSearch())
        self.config = types.GenerateContentConfig(
            temperature=0.3,          # Low temperature = more factual, less creative
            max_output_tokens=8192,   # Docs are verbose — needs more tokens than itinerary
            tools=[self.grounding_tool],
            
        )

    # ── Public API ──────────────────────────────────────────────────

    async def generate_documentation(self, trip_id: int) -> TripDocumentation:
        """
        Generate complete legal and travel documentation for a trip.

        Args:
            trip_id: ID of the trip to generate documentation for

        Returns:
            TripDocumentation object saved to DB

        Raises:
            ValueError: If trip not found
            Exception: If Gemini call or DB save fails
        """
        logger.info(f"📋 Generating documentation for trip {trip_id}")

        # Load trip
        trip = self.db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise ValueError(f"Trip {trip_id} not found")

        if not trip.destinations:
            raise ValueError(f"Trip {trip_id} has no destinations")

        try:
            # Step 1: Build prompt from trip data
            prompt = self._build_prompt(trip)

            # Step 2: Call Gemini
            logger.info(f"🤖 Calling Gemini for trip {trip_id} documentation ({len(trip.destinations)} destination(s))...")
            full_prompt = f"{DOCUMENTATION_SYSTEM_PROMPT}\n\n{prompt}"

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=self.config,
            )

            # Step 3: Parse response
            parsed = self._parse_response(response.text)
            if not parsed:
                raise ValueError("Failed to parse Gemini documentation response")

            # Step 4: Save to DB (upsert — safe to call on regenerate)
            doc = self._save_to_db(trip_id, parsed)

            logger.info(f"✅ Documentation generated for trip {trip_id}")
            return doc

        except Exception as e:
            logger.error(f"❌ Documentation generation failed for trip {trip_id}: {e}")
            raise

    # ── Private Methods ─────────────────────────────────────────────

    def _build_prompt(self, trip: Trip) -> str:
        """
        Assemble the documentation prompt from trip fields.

        Args:
            trip: Trip ORM object

        Returns:
            Formatted prompt string
        """
        # Safely extract dates as ISO strings
        start_date = (
            trip.start_date.date().isoformat()
            if isinstance(trip.start_date, datetime)
            else str(trip.start_date)
        )
        end_date = (
            trip.end_date.date().isoformat()
            if isinstance(trip.end_date, datetime)
            else str(trip.end_date)
        )

        return create_documentation_prompt(
            origin=trip.origin,
            destinations=trip.destinations,
            start_date=start_date,
            end_date=end_date,
            traveler_count=trip.traveler_count or 1,
            trip_type=trip.trip_type or "solo",
            traveler_ages=trip.traveler_ages,
            budget_currency=trip.budget_currency or "USD",
        )

    def _parse_response(self, response_text: str) -> Optional[dict]:
        """
        Parse Gemini JSON response — identical pattern to PlannerAgent._parse_gemini_response.
        With grounding enabled, Gemini may wrap JSON with citation text or
        grounding metadata — regex extraction handles this gracefully.
        Args:
            response_text: Raw text from Gemini

        Returns:
            Parsed dict or None if parsing fails
        """
        try:
            text = response_text.strip()

            # Strip markdown fences if Gemini adds them despite instructions
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            text = text.strip()
            # If grounding added surrounding text, extract the JSON block
            if not text.startswith("{"):
                
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    logger.info("🔍 Extracted JSON from grounded response")
                    text = json_match.group(0)
            def fix_control_chars(s: str) -> str:
                result = []
                in_string = False
                escape_next = False
                for char in s:
                    if escape_next:
                        result.append(char)
                        escape_next = False
                        continue
                    if char == '\\':
                        escape_next = True
                        result.append(char)
                        continue
                    if char == '"':
                        in_string = not in_string
                        result.append(char)
                        continue
                    # Inside a string, replace bare control chars with escaped versions
                    if in_string:
                        if char == '\n':
                            result.append('\\n')
                        elif char == '\r':
                            result.append('\\r')
                        elif char == '\t':
                            result.append('\\t')
                        elif ord(char) < 32:  # Other control chars
                            result.append(' ')
                        else:
                            result.append(char)
                    else:
                        result.append(char)
                return ''.join(result)

            text = fix_control_chars(text)
            data = json.loads(text)
            return data

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parse error in documentation response: {e}")
            logger.error(f"Response preview: {response_text[:500]}")
            return None

    def _save_to_db(self, trip_id: int, parsed_data: dict) -> TripDocumentation:
        """
        Upsert documentation to DB.
        Safe to call on both initial generation and regeneration.
        If a record already exists for this trip_id, it gets updated.
        If not, a new record is created.

        Args:
            trip_id: Trip ID
            parsed_data: Parsed dict from Gemini response

        Returns:
            Saved TripDocumentation ORM object
        """
        # Check if documentation already exists for this trip (regenerate case)
        existing = (
            self.db.query(TripDocumentation)
            .filter(TripDocumentation.trip_id == trip_id)
            .first()
        )

        now = datetime.now(timezone.utc)

        if existing:
            # UPDATE existing record
            logger.info(f"🔄 Updating existing documentation for trip {trip_id}")
            existing.origin_country = parsed_data.get("origin_country")
            existing.document_checklist = parsed_data.get("document_checklist", [])
            existing.entry_requirements = parsed_data.get("entry_requirements", [])
            existing.legal_advisories = parsed_data.get("legal_advisories", [])
            existing.emergency_contacts = parsed_data.get("emergency_contacts", [])
            existing.generated_at = now
            existing.updated_at = now

            self.db.commit()
            self.db.refresh(existing)
            return existing

        else:
            # INSERT new record
            logger.info(f"✨ Creating new documentation for trip {trip_id}")
            doc = TripDocumentation(
                trip_id=trip_id,
                origin_country=parsed_data.get("origin_country"),
                document_checklist=parsed_data.get("document_checklist", []),
                entry_requirements=parsed_data.get("entry_requirements", []),
                legal_advisories=parsed_data.get("legal_advisories", []),
                emergency_contacts=parsed_data.get("emergency_contacts", []),
                generated_at=now,
            )

            self.db.add(doc)
            self.db.commit()
            self.db.refresh(doc)
            return doc


# ── Factory function ────────────────────────────────────────────────

def create_documentation_agent(db: Session) -> DocumentationAgent:
    """
    Create DocumentationAgent instance.
    Mirrors create_planner_agent(db) pattern exactly.

    Args:
        db: SQLAlchemy database session

    Returns:
        DocumentationAgent instance
    """
    return DocumentationAgent(db)
