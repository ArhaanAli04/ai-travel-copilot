"""
AI Prompts for PlannerAgent
Structured prompts for Gemini itinerary generation
"""
from typing import List, Dict
from datetime import date
import json
import os
import pycountry
import geonamescache
# Initialize this outside the function so it only loads into memory once
_gc = geonamescache.GeonamesCache()
_airports_cache: dict = {}

def _load_airports() -> dict:
    """
    Load airports.json and build a unified lookup dict indexed by IATA code.
    airports.json keys are ICAO codes (e.g. "VABB") but users type IATA codes (e.g. "BOM").
    We build a reverse map: IATA → airport_data so "BOM" lookups work correctly.
    """
    global _airports_cache
    if _airports_cache:
        return _airports_cache
    try:
        airports_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "data", "airports.json"
        ))
        with open(airports_path, "r", encoding="utf-8") as f:
            all_airports = json.load(f)

        # Build IATA-keyed index (skip airports with no IATA code)
        iata_indexed = {}
        for icao_code, data in all_airports.items():
            iata = data.get("iata", "").strip()
            if iata:
                iata_indexed[iata] = data   # "BOM" → Mumbai data
                iata_indexed[icao_code] = data  # "VABB" → Mumbai data (bonus)

        _airports_cache = iata_indexed
        logging.getLogger(__name__).info(f"✅ Loaded {len(iata_indexed)} airport entries (IATA + ICAO indexed)")

    except Exception as e:
        logging.getLogger(__name__).warning(f"⚠️ Could not load airports.json: {e}")
        _airports_cache = {}
    return _airports_cache

# System prompt for itinerary planning
ITINERARY_SYSTEM_PROMPT = """You are an expert travel planner AI assistant. Your goal is to create personalized, realistic, and enjoyable day-by-day itineraries based on:

1. **Weather conditions** - Suggest indoor activities for bad weather, outdoor for good weather
2. **User preferences** - Match activities to their interests and budget
3. **Local insights** - Use authentic local recommendations, not just tourist traps
4. **Timing** - Create realistic schedules with travel time between locations
5. **Budget** - Keep activities within the specified budget per day

**Output Format:**
You MUST respond with valid JSON only. No markdown, no explanations, just pure JSON.

Format:
{
  "day_theme": "Brief theme description",
  "day_description": "2-sentence overview of the day",
  "activities": [
    {
      "title": "Activity name",
      "description": "What you'll do and why it's great",
      "category": "sightseeing|dining|entertainment|shopping|relaxation",
      "start_time": "HH:MM",
      "duration_minutes": 120,
      "location": "Location name",
      "estimated_cost": 25.50,
      "reasoning": "Why this activity fits the weather/preferences"
    }
  ]
}

**Important:**
- Suggest 3-5 activities per day
- Include breakfast, lunch, dinner suggestions
- Account for travel time between locations
- Consider weather (e.g., museums on rainy days, parks on sunny days)
- Stay within budget
- Mix different activity types for variety
"""


def create_day_planning_prompt(
    day_number: int,
    date_str: str,
    city: str,
    weather: Dict,
    budget_per_day: float,
    interests: List[str],
    preferences: Dict,
    guide_context: str,
    trip_type: str = "solo",
    traveler_count: int = 1
) -> str:
    """
    Create a day planning prompt with all context
    
    Args:
        day_number: Day number in trip
        date_str: Date string (e.g., "2026-01-15")
        city: City name
        weather: Weather dict with temp, condition, icon
        budget_per_day: Budget per day in USD
        interests: List of user interests
        preferences: Additional preferences dict
        guide_context: Relevant travel guide content
        trip_type: solo, couple, family, group
        traveler_count: Number of travelers
        
    Returns:
        Formatted prompt string
    """
    
    # Format weather info
    weather_desc = f"{weather.get('icon', '🌤️')} {weather.get('condition', 'Unknown')}"
    temp_high = weather.get('temp_high', 20)
    temp_low = weather.get('temp_low', 15)
    precipitation = weather.get('precipitation_prob', 0)
    
    # Format interests
    interests_str = ", ".join(interests) if interests else "general sightseeing"
    
    # Build prompt
    prompt = f"""Plan Day {day_number} of a {trip_type} trip to {city}.

**Date:** {date_str}

**Weather Forecast:**
- Conditions: {weather_desc}
- Temperature: {temp_low}°C - {temp_high}°C
- Precipitation chance: {precipitation}%

**Trip Details:**
- Travelers: {traveler_count} person(s)
- Type: {trip_type}
- Budget for this day: ${budget_per_day:.2f}
- Interests: {interests_str}

**Additional Preferences:**
{format_preferences(preferences)}

**Local Recommendations (use these as inspiration):**
{guide_context}

**Instructions:**
1. Create a realistic day plan with 3-5 activities
2. **Weather-appropriate**: {"Choose indoor activities (museums, cafes, shopping) due to rain/bad weather" if precipitation > 40 else "Take advantage of good weather with outdoor activities"}
3. Include meal suggestions (breakfast, lunch, dinner)
4. Stay within ${budget_per_day:.2f} budget
5. Match activities to interests: {interests_str}
6. Provide specific location names from the guide content
7. Include realistic start times and durations
8. Add brief reasoning for each activity

Respond with ONLY the JSON format specified in the system prompt. No markdown, no extra text.
"""
    
    return prompt


