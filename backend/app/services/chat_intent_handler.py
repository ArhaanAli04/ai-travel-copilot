import logging
from typing import List, Optional, Dict, Any
from app.core.mongo import get_database
import json
from functools import lru_cache
from pathlib import Path
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def load_airports() -> Dict[str, Dict]:
    """Load airports.json once and cache it"""
    airports_path = Path(__file__).parent.parent / "data" / "airports.json"
    with open(airports_path, "r") as f:
        return json.load(f)


def get_airport_country(iata_code: str) -> Optional[str]:
    """Get country code for an IATA airport code"""
    airports = load_airports()
    # airports.json is keyed by ICAO, so search by iata field
    for _, airport in airports.items():
        if airport.get("iata") == iata_code:
            return airport.get("country")
    return None

EU_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
    # EEA (also covered by EU261)
    "IS", "LI", "NO",
    # UK (retained EU261 post-Brexit as UK261)
    "GB",
}


def get_applicable_regions(origin: str, destination: str) -> List[str]:
    """Determine applicable regulatory regions from airport IATA codes"""
    origin_country = get_airport_country(origin)
    dest_country = get_airport_country(destination)

    logger.info(f"🌍 Route {origin}({origin_country}) → {destination}({dest_country})")

    regions = []

    # Domestic India
    if origin_country == "IN" and dest_country == "IN":
        return ["IN"]

    # International — Montreal always applies
    regions.append("INTERNATIONAL")

    # EU261 if either endpoint is EU/EEA/UK
    if dest_country in EU_COUNTRIES or origin_country in EU_COUNTRIES:
        regions.append("EU")

    # DGCA if either endpoint is India
    if origin_country == "IN" or dest_country == "IN":
        regions.append("IN")

    return regions if regions else ["INTERNATIONAL"]

# ── Intent keywords ────────────────────────────────────────────────────────
INTENT_PATTERNS = {
    "compensation": [
        "compensation", "claim", "money", "refund amount", "how much",
        "entitled to", "payment", "reimburse", "reimbursement", "owed",
        "€", "$", "£", "pay me", "get paid", "financial"
    ],
    "rights": [
        "rights", "passenger rights", "what am i", "entitled", "policy",
        "regulation", "law", "legal", "eu261", "montreal", "dgca",
        "what can i", "allowed to", "rules","hotel", "accommodation", "overnight", "meal", "voucher",  # ← ADD THESE
        "care", "lounge", "food", "shelter"
    ],
    "rebooking": [
        "rebook", "alternative flight", "another flight", "options",
        "reschedule", "change flight", "next flight", "switch", "new flight",
        "book another", "earliest flight", "available flights"
    ],
    "status": [
        "status", "where is", "landed", "delayed", "on time", "departed",
        "arrived", "current", "now", "update", "weather", "gate", "terminal",
        "in air", "flying", "when will", "how long"
    ],
}


def detect_intent(message: str) -> str:
    """Detect intent from user message. Returns one of: compensation, rights, rebooking, status, general"""
    msg_lower = message.lower()
    
    scores = {intent: 0 for intent in INTENT_PATTERNS}
    for intent, keywords in INTENT_PATTERNS.items():
        for kw in keywords:
            if kw in msg_lower:
                scores[intent] += 1
    
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "general"
    
    logger.info(f"🎯 Detected intent: {best} (scores: {scores})")
    return best

async def fetch_rights_from_mongo(
    disruption_type: str,
    regions: List[str]
) -> List[Dict]:
    """Fetch rights documents from MongoDB for given regions and disruption type"""
    try:
        db = get_database()
        if db is None:
            logger.warning("⚠️ MongoDB not connected, skipping rights fetch")
            return []

        collection = db["passenger_rights"]

        type_map = {
            "delay": "delay",
            "cancellation": "cancellation",
            "weather": "delay",
            "strike": "cancellation",
            "other": "delay",
        }
        mongo_type = type_map.get(disruption_type, "delay")

        cursor = collection.find(
            {
                "region": {"$in": regions},
                "disruption_type": mongo_type
            },
            {"_id": 0}
        )
        docs = await cursor.to_list(length=10)

        logger.info(f"📚 Fetched {len(docs)} rights docs for regions={regions}, type={mongo_type}")
        return docs

    except Exception as e:
        logger.error(f"❌ MongoDB rights fetch failed: {e}")
        return []


def format_rights_context(docs: List[Dict]) -> str:
    """Format MongoDB rights documents into prompt-ready text"""
    if not docs:
        return "No specific regulatory data available for this route."
    
    sections = []
    for doc in docs:
        region = doc.get("region", "Unknown")
        regulation = doc.get("regulation_name", doc.get("applicable_regulation", ""))
        summary = doc.get("summary", "")
        bullets = doc.get("rights_bullets", [])
        next_steps = doc.get("next_steps", [])
        comp_amount = doc.get("default_compensation_amount")
        comp_currency = doc.get("default_compensation_currency", "")
        tiers = doc.get("compensation_tiers", [])
        
        section = f"[{region} — {regulation}]\n"
        
        if summary:
            section += f"Summary: {summary}\n"
        
        if comp_amount:
            section += f"Compensation: {comp_currency}{comp_amount}\n"
        elif tiers:
            tier_text = ", ".join([
                f"{t.get('distance_km', 'N/A')}km → {t.get('currency','')}{t.get('amount','N/A')}"
                for t in tiers
            ])
            section += f"Compensation tiers: {tier_text}\n"
        
        if bullets:
            section += "Key rights:\n" + "\n".join(f"  • {b}" for b in bullets) + "\n"
        
        if next_steps:
            section += "Action steps:\n" + "\n".join(f"  {i+1}. {s}" for i, s in enumerate(next_steps[:4])) + "\n"
        
        sections.append(section)
    
    return "\n".join(sections)


def build_case_context(case) -> str:
    """Build base case context string used by all prompts"""
    flight_status = (case.meta_data or {}).get("flight_status", {})
    delay_dep = (flight_status.get("departure") or {}).get("delay", 0) or 0
    delay_arr = (flight_status.get("arrival") or {}).get("delay", 0) or 0
    aircraft = flight_status.get("aircraft", "")
    
    # ── Use actual flight date from live status if available ──
    scheduled_dep = (flight_status.get("departure") or {}).get("scheduled")
    if scheduled_dep:
        try:
            from datetime import datetime as dt
            flight_date_str = dt.fromisoformat(
                scheduled_dep.replace("Z", "+00:00")
            ).strftime("%B %d, %Y")
        except Exception:
            flight_date_str = case.disruption_date.strftime("%B %d, %Y")
    else:
        flight_date_str = case.disruption_date.strftime("%B %d, %Y")

    return f"""Flight: {case.flight_number} ({case.airline})
Route: {case.origin} → {case.destination}
Date: {flight_date_str}
Current Status: {case.current_status or 'Unknown'}
Severity: {case.severity.value}
Disruption Type: {case.disruption_type.value}
Departure Delay: {delay_dep} minutes
Arrival Delay: {delay_arr} minutes
Aircraft: {aircraft or 'N/A'}
PNR: {case.pnr or 'N/A'}"""


def build_weather_context(case) -> str:
    """Extract weather context from case meta_data"""
    weather = (case.meta_data or {}).get("weather", {})
    if not weather:
        return "Weather data not available."
    
    return f"""Weather at {weather.get('airport_code', case.destination)}:
Condition: {weather.get('condition', 'Unknown')}
Severity: {weather.get('severity', 'Unknown')}
Temperature: {weather.get('temp_min', 'N/A')}°–{weather.get('temp_max', 'N/A')}°C
Precipitation probability: {weather.get('precipitation_probability', 0)}%
Wind speed: {weather.get('wind_speed', 'N/A')} km/h"""


def build_flight_status_context(case) -> str:
    """Extract detailed flight status context from meta_data"""
    fs = (case.meta_data or {}).get("flight_status", {})
    if not fs:
        return "Live flight status not available."
    
    dep = fs.get("departure", {})
    arr = fs.get("arrival", {})
    
    return f"""Live Flight Status: {fs.get('status', 'unknown').upper()}
Departure airport: {dep.get('airport', 'N/A')} ({dep.get('iata', '')})
  Scheduled: {dep.get('scheduled', 'N/A')}
  Actual: {dep.get('actual', 'Not yet departed')}
  Delay: {dep.get('delay', 0) or 0} minutes
  Terminal: {dep.get('terminal', 'N/A')} · Gate: {dep.get('gate', 'N/A')}
Arrival airport: {arr.get('airport', 'N/A')} ({arr.get('iata', '')})
  Scheduled: {arr.get('scheduled', 'N/A')}
  Estimated: {arr.get('estimated', 'N/A')}
  Delay: {arr.get('delay', 0) or 0} minutes
  Terminal: {arr.get('terminal', 'N/A')}"""


def build_options_context(options: List) -> str:
    """Format disruption options into prompt context"""
    if not options:
        return "No alternative options have been generated yet."
    
    lines = []
    for opt in options[:4]:
        cost = f"${opt.estimated_cost}" if opt.estimated_cost else "Free"
        lines.append(f"- [{opt.option_type.value}] {opt.title} ({cost}): {opt.description or ''}")
    
    return "Available Options:\n" + "\n".join(lines)


# ── Specialized prompt builders ────────────────────────────────────────────