def format_preferences(preferences: Dict) -> str:
    """Format preferences dict into readable string"""
    if not preferences:
        return "None specified"
    
    formatted = []
    for key, value in preferences.items():
        formatted.append(f"- {key.replace('_', ' ').title()}: {value}")
    
    return "\n".join(formatted) if formatted else "None specified"


def format_guide_context(documents: List, max_length: int = 2000) -> str:
    """
    Format LangChain documents into context string
    
    Args:
        documents: List of Document objects from retriever
        max_length: Maximum character length
        
    Returns:
        Formatted context string
    """
    if not documents:
        return "No specific recommendations available. Use your general knowledge."
    
    context_parts = []
    total_length = 0
    
    for i, doc in enumerate(documents, 1):
        content = doc.page_content[:300]  # Limit each doc to 300 chars
        source = doc.metadata.get("source_title", "Unknown source")
        
        part = f"{i}. {content}\n   Source: {source}\n"
        
        if total_length + len(part) > max_length:
            break
        
        context_parts.append(part)
        total_length += len(part)
    
    return "\n".join(context_parts)


# Fallback prompt if no guide data available
FALLBACK_PLANNING_PROMPT = """You don't have specific local guides, but use your general knowledge of {city} to suggest popular, well-reviewed activities. Focus on major attractions, highly-rated restaurants, and authentic experiences."""


# ════════════════════════════════════════════════════════════════════
# DOCUMENTATION PROMPTS
# Legal, visa, entry requirements, and emergency contacts generation
# ════════════════════════════════════════════════════════════════════


DOCUMENTATION_SYSTEM_PROMPT = """You are an expert travel documentation advisor with deep knowledge of international visa requirements, entry regulations, legal advisories, and emergency services worldwide.

Your task is to generate accurate, structured travel documentation for a trip based on the traveler's origin country and destinations.

**CRITICAL OUTPUT RULES:**
- Respond with ONLY valid JSON. Zero markdown, zero explanations, zero extra text.
- Every destination in the trip MUST have exactly one entry in each of the 4 sections.
- Never skip a destination. Never merge two destinations into one entry.
- If you are uncertain about a specific detail, provide the best known information and flag it in the notes field.

**JSON OUTPUT STRUCTURE:**
{
  "origin_country": "string — full country name derived from origin city",

  "document_checklist": [
    {
      "destination": "string — City, Country",
      "visa_type": "string — e.g. Schengen Visa | Visa on Arrival | e-Visa | Visa Free | Tourist Visa",
      "visa_cost": "string — e.g. €80 EUR | Free | $50 USD | Varies",
      "processing_days": "string — e.g. 15-20 business days | Instant | 3-5 business days",
      "apply_url": "string — official government or embassy URL for visa application",
      "procedure": "string — step by step visa application procedure as a single paragraph",
      "checklist_items": [
        {
          "item": "string — document name",
          "required": true,
          "notes": "string or null — specific requirements or tips"
        }
      ]
    }
  ],

  "entry_requirements": [
    {
      "destination": "string — City, Country",
      "items": [
        {
          "category": "string — Health | Customs | Restricted Items | Minor Travel | Currency | Dual Citizenship",
          "description": "string — short title",
          "details": "string — full explanation"
        }
      ]
    }
  ],

  "legal_advisories": [
    {
      "destination": "string — City, Country",
      "advisories": [
        {
          "severity": "string — critical | warning | info",
          "category": "string — Drug Laws | LGBTQ+ Rights | Drone Regulations | Photography Restrictions | Dress Code | Alcohol Laws | Scam Awareness | Cultural Norms",
          "description": "string — clear, specific advisory text"
        }
      ]
    }
  ],

  "emergency_contacts": [
    {
      "destination": "string — City, Country",
      "police": "string — local police number",
      "ambulance": "string — local ambulance number",
      "fire": "string — local fire brigade number",
      "general_emergency": "string — unified emergency number if exists e.g. 112",
      "embassy_phone": "string — origin country embassy phone in this destination",
      "embassy_address": "string — origin country embassy address in this destination",
      "embassy_website": "string — embassy website URL",
      "hospital_recommendations": [
        {
          "name": "string — hospital name",
          "address": "string or null",
          "phone": "string or null",
          "notes": "string or null — e.g. Best English-speaking hospital"
        }
      ],
      "travel_advisory_level": "string — e.g. Level 1 - Exercise Normal Precautions",
      "travel_advisory_source": "string — e.g. US State Department | UK FCDO | Indian MEA"
    }
  ]
}

**SEVERITY GUIDE for legal_advisories:**
- critical: Criminal offense, possible arrest, imprisonment — e.g. drug trafficking, photographing military
- warning: Fines, confiscation, deportation risk — e.g. drone without permit, excessive cash
- info: Cultural sensitivity, etiquette, strong recommendations — e.g. dress codes, tipping norms

**CHECKLIST ITEMS to always include for each destination (add more as relevant):**
- Passport (with validity note)
- Visa (if required)
- Travel insurance
- Return/onward ticket proof
- Hotel booking confirmation
- Bank statement / proof of funds
- Passport-size photographs
- Vaccination certificates (only if required for that destination)

**IMPORTANT:**
- Base embassy information on the traveler's ORIGIN COUNTRY visiting each destination
- Travel advisory levels should reflect the origin country's government advisory
- For minor travelers (under 18), always add minor travel requirements in entry_requirements
- Include 2-3 hospital recommendations per destination
- All phone numbers should be in local format as dialed within the country
"""