def build_compensation_prompt(
    case, rights_docs: List[Dict], history_text: str, user_message: str
) -> str:
    case_ctx = build_case_context(case)
    rights_ctx = format_rights_context(rights_docs)
    
    return f"""You are a flight disruption compensation specialist. Be direct, specific, and actionable.

CASE DETAILS:
{case_ctx}

APPLICABLE REGULATIONS FOR THIS ROUTE ({case.origin} → {case.destination}):
{rights_ctx}

CONVERSATION SO FAR:
{history_text or "New conversation."}

USER QUESTION: {user_message}

INSTRUCTIONS:
- Answer ONLY about compensation — how much, under which regulation, and exactly how to claim it
- Cite the specific regulation (EU261, Montreal Convention, etc.) and exact amounts in €/$/₹
- Give 2–3 concrete action steps the passenger should take RIGHT NOW
- If multiple regulations apply, explain which gives more benefit
- Do NOT repeat generic disclaimers like "consult a lawyer" unless truly necessary
- Be direct: 3–5 sentences max, then a numbered action list

RESPONSE:"""


def build_rights_prompt(
    case, rights_docs: List[Dict], history_text: str, user_message: str
) -> str:
    case_ctx = build_case_context(case)
    rights_ctx = format_rights_context(rights_docs)
    
    return f"""You are a passenger rights expert. Give precise, regulation-backed answers.

CASE DETAILS:
{case_ctx}

PASSENGER RIGHTS FOR THIS ROUTE ({case.origin} → {case.destination}):
{rights_ctx}

CONVERSATION SO FAR:
{history_text or "New conversation."}

USER QUESTION: {user_message}

INSTRUCTIONS:
- List the TOP 3 most relevant rights for THIS specific disruption type ({case.disruption_type.value})
- Reference the specific regulation name (not just "you have rights")
- Distinguish between what the passenger is GUARANTEED vs what they can REQUEST
- End with the single most important next step they should take today
- Keep it conversational, not legalese — 4–6 sentences total

RESPONSE:"""


def build_rebooking_prompt(
    case, options: List, history_text: str, user_message: str
) -> str:
    case_ctx = build_case_context(case)
    options_ctx = build_options_context(options)
    
    return f"""You are a flight rebooking assistant. Help the passenger pick the best option.

CASE DETAILS:
{case_ctx}

{options_ctx}

CONVERSATION SO FAR:
{history_text or "New conversation."}

USER QUESTION: {user_message}

INSTRUCTIONS:
- Recommend the BEST option from the list above with a clear reason why
- Compare cost, time, and convenience trade-offs briefly
- If asking about refund vs rebooking, explain which is better for their situation
- Mention what action to take (e.g. "click Contact on the AI 2439 card")
- Keep it to 3–4 sentences + one clear recommendation

RESPONSE:"""


def build_status_prompt(
    case, history_text: str, user_message: str
) -> str:
    case_ctx = build_case_context(case)
    flight_ctx = build_flight_status_context(case)
    weather_ctx = build_weather_context(case)
    
    return f"""You are a real-time flight status assistant. Give accurate, current information.

CASE DETAILS:
{case_ctx}

{flight_ctx}

{weather_ctx}

CONVERSATION SO FAR:
{history_text or "New conversation."}

USER QUESTION: {user_message}

INSTRUCTIONS:
- Describe the current flight situation clearly and conversationally
- If there's a delay, state the delay duration and connect it to weather if weather severity is medium/high
- Mention gate/terminal if available and relevant
- If the flight is in air, estimate arrival based on estimated time
- Do NOT say "I don't have real-time data" — you DO have the data above, use it
- Keep it to 2–4 sentences, be direct

RESPONSE:"""


def build_general_prompt(
    case, rights_docs: List[Dict], options: List,
    history_text: str, user_message: str
) -> str:
    case_ctx = build_case_context(case)
    rights_ctx = format_rights_context(rights_docs)
    options_ctx = build_options_context(options)
    flight_ctx = build_flight_status_context(case)
    weather_ctx = build_weather_context(case)
    
    return f"""You are an AI travel assistant helping a passenger with a flight disruption. 
Be specific, helpful, and reference actual data from the context below.

CASE DETAILS:
{case_ctx}

{flight_ctx}

{weather_ctx}

APPLICABLE REGULATIONS:
{rights_ctx}

{options_ctx}

CONVERSATION SO FAR:
{history_text or "New conversation."}

USER QUESTION: {user_message}

INSTRUCTIONS:
- Answer the question directly using the data provided above
- Be specific — mention flight numbers, amounts, times from the context
- Do NOT give generic travel advice — everything should be specific to THIS case
- If you reference a regulation, name it explicitly
- 3–5 sentences, friendly and professional tone

RESPONSE:"""