# ── Prompt builder ──────────────────────────────────────────────────

def create_documentation_prompt(
    origin: str,
    destinations: list[str],
    start_date: str,
    end_date: str,
    traveler_count: int,
    trip_type: str,
    traveler_ages: list[int] | None = None,
    budget_currency: str = "USD",
) -> str:
    """
    Build the user-facing documentation generation prompt.

    Args:
        origin:          Trip origin city/country (e.g. "Mumbai, India")
        destinations:    List of destination city strings (e.g. ["Paris", "Rome"])
        start_date:      ISO date string (e.g. "2026-06-01")
        end_date:        ISO date string (e.g. "2026-06-14")
        traveler_count:  Number of travelers
        trip_type:       solo | couple | family | group
        traveler_ages:   Optional list of traveler ages (e.g. [35, 32, 8, 5])
        budget_currency: Currency code (e.g. "USD", "INR", "EUR")

    Returns:
        Formatted prompt string
    """

    # ── Derive origin country context ──────────────────────────────
    origin_context = _format_origin_context(origin)

    # ── Format destinations list ────────────────────────────────────
    destinations_str = "\n".join(
        f"  {i + 1}. {dest}" for i, dest in enumerate(destinations)
    )

    # ── Traveler details ────────────────────────────────────────────
    traveler_details = _format_traveler_details(
        traveler_count=traveler_count,
        trip_type=trip_type,
        traveler_ages=traveler_ages,
    )

    # ── Minor traveler flag ─────────────────────────────────────────
    has_minors = _check_has_minors(traveler_ages)
    minor_instruction = (
        "\n⚠️ IMPORTANT: This trip includes MINOR travelers (under 18). "
        "You MUST include minor travel requirements (consent letters, "
        "guardian documentation, unaccompanied minor rules) in the "
        "entry_requirements section for EVERY destination."
        if has_minors
        else ""
    )

    # ── Trip duration ───────────────────────────────────────────────
    duration_note = _format_duration_note(start_date, end_date)

    # ── Final prompt ────────────────────────────────────────────────
    prompt = f"""Generate complete travel documentation for the following trip:

**TRAVELER ORIGIN:**
{origin_context}

**DESTINATIONS ({len(destinations)} total):**
{destinations_str}

**TRIP DETAILS:**
- Travel dates: {start_date} to {end_date} ({duration_note})
- Trip type: {trip_type}
- Traveler count: {traveler_count}
- Traveler details: {traveler_details}
- Currency preference: {budget_currency}
{minor_instruction}

**YOUR TASK:**
Generate complete documentation for ALL {len(destinations)} destination(s) listed above.

For EACH destination, provide:
1. DOCUMENT CHECKLIST — Visa type, cost, processing time, official application URL, step-by-step procedure, and full document checklist
2. ENTRY REQUIREMENTS — Health requirements, customs limits, restricted items, currency rules{", minor travel requirements" if has_minors else ""}
3. LEGAL ADVISORIES — Drug laws, LGBTQ+ status, drone regulations, photography restrictions, dress codes, scam awareness
4. EMERGENCY CONTACTS — Local emergency numbers, {origin_context.split(",")[0].strip()} embassy details, 2-3 recommended hospitals, travel advisory level

**ORIGIN COUNTRY CONTEXT:**
The traveler is from {origin_context}. All embassy information should reflect {origin_context.split(",")[0].strip()} embassies/consulates in each destination. Travel advisory levels should be from the perspective of a traveler from {origin_context}.

Respond with ONLY the JSON. No markdown fences, no explanation text.
"""

    return prompt


# ── Private helper functions ────────────────────────────────────────
import logging
def _format_origin_context(origin: str) -> str:
    """
    Map origin city/airport string to 'City, Country' format.

    Resolution order:
    1. IATA code → airports.json (e.g. BOM → Mumbai, India)
    2. City name → geonamescache by population (e.g. Delhi → Delhi, India)
    3. Multi-word partial match in geonamescache (e.g. New York → New York, United States)
    4. Fallback → return as-is (Gemini handles it)
    """
    clean_origin = origin.strip()
    if not clean_origin:
        return origin

    # ── Strategy 1: IATA code lookup ────────────────────────────────
    # Handles: "BOM", "DEL", "DXB", "JFK", "LHR" etc.
    upper = clean_origin.upper()
    if len(upper) in (3, 4):  # IATA = 3 chars, ICAO = 4 chars
        airports = _load_airports()
        if upper in airports:
            airport = airports[upper]
            city = airport.get("city", clean_origin)
            country_name = _country_code_to_name(airport.get("country", ""))
            return f"{city}, {country_name}" if country_name else city

    # ── Strategy 2: Exact city name via geonamescache ────────────────
    # Handles: "Mumbai", "Delhi", "London", "Singapore" etc.
    try:
        matches = _gc.get_cities_by_name(clean_origin)
        if matches:
            city_options = [
                city_data
                for match in matches
                for city_data in match.values()
            ]
            # Pick highest population — always gives the major city
            city_options.sort(key=lambda x: x.get("population", 0), reverse=True)
            best = city_options[0]
            country_code = best.get("countrycode", "")
            country_name = _country_code_to_name(country_code)
            city_name = best.get("name", clean_origin)
            return f"{city_name}, {country_name}" if country_name else city_name
    except Exception as e:
        logging.getLogger(__name__).warning(f"⚠️ geonamescache lookup failed: {e}")

    # ── Strategy 3: Multi-word city via geonamescache ────────────────
    # Handles: "New York", "Kuala Lumpur", "São Paulo" etc.
    # geonamescache doesn't support multi-word lookup directly,
    # so we search all cities and match by name
    try:
        all_cities = _gc.get_cities()
        lower_origin = clean_origin.lower()

        # Collect all cities whose name matches (case-insensitive)
        name_matches = [
            city for city in all_cities.values()
            if city.get("name", "").lower() == lower_origin
        ]

        if name_matches:
            # Pick highest population
            name_matches.sort(key=lambda x: x.get("population", 0), reverse=True)
            best = name_matches[0]
            country_code = best.get("countrycode", "")
            country_name = _country_code_to_name(country_code)
            city_name = best.get("name", clean_origin)
            return f"{city_name}, {country_name}" if country_name else city_name
    except Exception as e:
        logging.getLogger(__name__).warning(f"⚠️ Multi-word city lookup failed: {e}")

    # ── Fallback ─────────────────────────────────────────────────────
    return clean_origin


def _country_code_to_name(country_code: str) -> str:
    """
    Convert 2-letter ISO country code to full country name using pycountry.
    """
    if not country_code:
        return ""
    try:
        country = pycountry.countries.get(alpha_2=country_code.upper())
        if country:
            return country.name
        return country_code
    except Exception:
        return country_code

def _format_traveler_details(
    traveler_count: int,
    trip_type: str,
    traveler_ages: list[int] | None,
) -> str:
    """Format traveler details into a readable string."""
    if not traveler_ages:
        trip_type_descriptions = {
            "solo":   f"1 adult traveler",
            "couple": f"2 adult travelers",
            "family": f"{traveler_count} travelers (family group)",
            "group":  f"{traveler_count} travelers (group trip)",
        }
        return trip_type_descriptions.get(trip_type, f"{traveler_count} travelers")

    # Build age breakdown
    adults = [age for age in traveler_ages if age >= 18]
    minors = [age for age in traveler_ages if age < 18]

    parts = []
    if adults:
        parts.append(f"{len(adults)} adult(s) (ages: {', '.join(str(a) for a in adults)})")
    if minors:
        parts.append(f"{len(minors)} minor(s) (ages: {', '.join(str(m) for m in minors)})")

    return ", ".join(parts) if parts else f"{traveler_count} travelers"


def _check_has_minors(traveler_ages: list[int] | None) -> bool:
    """Return True if any traveler is under 18."""
    if not traveler_ages:
        return False
    return any(age < 18 for age in traveler_ages)


def _format_duration_note(start_date: str, end_date: str) -> str:
    """Calculate trip duration as a readable string."""
    try:
        from datetime import date as date_type
        start = date_type.fromisoformat(start_date)
        end = date_type.fromisoformat(end_date)
        days = (end - start).days + 1
        nights = days - 1
        return f"{days} days, {nights} nights"
    except Exception:
        return "see dates above"