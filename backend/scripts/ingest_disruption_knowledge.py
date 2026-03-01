"""
Ingest passenger rights knowledge and draft message templates into MongoDB.

Collections populated:
- passenger_rights (~50 documents)
- draft_message_templates (15 documents)

Run with:
    python scripts/ingest_disruption_knowledge.py --rights
    python scripts/ingest_disruption_knowledge.py --templates
    python scripts/ingest_disruption_knowledge.py --all

Idempotent — safe to re-run. Uses upserts.
"""
import sys
import os
import asyncio
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from app.core.mongo import connect_to_mongo, close_mongo_connection
from app.services.disruption_mongo_service import (
    save_rights,
    save_draft_template,
    ensure_indexes
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# =============================================================================
# PASSENGER RIGHTS DATA
# =============================================================================

def build_rights_data() -> list:
    """
    Build the full list of ~50 passenger rights documents.
    Each dict matches PassengerRightsDocument shape.
    """
    rights = []

    # =========================================================================
    # EU — EC 261/2004
    # =========================================================================

    EU_SOURCE_LINKS = [
        {
            "title": "EU Regulation 261/2004",
            "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32004R0261",
            "type": "regulation",
            "region": "EU"
        },
        {
            "title": "European Consumer Centre",
            "url": "https://ec.europa.eu/info/live-work-travel-eu/consumer-rights-and-complaints/resolve-your-consumer-complaint/european-consumer-centres-network-ecc-net_en",
            "type": "authority",
            "region": "EU"
        }
    ]

    EU_TIERS = [
        {"max_distance_km": 1500, "amount": 250, "currency": "EUR", "condition": "All flights ≤ 1500km"},
        {"max_distance_km": 3500, "amount": 400, "currency": "EUR", "condition": "Internal EU flights > 1500km or other flights 1500–3500km"},
        {"max_distance_km": 999999, "amount": 600, "currency": "EUR", "condition": "All flights > 3500km"}
    ]

    rights.append({
        "region": "EU",
        "disruption_type": "cancellation",
        "regulation_name": "EU Regulation 261/2004",
        "applicable_regulation": "EU261",
        "enforcement_body": "National Enforcement Body (e.g., CAA in Germany: Luftfahrt-Bundesamt, France: DGAC)",
        "summary": (
            "Under EU Regulation 261/2004, if your flight is cancelled with less than 14 days' notice, "
            "you are entitled to compensation of €250–€600 depending on flight distance. "
            "You also have the right to a full refund or re-routing, plus care (meals, refreshments, accommodation if overnight)."
        ),
        "rights_bullets": [
            "Compensation of €250 (≤1500km), €400 (1500–3500km), or €600 (>3500km) — unless extraordinary circumstances apply",
            "Full refund of ticket price within 7 days, OR re-routing to destination at earliest opportunity",
            "Right to care: meals and refreshments proportionate to waiting time",
            "Hotel accommodation and transport to/from hotel if overnight stay is required",
            "Two free phone calls, emails, or faxes",
            "Compensation may be reduced by 50% if re-routing gets you there within 2–4 hours of original arrival (distance dependent)",
            "No compensation if cancellation is due to extraordinary circumstances (severe weather, political instability, ATC strikes)"
        ],
        "compensation_tiers": EU_TIERS,
        "default_compensation_amount": None,
        "default_compensation_currency": "EUR",
        "next_steps": [
            "File a written claim with the airline immediately — keep your boarding pass and booking confirmation",
            "Request the reason for cancellation in writing from airline staff",
            "Keep all receipts for meals, accommodation, and transport incurred",
            "If airline refuses within 8 weeks, escalate to your country's National Enforcement Body",
            "Consider using an EU-certified ADR (Alternative Dispute Resolution) body",
            "Small claims court is an option for claims up to €5,000 in most EU countries"
        ],
        "source_links": EU_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "EU",
        "disruption_type": "delay",
        "regulation_name": "EU Regulation 261/2004",
        "applicable_regulation": "EU261",
        "enforcement_body": "National Enforcement Body (varies by country)",
        "summary": (
            "Under EU261, flight delays of 2+ hours entitle you to care (meals, refreshments). "
            "If the delay reaches 3+ hours at your final destination, you are entitled to the same "
            "compensation as a cancellation (€250–€600), unless extraordinary circumstances apply."
        ),
        "rights_bullets": [
            "2+ hour delay: right to meals, refreshments, and 2 free phone calls/emails",
            "3+ hour delay at final destination: compensation of €250–€600 (same tiers as cancellation)",
            "5+ hour delay: right to full refund AND return flight to point of departure if outbound leg is no longer useful",
            "Overnight delay: right to hotel accommodation and transport to/from hotel",
            "No compensation if delay is due to extraordinary circumstances (severe weather, ATC strikes, etc.)",
            "Compensation based on arrival delay at final destination, not departure delay"
        ],
        "compensation_tiers": EU_TIERS,
        "default_compensation_amount": None,
        "default_compensation_currency": "EUR",
        "next_steps": [
            "Request a 'Notice of Rights' from airline staff at the airport",
            "Keep all receipts for any expenses incurred during the delay",
            "Note the actual arrival time at final destination — this determines compensation eligibility",
            "File a claim with the airline if delay exceeds 3 hours at destination",
            "Escalate to National Enforcement Body if airline rejects your claim within 8 weeks"
        ],
        "source_links": EU_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "EU",
        "disruption_type": "overbooking",
        "regulation_name": "EU Regulation 261/2004",
        "applicable_regulation": "EU261",
        "enforcement_body": "National Enforcement Body (varies by country)",
        "summary": (
            "EU261 covers denied boarding due to overbooking. If you are involuntarily denied boarding, "
            "you are entitled to compensation of €250–€600, a full refund or re-routing, and care rights."
        ),
        "rights_bullets": [
            "Immediate right to compensation of €250–€600 depending on flight distance",
            "Choice between full refund within 7 days OR re-routing to final destination at earliest opportunity",
            "Right to care: meals, refreshments, accommodation if needed",
            "Airline must first ask for volunteers before denying boarding involuntarily",
            "If you volunteer to give up your seat, negotiate compensation directly with airline — you may waive EU261 rights",
            "Compensation reduced by 50% if re-routing gets you to destination within 2–4 hours of original time"
        ],
        "compensation_tiers": EU_TIERS,
        "default_compensation_amount": None,
        "default_compensation_currency": "EUR",
        "next_steps": [
            "Do not voluntarily give up your seat unless you are satisfied with the compensation offered",
            "Request compensation in writing at the airport before leaving",
            "Get the reason for denial in writing from airline staff",
            "File a formal claim with the airline if they refuse at the gate",
            "Escalate to National Enforcement Body if unresolved after 8 weeks"
        ],
        "source_links": EU_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "EU",
        "disruption_type": "missed_connection",
        "regulation_name": "EU Regulation 261/2004",
        "applicable_regulation": "EU261",
        "enforcement_body": "National Enforcement Body (varies by country)",
        "summary": (
            "If you miss a connecting flight due to a delay on a previous leg of the same booking, "
            "EU261 applies. If you arrive at your final destination 3+ hours late, you are entitled to compensation."
        ),
        "rights_bullets": [
            "EU261 applies if the entire itinerary is on a single booking and the connection is missed due to the airline",
            "Compensation of €250–€600 if you arrive at final destination 3+ hours late",
            "Right to re-routing to final destination at no extra cost",
            "Right to care (meals, refreshments, accommodation) during the wait",
            "No EU261 rights if the two flights were separate bookings",
            "Self-transfer connections on separate bookings: airline is not obligated to rebook you"
        ],
        "compensation_tiers": EU_TIERS,
        "default_compensation_amount": None,
        "default_compensation_currency": "EUR",
        "next_steps": [
            "Go immediately to the airline's transfer desk when you realize you will miss the connection",
            "Request re-routing to your final destination at no charge",
            "Keep all receipts for expenses during the wait",
            "Confirm your arrival time at final destination in writing",
            "File compensation claim based on total delay at final destination"
        ],
        "source_links": EU_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "EU",
        "disruption_type": "strike",
        "regulation_name": "EU Regulation 261/2004",
        "applicable_regulation": "EU261",
        "enforcement_body": "National Enforcement Body (varies by country)",
        "summary": (
            "Strikes by airline staff (pilots, cabin crew) are NOT considered extraordinary circumstances under EU261. "
            "You are still entitled to compensation. However, third-party strikes (ATC, airport staff) may qualify "
            "as extraordinary circumstances, potentially exempting the airline from compensation."
        ),
        "rights_bullets": [
            "Airline staff strikes (pilots, cabin crew): compensation IS owed — not an extraordinary circumstance",
            "ATC strikes or airport staff strikes: may be extraordinary circumstances — compensation possibly not owed",
            "Right to refund or re-routing regardless of the type of strike",
            "Right to care (meals, refreshments, accommodation) during the disruption",
            "EU Court of Justice ruling (Krüsemann, 2018): wildcat strikes by airline staff are NOT extraordinary",
            "Always request compensation — airline must prove extraordinary circumstances to avoid paying"
        ],
        "compensation_tiers": EU_TIERS,
        "default_compensation_amount": None,
        "default_compensation_currency": "EUR",
        "next_steps": [
            "Request the specific reason for the disruption in writing from the airline",
            "File a compensation claim regardless — let the airline prove extraordinary circumstances",
            "If airline claims ATC strike, verify this independently via the airport or news sources",
            "Escalate to National Enforcement Body if claim is rejected without clear justification"
        ],
        "source_links": EU_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "EU",
        "disruption_type": "weather",
        "regulation_name": "EU Regulation 261/2004",
        "applicable_regulation": "EU261",
        "enforcement_body": "National Enforcement Body (varies by country)",
        "summary": (
            "Severe weather is generally considered an extraordinary circumstance under EU261, "
            "which means the airline is NOT required to pay compensation. However, you are still entitled "
            "to a full refund or re-routing, and care rights (meals, accommodation) apply."
        ),
        "rights_bullets": [
            "Severe weather IS an extraordinary circumstance — compensation (€250–€600) typically NOT owed",
            "Right to full refund of ticket price OR re-routing to destination, even in weather cancellations",
            "Right to care: meals, refreshments proportionate to wait time",
            "Right to hotel accommodation and transport if overnight stay is required",
            "Airline must still provide care even if no compensation is owed",
            "If weather only affected some flights but not others on same route, you may still have a claim"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 0,
        "default_compensation_currency": "EUR",
        "next_steps": [
            "Request refund or re-routing immediately at the airline desk",
            "Claim meals and accommodation — these are owed regardless of weather",
            "Keep all receipts for care expenses",
            "If the weather was localised or other airlines flew the same route, file a compensation claim anyway",
            "Contact National Enforcement Body if airline refuses to provide care"
        ],
        "source_links": EU_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "EU",
        "disruption_type": "baggage_issue",
        "regulation_name": "Montreal Convention 1999",
        "applicable_regulation": "Montreal Convention",
        "enforcement_body": "National civil aviation authority or civil court",
        "summary": (
            "Baggage issues (lost, delayed, or damaged) on flights to/from/within the EU are governed by the "
            "Montreal Convention. Compensation is capped at approximately 1,288 SDR (roughly €1,400–€1,600) "
            "for lost or damaged baggage."
        ),
        "rights_bullets": [
            "Lost baggage: compensation up to 1,288 SDR (~€1,400) under Montreal Convention",
            "Delayed baggage: claim reasonable expenses for essential items purchased during delay",
            "Damaged baggage: compensation up to 1,288 SDR for the damage",
            "Must file a Property Irregularity Report (PIR) at the airport immediately",
            "Written claim must be submitted within 7 days for damage, 21 days for delayed baggage",
            "For lost baggage: baggage is considered 'lost' after 21 days",
            "EU261 does NOT cover baggage issues — Montreal Convention applies separately"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 1288,
        "default_compensation_currency": "SDR",
        "next_steps": [
            "File a Property Irregularity Report (PIR) at the baggage desk before leaving the airport",
            "Get your PIR reference number — you will need this for all future claims",
            "Keep all receipts for essential items purchased due to delayed baggage",
            "Submit written claim to airline within 7 days (damage) or 21 days (delayed)",
            "For lost baggage: wait 21 days then file a formal lost baggage claim",
            "If airline rejects claim, pursue through civil court or national aviation authority"
        ],
        "source_links": [
            {
                "title": "Montreal Convention 1999",
                "url": "https://www.icao.int/secretariat/legal/List%20of%20Parties/Mtl99_EN.pdf",
                "type": "regulation",
                "region": "EU"
            }
        ],
        "version": 1
    })

    rights.append({
        "region": "EU",
        "disruption_type": "other",
        "regulation_name": "EU Regulation 261/2004",
        "applicable_regulation": "EU261",
        "enforcement_body": "National Enforcement Body (varies by country)",
        "summary": (
            "For other types of disruptions on EU-regulated flights, EU261 provides general passenger protections. "
            "Contact your airline first, and escalate to the national enforcement body if unresolved."
        ),
        "rights_bullets": [
            "EU261 applies to flights departing from an EU airport, or arriving in EU on an EU carrier",
            "Right to information: airline must inform you of your rights in writing",
            "Right to care: meals and refreshments during any significant disruption",
            "Right to refund if your travel plans are fundamentally affected",
            "Montreal Convention provides additional coverage for personal injury or baggage issues"
        ],
        "compensation_tiers": EU_TIERS,
        "default_compensation_amount": None,
        "default_compensation_currency": "EUR",
        "next_steps": [
            "Request a written explanation of the disruption from the airline",
            "Ask for a 'Notice of Rights' document",
            "File a complaint with the airline in writing within 6 years (UK) or applicable limitation period",
            "Escalate to the National Enforcement Body in the departure country"
        ],
        "source_links": EU_SOURCE_LINKS,
        "version": 1
    })

    # =========================================================================
    # US — DOT Regulations
    # =========================================================================

    US_SOURCE_LINKS = [
        {
            "title": "U.S. DOT Airline Passenger Rights",
            "url": "https://www.transportation.gov/airconsumer/fly-rights",
            "type": "regulation",
            "region": "US"
        },
        {
            "title": "DOT Aviation Consumer Protection",
            "url": "https://www.transportation.gov/airconsumer",
            "type": "authority",
            "region": "US"
        }
    ]

    rights.append({
        "region": "US",
        "disruption_type": "cancellation",
        "regulation_name": "U.S. Department of Transportation Regulations",
        "applicable_regulation": "DOT Regulations",
        "enforcement_body": "U.S. Department of Transportation (DOT) — file at transportation.gov",
        "summary": (
            "U.S. law does NOT require airlines to compensate passengers for flight cancellations beyond a refund. "
            "However, you are entitled to a full cash refund to your original payment method for cancelled flights, "
            "even for non-refundable tickets. Many airlines offer additional amenities as customer service."
        ),
        "rights_bullets": [
            "Mandatory full cash refund to original payment method for all cancelled flights — no exceptions",
            "Refund applies even for non-refundable tickets when airline cancels the flight",
            "No mandatory compensation (cash, miles, vouchers) required under U.S. law",
            "Airlines may offer vouchers, rebooking, meals as customer service — but this is voluntary",
            "DOT 2024 rule: refunds must be issued within 7 days (credit card) or 20 days (other payment)",
            "If you accept a voucher instead of a refund, you waive your right to cash refund",
            "Right to rebook on next available flight at no extra charge (most airline policies)"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 0,
        "default_compensation_currency": "USD",
        "next_steps": [
            "Request a full cash refund directly with the airline — do not accept vouchers unless you prefer them",
            "If rebooking, ask to be placed on the next available flight at no charge",
            "Request meal vouchers as a customer service gesture — many airlines provide these voluntarily",
            "File a complaint with DOT at transportation.gov if airline refuses cash refund",
            "Consider travel insurance or credit card travel protection for additional compensation",
            "Check if your credit card has trip cancellation or interruption coverage"
        ],
        "source_links": US_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "US",
        "disruption_type": "delay",
        "regulation_name": "U.S. Department of Transportation Regulations",
        "applicable_regulation": "DOT Regulations",
        "enforcement_body": "U.S. Department of Transportation (DOT)",
        "summary": (
            "U.S. law does NOT require airlines to compensate passengers for flight delays. "
            "However, DOT tarmac delay rules apply: domestic flights cannot remain on tarmac for more than "
            "3 hours, international flights 4 hours, without allowing passengers to deplane."
        ),
        "rights_bullets": [
            "No mandatory cash compensation for flight delays under U.S. law",
            "Tarmac delay rule: domestic flights — must allow deplaning after 3 hours",
            "Tarmac delay rule: international flights — must allow deplaning after 4 hours",
            "Airlines must provide food and water after 2 hours on the tarmac",
            "Working lavatories and medical attention must be available throughout tarmac delay",
            "If delay causes you to miss a connection on the same booking, airline must rebook you",
            "Airlines may voluntarily offer meal vouchers, hotel, or miles as customer service"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 0,
        "default_compensation_currency": "USD",
        "next_steps": [
            "Ask airline staff for meal vouchers and accommodation if delay is significant",
            "If on tarmac for 2+ hours, airline must provide food and water — request it",
            "Request rebooking on next available flight if you miss a connection",
            "File a DOT complaint at transportation.gov if tarmac delay rules are violated",
            "Check your travel insurance or credit card for delay compensation coverage",
            "Keep all receipts for expenses incurred during the delay for insurance claims"
        ],
        "source_links": US_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "US",
        "disruption_type": "overbooking",
        "regulation_name": "U.S. Department of Transportation Regulations",
        "applicable_regulation": "DOT Regulations",
        "enforcement_body": "U.S. Department of Transportation (DOT)",
        "summary": (
            "U.S. DOT has the strongest involuntary bumping rules globally. If you are involuntarily denied "
            "boarding, you are entitled to cash compensation of 200%–400% of your one-way fare, capped at "
            "$775–$1,550, plus a full refund."
        ),
        "rights_bullets": [
            "Involuntary bump: 200% of one-way fare (max $775) if rebooked to arrive within 1–2 hours domestically",
            "Involuntary bump: 400% of one-way fare (max $1,550) if delay exceeds 2 hours domestically (4 hours internationally)",
            "You are also entitled to keep your original ticket and use it later, OR get a full refund",
            "Airlines must first ask for volunteers before involuntarily bumping passengers",
            "Volunteers can negotiate any compensation with the airline — no legal cap",
            "If you volunteer, get the compensation offer in writing before giving up your seat",
            "These rights apply to oversold flights — not weather or mechanical cancellations"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 1550,
        "default_compensation_currency": "USD",
        "next_steps": [
            "Do not give up your seat without getting compensation terms in writing",
            "Negotiate with gate agents for higher compensation, upgrades, or future travel credit",
            "If involuntarily bumped, request written documentation and immediate cash/check compensation",
            "File a DOT complaint at transportation.gov if airline refuses proper compensation",
            "You can still file a civil lawsuit for additional damages if applicable"
        ],
        "source_links": US_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "US",
        "disruption_type": "missed_connection",
        "regulation_name": "U.S. Department of Transportation Regulations",
        "applicable_regulation": "DOT Regulations",
        "enforcement_body": "U.S. Department of Transportation (DOT)",
        "summary": (
            "If you miss a connection on a single itinerary booking due to an airline-caused delay, "
            "U.S. airlines are contractually obligated to rebook you at no charge. No cash compensation "
            "is required by law, but rebooking on the next available flight is standard."
        ),
        "rights_bullets": [
            "Right to rebooking on next available flight at no charge if connection missed due to airline delay",
            "Applies only to connections on a single booking — separate bookings have no protection",
            "No mandatory cash compensation for missed connections under U.S. law",
            "Airline must rebook even on partner airlines if that gets you there sooner",
            "Request meal vouchers and accommodation as customer service if overnight stay is required",
            "If you self-connected (booked separately), you are on your own for rebooking costs"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 0,
        "default_compensation_currency": "USD",
        "next_steps": [
            "Go immediately to the airline's transfer desk or customer service",
            "Request rebooking on the next available flight to your destination at no charge",
            "Ask for meal vouchers and accommodation if you are stranded overnight",
            "Get all rebooking confirmations in writing or via email",
            "File DOT complaint if airline refuses to rebook you on a single-booking itinerary"
        ],
        "source_links": US_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "US",
        "disruption_type": "strike",
        "regulation_name": "U.S. Department of Transportation Regulations",
        "applicable_regulation": "DOT Regulations",
        "enforcement_body": "U.S. Department of Transportation (DOT)",
        "summary": (
            "U.S. law does not require compensation for strike-related cancellations. However, you are "
            "entitled to a full cash refund for cancelled flights. Airlines may rebook you voluntarily."
        ),
        "rights_bullets": [
            "Full cash refund required for any cancelled flight — including strike-related cancellations",
            "No mandatory compensation beyond refund for strike disruptions",
            "Airlines may offer voluntary rebooking, miles, or vouchers as customer service",
            "If your flight operates during a strike, you are on it — no changes without fees",
            "Check if your travel insurance covers strike-related disruptions"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 0,
        "default_compensation_currency": "USD",
        "next_steps": [
            "Request a full cash refund if your flight is cancelled due to a strike",
            "Ask about voluntary rebooking options without change fees",
            "File a travel insurance claim if your policy covers strikes",
            "File a DOT complaint if the airline refuses to refund a cancelled flight"
        ],
        "source_links": US_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "US",
        "disruption_type": "weather",
        "regulation_name": "U.S. Department of Transportation Regulations",
        "applicable_regulation": "DOT Regulations",
        "enforcement_body": "U.S. Department of Transportation (DOT)",
        "summary": (
            "Weather cancellations entitle you to a full cash refund under DOT rules. However, no additional "
            "compensation is required. Most airlines issue travel waivers during major weather events allowing "
            "free rebooking."
        ),
        "rights_bullets": [
            "Full cash refund required even for weather-related cancellations",
            "No mandatory compensation, meals, or accommodation for weather disruptions",
            "Most airlines issue 'weather waivers' — check airline website for free rebooking windows",
            "Travel insurance may cover weather-related expenses airlines won't",
            "DOT tarmac rules still apply even in weather delays — 3hr domestic, 4hr international limit"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 0,
        "default_compensation_currency": "USD",
        "next_steps": [
            "Check airline website for a weather waiver — this allows free rebooking",
            "Request a full refund if you choose not to travel",
            "Keep all receipts for expenses — file travel insurance claim if applicable",
            "Monitor airline app and airport for real-time updates"
        ],
        "source_links": US_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "US",
        "disruption_type": "baggage_issue",
        "regulation_name": "U.S. DOT Regulations + Montreal Convention",
        "applicable_regulation": "DOT + Montreal Convention",
        "enforcement_body": "U.S. Department of Transportation (DOT)",
        "summary": (
            "For domestic U.S. flights, DOT rules cap airline liability for lost/damaged baggage at $3,800 per "
            "passenger. For international flights, the Montreal Convention caps liability at ~1,288 SDR (~$1,700)."
        ),
        "rights_bullets": [
            "Domestic flights: airline liability up to $3,800 for lost, damaged, or delayed baggage",
            "International flights: Montreal Convention cap of ~1,288 SDR (~$1,700)",
            "File a claim before leaving the baggage area — get a Property Irregularity Report (PIR)",
            "For delayed baggage: claim reasonable essential expenses (clothing, toiletries)",
            "Airlines must refund checked baggage fees if baggage is lost",
            "File written claim within 30 days for delayed baggage, 7 days for damage (international)"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 3800,
        "default_compensation_currency": "USD",
        "next_steps": [
            "File a Property Irregularity Report (PIR) at the baggage desk before leaving the airport",
            "Keep your baggage claim ticket and boarding pass",
            "Submit written claim to airline with receipts for essential purchases",
            "File DOT complaint if airline refuses reasonable compensation",
            "Check your travel insurance and credit card for additional baggage coverage"
        ],
        "source_links": US_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "US",
        "disruption_type": "other",
        "regulation_name": "U.S. Department of Transportation Regulations",
        "applicable_regulation": "DOT Regulations",
        "enforcement_body": "U.S. Department of Transportation (DOT)",
        "summary": (
            "For other disruptions on U.S. domestic or U.S.-originating flights, DOT consumer protection "
            "rules apply. The key right is always a full cash refund if the airline cancels or significantly "
            "changes your flight."
        ),
        "rights_bullets": [
            "Full cash refund if airline cancels or makes a significant schedule change you don't accept",
            "DOT defines 'significant change' as: 3+ hours domestic, 6+ hours international departure change",
            "Seat downgrade: entitled to refund of fare difference",
            "Right to information: airlines must disclose fees and rules at time of booking",
            "Tarmac delay protections apply regardless of disruption cause"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 0,
        "default_compensation_currency": "USD",
        "next_steps": [
            "Request a cash refund for any significant airline-initiated change",
            "File a complaint at transportation.gov/airconsumer",
            "Contact your credit card company if airline refuses and you paid by card",
            "Check travel insurance policy for coverage of your specific disruption"
        ],
        "source_links": US_SOURCE_LINKS,
        "version": 1
    })

    # =========================================================================
    # UK — UK261 (post-Brexit)
    # =========================================================================

    UK_SOURCE_LINKS = [
        {
            "title": "UK Civil Aviation Authority — Passenger Rights",
            "url": "https://www.caa.co.uk/passengers-and-public/resolving-travel-problems/disrupted-travel/your-rights-when-flights-are-disrupted/",
            "type": "regulation",
            "region": "UK"
        },
        {
            "title": "UK Retained EU Law 261/2004",
            "url": "https://www.legislation.gov.uk/eur/2004/261/contents",
            "type": "regulation",
            "region": "UK"
        }
    ]

    UK_TIERS = [
        {"max_distance_km": 1500, "amount": 220, "currency": "GBP", "condition": "All flights ≤ 1500km"},
        {"max_distance_km": 3500, "amount": 350, "currency": "GBP", "condition": "Internal UK/EU flights > 1500km or other flights 1500–3500km"},
        {"max_distance_km": 999999, "amount": 520, "currency": "GBP", "condition": "All flights > 3500km"}
    ]

    for disruption_type, summary, bullets in [
        (
            "cancellation",
            "Under UK261 (retained EU law post-Brexit), if your UK-regulated flight is cancelled with less than 14 days' notice, you are entitled to compensation of £220–£520 depending on distance, plus a full refund or re-routing.",
            [
                "Compensation of £220 (≤1500km), £350 (1500–3500km), or £520 (>3500km) — unless extraordinary circumstances",
                "Full refund within 7 days OR re-routing to destination at earliest opportunity",
                "Right to care: meals, refreshments, accommodation if overnight stay needed",
                "No compensation if cancellation is due to extraordinary circumstances (severe weather, ATC strikes)",
                "UK CAA is the enforcement body — file complaints at caa.co.uk",
                "CEDR and Aviation ADR are approved UK ADR schemes for disputes"
            ]
        ),
        (
            "delay",
            "UK261 mirrors EU261 for delays. If your flight arrives 3+ hours late at your final destination, you are entitled to compensation of £220–£520. Care rights apply from 2+ hours delay.",
            [
                "2+ hour delay: right to meals, refreshments, and 2 free communications",
                "3+ hour arrival delay at final destination: compensation of £220–£520",
                "5+ hour delay: right to full refund AND return flight to origin",
                "Overnight delay: hotel accommodation and transport to/from hotel",
                "No compensation for extraordinary circumstances (severe weather, ATC strikes)"
            ]
        ),
        (
            "overbooking",
            "UK261 applies to denied boarding on UK-regulated flights. Compensation of £220–£520 plus a refund or re-routing.",
            [
                "Immediate compensation of £220–£520 if involuntarily denied boarding",
                "Choice of full refund or re-routing to destination",
                "Right to care during the wait",
                "Airline must ask for volunteers first",
                "UK CAA enforces these rights — escalate if airline refuses"
            ]
        ),
        (
            "missed_connection",
            "UK261 applies to missed connections on a single booking on UK-regulated flights. Arrival delay of 3+ hours at final destination entitles you to compensation.",
            [
                "UK261 applies if entire itinerary is on single booking and connection missed due to airline",
                "Compensation if arriving 3+ hours late at final destination",
                "Right to re-routing at no extra cost",
                "Right to care during the wait",
                "No rights if flights were booked separately"
            ]
        ),
        (
            "strike",
            "Airline staff strikes on UK carriers are not extraordinary circumstances. You are entitled to compensation. ATC or airport strikes may be extraordinary circumstances.",
            [
                "Airline staff strikes: compensation IS owed",
                "ATC/airport strikes: may be extraordinary circumstances — compensation possibly not owed",
                "Right to refund or re-routing regardless",
                "Right to care during the disruption",
                "UK CAA enforces — file at caa.co.uk if refused"
            ]
        ),
        (
            "weather",
            "Severe weather is an extraordinary circumstance under UK261. No compensation is owed, but you are still entitled to a full refund or re-routing, and care rights apply.",
            [
                "No compensation for severe weather disruptions",
                "Full refund or re-routing still required",
                "Care rights (meals, accommodation) still apply",
                "Airline must still look after you even if no compensation is owed",
                "ATOL protection may provide additional cover for package holidays"
            ]
        ),
        (
            "baggage_issue",
            "Baggage issues on UK flights are covered by the Montreal Convention, capped at ~1,288 SDR (~£1,000–£1,100). File a Property Irregularity Report at the airport.",
            [
                "Montreal Convention applies: compensation up to ~1,288 SDR for lost/damaged baggage",
                "Must file Property Irregularity Report (PIR) at the airport before leaving",
                "7-day written claim deadline for damage, 21 days for delayed baggage",
                "Keep all receipts for essential purchases during baggage delay",
                "UK CAA can mediate disputes with airlines"
            ]
        ),
        (
            "other",
            "For other disruptions on UK-regulated flights, UK261 provides general protections. The UK CAA is the enforcement body.",
            [
                "UK261 applies to flights departing UK, or arriving in UK on UK/EU carrier",
                "Right to information and written notice of rights",
                "Right to care during significant disruptions",
                "Right to refund if airline makes significant changes",
                "File complaints with UK CAA at caa.co.uk"
            ]
        ),
    ]:
        rights.append({
            "region": "UK",
            "disruption_type": disruption_type,
            "regulation_name": "UK Retained EU Law 261/2004 (UK261)",
            "applicable_regulation": "UK261",
            "enforcement_body": "UK Civil Aviation Authority (CAA) — caa.co.uk",
            "summary": summary,
            "rights_bullets": bullets,
            "compensation_tiers": UK_TIERS if disruption_type not in ("weather", "baggage_issue", "other") else [],
            "default_compensation_amount": None,
            "default_compensation_currency": "GBP",
            "next_steps": [
                "File written claim with airline immediately",
                "Keep all receipts and documentation",
                "Escalate to UK CAA if unresolved after 8 weeks",
                "Use CEDR or Aviation ADR for alternative dispute resolution"
            ],
            "source_links": UK_SOURCE_LINKS,
            "version": 1
        })

    # =========================================================================
    # IN — DGCA Regulations
    # =========================================================================

    IN_SOURCE_LINKS = [
        {
            "title": "DGCA Civil Aviation Requirements — Passenger Services",
            "url": "https://dgca.gov.in/digigov-portal/",
            "type": "regulation",
            "region": "IN"
        }
    ]

    rights.append({
        "region": "IN",
        "disruption_type": "cancellation",
        "regulation_name": "DGCA Civil Aviation Requirements (CAR) Section 3, Series M Part IV",
        "applicable_regulation": "DGCA CAR",
        "enforcement_body": "Directorate General of Civil Aviation (DGCA) India",
        "summary": (
            "Indian DGCA regulations require airlines to compensate passengers for cancelled domestic flights. "
            "If cancelled with less than 2 weeks notice, compensation of INR 5,000–10,000 applies. "
            "International routes follow Montreal Convention."
        ),
        "rights_bullets": [
            "Cancellation < 2 weeks notice: compensation of INR 5,000 (short routes) to INR 10,000 (long routes)",
            "Right to full refund within 7 days, or re-routing at no additional cost",
            "Right to meals and refreshments if wait exceeds 2 hours",
            "Hotel accommodation if overnight stay required due to cancellation",
            "These rights apply only to domestic flights — international routes follow Montreal Convention",
            "Airline must inform you of the cancellation reason and your rights"
        ],
        "compensation_tiers": [
            {"max_distance_km": 1500, "amount": 5000, "currency": "INR", "condition": "Domestic short routes"},
            {"max_distance_km": 999999, "amount": 10000, "currency": "INR", "condition": "Domestic long routes"}
        ],
        "default_compensation_amount": 5000,
        "default_compensation_currency": "INR",
        "next_steps": [
            "Request written confirmation of cancellation and reason from airline",
            "Claim compensation at the airline counter before leaving the airport",
            "Request meals if wait is 2+ hours",
            "File complaint with DGCA at dgca.gov.in if airline refuses",
            "Consumer Forum is an option for unresolved disputes"
        ],
        "source_links": IN_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "IN",
        "disruption_type": "delay",
        "regulation_name": "DGCA Civil Aviation Requirements (CAR)",
        "applicable_regulation": "DGCA CAR",
        "enforcement_body": "Directorate General of Civil Aviation (DGCA) India",
        "summary": (
            "DGCA regulations require Indian airlines to provide meals after 2-hour delays and hotel accommodation "
            "after 6-hour delays on domestic flights. No cash compensation is mandated for delays under 6 hours."
        ),
        "rights_bullets": [
            "2+ hour delay: right to meals and refreshments",
            "6+ hour delay: right to hotel accommodation and transport",
            "6+ hour delay: right to full refund if you choose not to travel",
            "No mandatory cash compensation for delays under 6 hours",
            "Airline must keep passengers informed of delay reasons and updates",
            "These apply to domestic Indian flights only"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 0,
        "default_compensation_currency": "INR",
        "next_steps": [
            "Request meals at the airport after 2 hours — airline is obligated to provide",
            "Request hotel voucher if delay extends to 6+ hours",
            "Claim refund if you opt not to travel on a 6+ hour delay",
            "File complaint with DGCA if airline refuses to provide care",
            "Keep all receipts if you purchase food/accommodation and airline refuses to provide"
        ],
        "source_links": IN_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "IN",
        "disruption_type": "overbooking",
        "regulation_name": "DGCA Civil Aviation Requirements (CAR)",
        "applicable_regulation": "DGCA CAR",
        "enforcement_body": "Directorate General of Civil Aviation (DGCA) India",
        "summary": (
            "DGCA regulations provide compensation for denied boarding due to overbooking on domestic Indian flights. "
            "Compensation ranges from INR 5,000 to INR 20,000 depending on route length and alternate flight timing."
        ),
        "rights_bullets": [
            "Denied boarding: compensation of INR 5,000–20,000 depending on route and delay to alternate flight",
            "Right to alternate flight at no charge, or full refund",
            "Airline must ask for volunteers before involuntary bumping",
            "If rebooked within 1 hour: compensation at lower end of range",
            "If no alternate flight within 24 hours: full refund + higher compensation",
            "Meals and refreshments while waiting for alternate flight"
        ],
        "compensation_tiers": [
            {"max_distance_km": 1500, "amount": 5000, "currency": "INR", "condition": "Rebooked within 1 hour"},
            {"max_distance_km": 999999, "amount": 20000, "currency": "INR", "condition": "No flight within 24 hours"}
        ],
        "default_compensation_amount": 10000,
        "default_compensation_currency": "INR",
        "next_steps": [
            "Do not give up your seat without getting written compensation confirmation",
            "Request compensation at the airport check-in counter",
            "File complaint with DGCA at dgca.gov.in if denied",
            "Consumer Forum for unresolved disputes"
        ],
        "source_links": IN_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "IN",
        "disruption_type": "other",
        "regulation_name": "DGCA Civil Aviation Requirements (CAR)",
        "applicable_regulation": "DGCA CAR",
        "enforcement_body": "Directorate General of Civil Aviation (DGCA) India",
        "summary": (
            "For other disruptions on Indian domestic flights, DGCA regulations provide general consumer protections. "
            "For international routes, the Montreal Convention applies."
        ),
        "rights_bullets": [
            "DGCA CAR applies to all scheduled domestic flights in India",
            "Montreal Convention applies to international flights to/from India",
            "Right to information and written explanation of disruption",
            "Right to care proportionate to disruption length",
            "File grievances at dgca.gov.in or through AirSeva portal"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 0,
        "default_compensation_currency": "INR",
        "next_steps": [
            "Contact airline's customer service first",
            "File complaint on AirSeva portal (airsewa.gov.in)",
            "Escalate to DGCA at dgca.gov.in",
            "Consumer Forum as final escalation option"
        ],
        "source_links": IN_SOURCE_LINKS,
        "version": 1
    })

    # =========================================================================
    # CA — APPR (Air Passenger Protection Regulations)
    # =========================================================================

    CA_SOURCE_LINKS = [
        {
            "title": "Canada Air Passenger Protection Regulations (APPR)",
            "url": "https://otc-cta.gc.ca/eng/air-passenger-protection-regulations",
            "type": "regulation",
            "region": "CA"
        },
        {
            "title": "Canadian Transportation Agency",
            "url": "https://otc-cta.gc.ca/eng/air-travel",
            "type": "authority",
            "region": "CA"
        }
    ]

    CA_TIERS = [
        {"max_distance_km": 999999, "amount": 400, "currency": "CAD", "condition": "Delay 3–6 hours at destination (large airline)"},
        {"max_distance_km": 999999, "amount": 700, "currency": "CAD", "condition": "Delay 6–9 hours at destination (large airline)"},
        {"max_distance_km": 999999, "amount": 1000, "currency": "CAD", "condition": "Delay 9+ hours at destination (large airline)"}
    ]

    rights.append({
        "region": "CA",
        "disruption_type": "cancellation",
        "regulation_name": "Air Passenger Protection Regulations (APPR) 2019",
        "applicable_regulation": "APPR",
        "enforcement_body": "Canadian Transportation Agency (CTA)",
        "summary": (
            "Canada's APPR provides compensation of CAD $400–$1,000 for flight cancellations that are within "
            "the airline's control and not safety-related. You are also entitled to rebooking and care."
        ),
        "rights_bullets": [
            "Cancellation within airline's control (not safety): CAD $400 (large), $125 (small) for 3–6hr delay to rebooking",
            "CAD $700/$250 for 6–9hr delay, CAD $1,000/$500 for 9+ hr delay to rebooking",
            "Right to rebooking on next available flight at no charge",
            "Right to care: food/drink after 2 hours, hotel if overnight required",
            "No compensation if cancellation is due to safety reasons or outside airline's control",
            "Large airlines: Air Canada, WestJet, Porter, Swoop — higher compensation applies"
        ],
        "compensation_tiers": CA_TIERS,
        "default_compensation_amount": 400,
        "default_compensation_currency": "CAD",
        "next_steps": [
            "Request written explanation of cancellation reason from airline",
            "File compensation claim with airline — they have 30 days to respond",
            "If claim rejected, file with Canadian Transportation Agency (CTA)",
            "Keep all receipts for care expenses",
            "CTA adjudication is free for passengers"
        ],
        "source_links": CA_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "CA",
        "disruption_type": "delay",
        "regulation_name": "Air Passenger Protection Regulations (APPR) 2019",
        "applicable_regulation": "APPR",
        "enforcement_body": "Canadian Transportation Agency (CTA)",
        "summary": (
            "Canada's APPR provides compensation for delays within the airline's control. "
            "Large airlines must pay CAD $400–$1,000 depending on total delay at destination."
        ),
        "rights_bullets": [
            "Delay within airline's control: CAD $400 (3–6hrs), $700 (6–9hrs), $1,000 (9+hrs) — large airlines",
            "Small airline rates: CAD $125 (3–6hrs), $250 (6–9hrs), $500 (9+hrs)",
            "Right to food and drink after 2-hour delay",
            "Right to hotel accommodation if overnight delay is within airline's control",
            "No compensation for safety-related delays or delays outside airline's control",
            "Communication updates required every 30 minutes during delay"
        ],
        "compensation_tiers": CA_TIERS,
        "default_compensation_amount": 400,
        "default_compensation_currency": "CAD",
        "next_steps": [
            "Ask airline to confirm delay cause in writing",
            "Claim meals and accommodation if applicable",
            "File compensation claim with airline after travel",
            "Escalate to CTA if airline refuses within 30 days",
            "CTA complaint process is free and binding"
        ],
        "source_links": CA_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "CA",
        "disruption_type": "overbooking",
        "regulation_name": "Air Passenger Protection Regulations (APPR) 2019",
        "applicable_regulation": "APPR",
        "enforcement_body": "Canadian Transportation Agency (CTA)",
        "summary": (
            "APPR provides strong compensation for denied boarding due to overbooking. "
            "Passengers involuntarily bumped are entitled to CAD $900–$2,400 depending on delay to alternate flight."
        ),
        "rights_bullets": [
            "Denied boarding: CAD $900 if rebooked within 6 hours, $1,800 if 6–9 hours, $2,400 if 9+ hours",
            "Right to rebooking on next available flight at no charge",
            "Right to care during the wait",
            "Airline must ask for volunteers first",
            "Compensation must be paid within 48 hours in cash, voucher, or points (passenger's choice)",
            "You can refuse non-cash compensation and demand cash equivalent"
        ],
        "compensation_tiers": [
            {"max_distance_km": 999999, "amount": 900, "currency": "CAD", "condition": "Rebooked within 6 hours"},
            {"max_distance_km": 999999, "amount": 1800, "currency": "CAD", "condition": "Rebooked 6–9 hours later"},
            {"max_distance_km": 999999, "amount": 2400, "currency": "CAD", "condition": "Rebooked 9+ hours later"}
        ],
        "default_compensation_amount": 900,
        "default_compensation_currency": "CAD",
        "next_steps": [
            "Request cash compensation — you have the right to refuse vouchers",
            "Get all compensation terms in writing before giving up your seat",
            "File CTA complaint if airline refuses or delays payment beyond 48 hours"
        ],
        "source_links": CA_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "CA",
        "disruption_type": "other",
        "regulation_name": "Air Passenger Protection Regulations (APPR) 2019",
        "applicable_regulation": "APPR",
        "enforcement_body": "Canadian Transportation Agency (CTA)",
        "summary": (
            "Canada's APPR provides broad passenger protections. The CTA is the enforcement body. "
            "For international flights, Montreal Convention also applies."
        ),
        "rights_bullets": [
            "APPR applies to all flights operated by Canadian carriers and all flights to/from Canada",
            "Right to communication updates during any disruption",
            "Right to care proportionate to disruption length",
            "Lost/damaged baggage: Montreal Convention applies (up to ~1,288 SDR)",
            "CTA adjudication is free for passengers"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 0,
        "default_compensation_currency": "CAD",
        "next_steps": [
            "File claim with airline first — 30-day response deadline",
            "Escalate to CTA at otc-cta.gc.ca if unresolved",
            "CTA process is free and decisions are binding on airlines"
        ],
        "source_links": CA_SOURCE_LINKS,
        "version": 1
    })

    # =========================================================================
    # AU — Australian Consumer Law
    # =========================================================================

    AU_SOURCE_LINKS = [
        {
            "title": "Australian Competition and Consumer Commission — Air Travel",
            "url": "https://www.accc.gov.au/consumers/consumer-rights-guarantees/travel",
            "type": "authority",
            "region": "AU"
        },
        {
            "title": "Airline Customer Advocate",
            "url": "https://www.airlinecustomeradvocate.com.au/",
            "type": "authority",
            "region": "AU"
        }
    ]

    for disruption_type, summary, bullets in [
        (
            "cancellation",
            "Australian Consumer Law requires airlines to remedy cancellations within a reasonable time. There is no fixed compensation amount — remedies depend on whether the airline caused the disruption or it was outside their control.",
            [
                "Cancellation within airline's control: right to refund or re-routing, reasonable expense reimbursement",
                "Cancellation outside airline's control (weather): right to refund, but no mandatory care expenses",
                "No fixed compensation amounts under Australian law",
                "Australian Consumer Law guarantees that services are provided with due care and skill",
                "Airlines must provide accurate information about delays and cancellations",
                "Qantas and Jetstar have specific customer commitments — check their policies"
            ]
        ),
        (
            "delay",
            "No fixed compensation for delays under Australian law. However, Consumer Law guarantees may apply for significant delays. Airlines may voluntarily provide meal vouchers and accommodation.",
            [
                "No mandatory cash compensation for delays",
                "Australian Consumer Law may apply if delay is due to airline negligence",
                "Airlines may voluntarily provide care — ask gate agents for meal vouchers",
                "For international flights, Montreal Convention provides some protections",
                "Airline Ombudsman can mediate disputes",
                "Travel insurance is strongly recommended for Australian travellers"
            ]
        ),
        (
            "overbooking",
            "Australia has no specific overbooking regulation. However, Australian Consumer Law may entitle you to remedies. Airlines typically offer voluntary compensation for volunteers, and care for involuntary bumps.",
            [
                "No mandatory compensation under Australian law for overbooking",
                "Australian Consumer Law: airline must remedy the situation",
                "Request compensation in writing — document everything",
                "Airline Ombudsman (AFCA equivalent) can assist with disputes",
                "International flights: check if EU261 or another regulation applies based on carrier/route"
            ]
        ),
        (
            "other",
            "For other disruptions, Australian Consumer Law and airline-specific policies apply. The Airline Customer Advocate provides free dispute resolution.",
            [
                "Australian Consumer Law guarantees apply to all airline services",
                "Right to accurate information and timely updates",
                "Airline Customer Advocate provides free mediation",
                "International flights: Montreal Convention for baggage and injury",
                "Travel insurance is recommended for comprehensive coverage"
            ]
        ),
    ]:
        rights.append({
            "region": "AU",
            "disruption_type": disruption_type,
            "regulation_name": "Australian Consumer Law + Airline Policies",
            "applicable_regulation": "Australian Consumer Law",
            "enforcement_body": "ACCC + Airline Customer Advocate (airlinecustomeradvocate.com.au)",
            "summary": summary,
            "rights_bullets": bullets,
            "compensation_tiers": [],
            "default_compensation_amount": 0,
            "default_compensation_currency": "AUD",
            "next_steps": [
                "Submit formal complaint to airline customer service in writing",
                "Escalate to Airline Customer Advocate at airlinecustomeradvocate.com.au",
                "File ACCC complaint if airline breaches Consumer Law guarantees",
                "Consider travel insurance claim for additional coverage"
            ],
            "source_links": AU_SOURCE_LINKS,
            "version": 1
        })

    # =========================================================================
    # AE — GCAA Regulations (UAE)
    # =========================================================================

    AE_SOURCE_LINKS = [
        {
            "title": "UAE General Civil Aviation Authority — Passenger Rights",
            "url": "https://www.gcaa.gov.ae/en/Pages/default.aspx",
            "type": "authority",
            "region": "AE"
        }
    ]

    rights.append({
        "region": "AE",
        "disruption_type": "cancellation",
        "regulation_name": "UAE GCAA Consumer Protection Regulations",
        "applicable_regulation": "UAE GCAA Regulations",
        "enforcement_body": "General Civil Aviation Authority (GCAA) — gcaa.gov.ae",
        "summary": (
            "The UAE GCAA provides passenger protections for flights departing UAE airports. "
            "For cancellations, you are entitled to a full refund or re-routing, and care at the airport. "
            "Compensation amounts depend on airline policy and route."
        ),
        "rights_bullets": [
            "Right to full refund or re-routing for cancelled flights",
            "Right to care: meals and refreshments at the airport",
            "Hotel accommodation if overnight stay required",
            "Airline must inform you of your rights and cancellation reason",
            "Emirates, Etihad, and flydubai have specific customer service commitments",
            "For EU-destination flights on EU carriers: EU261 may also apply"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 0,
        "default_compensation_currency": "AED",
        "next_steps": [
            "Request refund or re-routing at the airline desk",
            "Ask for meal vouchers and accommodation if required",
            "File complaint with GCAA at gcaa.gov.ae if airline refuses",
            "Check if EU261 applies if flying to/from EU on EU carrier"
        ],
        "source_links": AE_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "AE",
        "disruption_type": "delay",
        "regulation_name": "UAE GCAA Consumer Protection Regulations",
        "applicable_regulation": "UAE GCAA Regulations",
        "enforcement_body": "General Civil Aviation Authority (GCAA)",
        "summary": (
            "UAE regulations require airlines to provide care for significant delays. Emirates and Etihad "
            "have strong voluntary customer service policies. No fixed cash compensation is mandated."
        ),
        "rights_bullets": [
            "Right to meals and refreshments for significant delays",
            "Hotel accommodation for overnight delays",
            "Right to accurate updates and information",
            "No mandatory cash compensation under UAE law",
            "Emirates and Etihad typically provide generous care voluntarily",
            "Montreal Convention applies for international flight protections"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 0,
        "default_compensation_currency": "AED",
        "next_steps": [
            "Request meal vouchers from airline staff",
            "Request hotel accommodation if delay is overnight",
            "File GCAA complaint if airline refuses to provide care",
            "Check airline-specific policies for voluntary compensation"
        ],
        "source_links": AE_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "AE",
        "disruption_type": "other",
        "regulation_name": "UAE GCAA Consumer Protection Regulations",
        "applicable_regulation": "UAE GCAA Regulations",
        "enforcement_body": "General Civil Aviation Authority (GCAA)",
        "summary": (
            "UAE GCAA provides general consumer protections for aviation. File complaints with GCAA "
            "for unresolved issues. Montreal Convention applies for international flights."
        ),
        "rights_bullets": [
            "GCAA regulates all flights departing UAE airports",
            "Right to information and care during disruptions",
            "Montreal Convention for international baggage and injury claims",
            "GCAA complaint process available at gcaa.gov.ae",
            "Dubai Economy (DED) for general consumer complaints"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 0,
        "default_compensation_currency": "AED",
        "next_steps": [
            "Contact airline customer service first",
            "File GCAA complaint at gcaa.gov.ae",
            "Contact Dubai Economy for consumer protection issues"
        ],
        "source_links": AE_SOURCE_LINKS,
        "version": 1
    })

    # =========================================================================
    # GENERAL — Montreal Convention + Generic
    # =========================================================================

    GENERAL_SOURCE_LINKS = [
        {
            "title": "Montreal Convention 1999 — ICAO",
            "url": "https://www.icao.int/secretariat/legal/List%20of%20Parties/Mtl99_EN.pdf",
            "type": "regulation",
            "region": "GENERAL"
        },
        {
            "title": "IATA Passenger Rights Information",
            "url": "https://www.iata.org/en/programs/passenger/passenger-rights/",
            "type": "authority",
            "region": "GENERAL"
        }
    ]

    rights.append({
        "region": "GENERAL",
        "disruption_type": "cancellation",
        "regulation_name": "Montreal Convention 1999 + General Airline Policies",
        "applicable_regulation": "Montreal Convention",
        "enforcement_body": "National civil aviation authority of departure country",
        "summary": (
            "For flights not covered by specific regional regulations, the Montreal Convention provides "
            "a baseline of passenger protections for international travel. Contact your airline directly "
            "and check the regulations of your departure country."
        ),
        "rights_bullets": [
            "Montreal Convention covers international flights between signatory countries (most major nations)",
            "Right to full refund per airline's terms and conditions",
            "Most airlines voluntarily offer rebooking at no charge for cancelled flights",
            "Check airline's Conditions of Carriage for specific rights",
            "Credit card travel protection may provide additional coverage",
            "Travel insurance strongly recommended for international travel"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 0,
        "default_compensation_currency": "USD",
        "next_steps": [
            "Request refund or rebooking directly from airline",
            "Review your airline's Conditions of Carriage document",
            "Check regulations of your departure country's aviation authority",
            "File travel insurance claim if applicable",
            "Contact national consumer protection agency as last resort"
        ],
        "source_links": GENERAL_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "GENERAL",
        "disruption_type": "delay",
        "regulation_name": "Montreal Convention 1999 + General Airline Policies",
        "applicable_regulation": "Montreal Convention",
        "enforcement_body": "National civil aviation authority of departure country",
        "summary": (
            "Outside specific regional regulations, there is generally no mandatory cash compensation for delays. "
            "Airlines may voluntarily provide care. The Montreal Convention provides some international protections."
        ),
        "rights_bullets": [
            "No universal mandatory compensation for delays outside EU/UK/CA/US",
            "Montreal Convention may apply for international delay-related consequential losses",
            "Most airlines provide voluntary care (meals, accommodation) for significant delays",
            "Check airline's Conditions of Carriage for specific delay commitments",
            "Travel insurance is the most reliable protection for delay expenses"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 0,
        "default_compensation_currency": "USD",
        "next_steps": [
            "Ask airline staff for meal vouchers and accommodation",
            "Keep all receipts for travel insurance claim",
            "Review airline's delay policy on their website",
            "Check if departure country has specific delay regulations"
        ],
        "source_links": GENERAL_SOURCE_LINKS,
        "version": 1
    })

    rights.append({
        "region": "GENERAL",
        "disruption_type": "other",
        "regulation_name": "Montreal Convention 1999 + General Airline Policies",
        "applicable_regulation": "Montreal Convention",
        "enforcement_body": "National civil aviation authority of departure country",
        "summary": (
            "For disruptions in regions without specific passenger rights legislation, rely on your airline's "
            "Conditions of Carriage, travel insurance, and the Montreal Convention for international flights."
        ),
        "rights_bullets": [
            "Montreal Convention is the international baseline for air travel rights",
            "Airline's Conditions of Carriage define your contractual rights",
            "Travel insurance provides the most comprehensive coverage",
            "Credit card travel protection may offer additional benefits",
            "IATA member airlines must follow IATA Passenger Services Conference Resolutions"
        ],
        "compensation_tiers": [],
        "default_compensation_amount": 0,
        "default_compensation_currency": "USD",
        "next_steps": [
            "Review your airline's Conditions of Carriage",
            "Contact the national civil aviation authority of your departure country",
            "File a travel insurance claim",
            "Consider small claims court for significant financial losses"
        ],
        "source_links": GENERAL_SOURCE_LINKS,
        "version": 1
    })

    return rights


# =============================================================================
# DRAFT MESSAGE TEMPLATES DATA
# =============================================================================

def build_templates_data() -> list:
    """
    Build the full list of draft message template documents.
    Pulls body content from message_templates.py and adds metadata.
    """
    from app.ai.message_templates import (
        AIRLINE_REFUND_FORMAL, AIRLINE_REFUND_FIRM, AIRLINE_REFUND_FRIENDLY,
        AIRLINE_REBOOKING_FORMAL,
        AIRLINE_ALTERNATIVE_FORMAL, AIRLINE_ALTERNATIVE_FIRM, AIRLINE_ALTERNATIVE_FRIENDLY,
        HOTEL_CANCELLATION_FORMAL, HOTEL_CANCELLATION_FRIENDLY,
        INSURANCE_CLAIM_FORMAL, INSURANCE_CLAIM_FRIENDLY
    )

    BASE_AIRLINE_VARS = [
        "airline_name", "flight_number", "origin", "destination",
        "departure_date", "pnr", "disruption_status"
    ]

    templates = [
        # ── AIRLINE REFUND ──────────────────────────────────────────────────
        {
            "recipient_type": "airline",
            "message_type": "refund",
            "tone": "formal",
            "disruption_types": ["cancellation", "delay", "overbooking"],
            "subject_template": "Refund Request - Flight {flight_number} Cancellation",
            "body_template": AIRLINE_REFUND_FORMAL,
            "required_variables": BASE_AIRLINE_VARS + ["regulation", "compensation_amount", "compensation_currency"],
            "optional_variables": [],
            "attachments_needed": ["Booking confirmation", "Flight cancellation notice", "Payment receipt"],
            "next_steps": [
                "Send to airline's customer service email",
                "Keep a copy of all correspondence",
                "Follow up in 48–72 hours if no response",
                "Track refund (typically 7–10 business days)"
            ],
            "version": 1
        },
        {
            "recipient_type": "airline",
            "message_type": "refund",
            "tone": "firm",
            "disruption_types": ["cancellation", "delay", "overbooking"],
            "subject_template": "URGENT: Mandatory Refund & Compensation - Flight {flight_number}",
            "body_template": AIRLINE_REFUND_FIRM,
            "required_variables": BASE_AIRLINE_VARS + ["regulation", "compensation_amount", "compensation_currency", "enforcement_body"],
            "optional_variables": [],
            "attachments_needed": ["Booking confirmation", "Flight cancellation notice", "Payment receipt"],
            "next_steps": [
                "Send via email AND recorded post for firm evidence trail",
                "Set a 7-day deadline for response",
                "If no response, file complaint with aviation authority immediately",
                "Consider ADR (Alternative Dispute Resolution) as next step"
            ],
            "version": 1
        },
        {
            "recipient_type": "airline",
            "message_type": "refund",
            "tone": "friendly",
            "disruption_types": ["cancellation", "delay", "overbooking"],
            "subject_template": "Refund Request for Flight {flight_number}",
            "body_template": AIRLINE_REFUND_FRIENDLY,
            "required_variables": BASE_AIRLINE_VARS + ["regulation", "compensation_amount", "compensation_currency"],
            "optional_variables": [],
            "attachments_needed": ["Booking confirmation", "Flight cancellation notice"],
            "next_steps": [
                "Send to airline's customer service email",
                "Follow up politely after 5 business days",
                "Escalate tone if no response after 2 weeks"
            ],
            "version": 1
        },

        # ── AIRLINE REBOOKING ───────────────────────────────────────────────
        {
            "recipient_type": "airline",
            "message_type": "rebooking",
            "tone": "formal",
            "disruption_types": ["cancellation", "delay", "missed_connection"],
            "subject_template": "Rebooking Request - Flight {flight_number}",
            "body_template": AIRLINE_REBOOKING_FORMAL,
            "required_variables": BASE_AIRLINE_VARS + ["alternative_flight", "alternative_departure", "regulation"],
            "optional_variables": [],
            "attachments_needed": ["Original booking confirmation", "Flight disruption notice"],
            "next_steps": [
                "Send to airline's customer service or rebooking desk",
                "Call airline directly for faster resolution",
                "Confirm rebooking in writing via email",
                "Request seat confirmation on the alternative flight"
            ],
            "version": 1
        },
        {
            "recipient_type": "airline",
            "message_type": "rebooking",
            "tone": "firm",
            "disruption_types": ["cancellation", "delay", "missed_connection"],
            "subject_template": "IMMEDIATE Rebooking Required - Flight {flight_number}",
            "body_template": (
                "To Whom It May Concern,\n\n"
                "I am writing to demand immediate rebooking following the {disruption_type} of flight "
                "{flight_number} from {origin} to {destination} on {departure_date}.\n\n"
                "Under {regulation}, I am entitled to re-routing to my final destination at no additional "
                "cost at the earliest opportunity. I require immediate placement on the next available "
                "flight to {destination}.\n\n"
                "My booking reference is {pnr}. Current status: {disruption_status}.\n\n"
                "I expect written confirmation of my rebooking within 2 hours of this message. "
                "Failure to rebook me promptly will result in a formal complaint to the relevant "
                "aviation authority.\n\n"
                "Regards,\n[Your Name]"
            ),
            "required_variables": BASE_AIRLINE_VARS + ["regulation"],
            "optional_variables": ["alternative_flight", "alternative_departure"],
            "attachments_needed": ["Original booking confirmation", "Flight disruption notice"],
            "next_steps": [
                "Send via email immediately and follow up by phone",
                "Set 2-hour deadline for response in the message",
                "If no response, go directly to airline desk at airport",
                "File aviation authority complaint if rebooking refused"
            ],
            "version": 1
        },
        {
            "recipient_type": "airline",
            "message_type": "rebooking",
            "tone": "friendly",
            "disruption_types": ["cancellation", "delay", "missed_connection"],
            "subject_template": "Rebooking Assistance Needed - Flight {flight_number}",
            "body_template": (
                "Hi {airline_name} Team,\n\n"
                "I hope you can help me out! My flight {flight_number} from {origin} to {destination} "
                "on {departure_date} has been disrupted ({disruption_status}), and I was hoping to "
                "get rebooked as soon as possible.\n\n"
                "My booking reference is {pnr}. Could you please put me on the next available flight "
                "to {destination}? I'm flexible on timing and would really appreciate any help you can "
                "provide.\n\n"
                "Thanks so much for your assistance!\n\n"
                "Best regards,\n[Your Name]"
            ),
            "required_variables": BASE_AIRLINE_VARS,
            "optional_variables": ["regulation"],
            "attachments_needed": ["Original booking confirmation"],
            "next_steps": [
                "Send to airline's customer service",
                "Also try the airline's app or website for self-service rebooking",
                "Call the airline's rebooking line for faster service"
            ],
            "version": 1
        },

        # ── AIRLINE ALTERNATIVE FLIGHT ──────────────────────────────────────
        {
            "recipient_type": "airline",
            "message_type": "alternative_flight",
            "tone": "formal",
            "disruption_types": ["cancellation", "delay"],
            "subject_template": "Alternative Flight Request - Flight {flight_number}",
            "body_template": AIRLINE_ALTERNATIVE_FORMAL,
            "required_variables": BASE_AIRLINE_VARS,
            "optional_variables": ["alternative_flight", "alternative_departure"],
            "attachments_needed": ["Original booking confirmation"],
            "next_steps": [
                "Send to airline's customer service",
                "Follow up by phone for faster response",
                "Confirm seat assignment on alternative flight"
            ],
            "version": 1
        },
        {
            "recipient_type": "airline",
            "message_type": "alternative_flight",
            "tone": "firm",
            "disruption_types": ["cancellation", "delay"],
            "subject_template": "URGENT: Alternative Flight Required - Flight {flight_number}",
            "body_template": AIRLINE_ALTERNATIVE_FIRM,
            "required_variables": BASE_AIRLINE_VARS + ["regulation"],
            "optional_variables": ["alternative_flight", "alternative_departure"],
            "attachments_needed": ["Original booking confirmation", "Disruption notice"],
            "next_steps": [
                "Send immediately and follow up by phone",
                "Request written confirmation within 1 hour",
                "Escalate to supervisor if initial agent cannot help"
            ],
            "version": 1
        },
        {
            "recipient_type": "airline",
            "message_type": "alternative_flight",
            "tone": "friendly",
            "disruption_types": ["cancellation", "delay"],
            "subject_template": "Help Finding Alternative Flight - {flight_number}",
            "body_template": AIRLINE_ALTERNATIVE_FRIENDLY,
            "required_variables": BASE_AIRLINE_VARS,
            "optional_variables": ["alternative_flight", "alternative_departure"],
            "attachments_needed": ["Original booking confirmation"],
            "next_steps": [
                "Send to airline customer service",
                "Check airline app for self-service options",
                "Be flexible on departure times for faster rebooking"
            ],
            "version": 1
        },

        # ── HOTEL CANCELLATION ──────────────────────────────────────────────
        {
            "recipient_type": "hotel",
            "message_type": "cancellation",
            "tone": "formal",
            "disruption_types": ["cancellation", "delay", "weather", "other"],
            "subject_template": "Cancellation Fee Waiver Request - Flight Disruption",
            "body_template": HOTEL_CANCELLATION_FORMAL,
            "required_variables": ["hotel_name", "booking_reference", "checkin_date", "checkout_date",
                                   "flight_number", "origin", "destination", "departure_date", "airline_name"],
            "optional_variables": [],
            "attachments_needed": ["Hotel booking confirmation", "Flight cancellation notice from airline"],
            "next_steps": [
                "Send to hotel reservations or front desk email",
                "Call hotel directly to confirm receipt",
                "Keep flight cancellation notice as proof",
                "Follow up if no response within 24 hours"
            ],
            "version": 1
        },
        {
            "recipient_type": "hotel",
            "message_type": "cancellation",
            "tone": "firm",
            "disruption_types": ["cancellation", "delay", "weather", "other"],
            "subject_template": "Urgent: Cancellation Fee Waiver Required - Flight Disruption",
            "body_template": (
                "Dear {hotel_name} Reservations Manager,\n\n"
                "I am writing to formally request a full waiver of cancellation fees for reservation "
                "{booking_reference} (check-in: {checkin_date}, check-out: {checkout_date}).\n\n"
                "My flight {flight_number} from {origin} to {destination} was cancelled by {airline_name}. "
                "This cancellation is entirely outside my control and I have documented proof from the airline.\n\n"
                "Under consumer protection principles and standard hospitality industry practice, cancellation "
                "fees should be waived when the guest's inability to honour the booking is due to a third-party "
                "service failure (in this case, airline cancellation).\n\n"
                "I require written confirmation of the fee waiver within 24 hours. I have attached the "
                "airline cancellation notice as proof.\n\n"
                "Should this not be resolved promptly, I will escalate to the relevant consumer protection "
                "authority and review platforms.\n\n"
                "Regards,\n[Your Name]"
            ),
            "required_variables": ["hotel_name", "booking_reference", "checkin_date", "checkout_date",
                                   "flight_number", "origin", "destination", "airline_name"],
            "optional_variables": [],
            "attachments_needed": ["Hotel booking confirmation", "Flight cancellation notice from airline"],
            "next_steps": [
                "Send via email with read receipt",
                "Set 24-hour response deadline",
                "Escalate to hotel manager if front desk cannot resolve",
                "File consumer complaint if hotel refuses without cause"
            ],
            "version": 1
        },
        {
            "recipient_type": "hotel",
            "message_type": "cancellation",
            "tone": "friendly",
            "disruption_types": ["cancellation", "delay", "weather", "other"],
            "subject_template": "Help Needed: Cancellation Due to Flight Issue",
            "body_template": HOTEL_CANCELLATION_FRIENDLY,
            "required_variables": ["hotel_name", "booking_reference", "checkin_date",
                                   "destination", "airline_name"],
            "optional_variables": [],
            "attachments_needed": ["Hotel booking confirmation", "Flight cancellation notice"],
            "next_steps": [
                "Call hotel directly — a friendly conversation often works best",
                "Send email as follow-up after phone call",
                "Ask if they can offer a future date credit instead"
            ],
            "version": 1
        },

        # ── INSURANCE CLAIM ─────────────────────────────────────────────────
        {
            "recipient_type": "insurance",
            "message_type": "claim",
            "tone": "formal",
            "disruption_types": ["cancellation", "delay", "weather", "other"],
            "subject_template": "Travel Insurance Claim - Flight {flight_number} Disruption",
            "body_template": INSURANCE_CLAIM_FORMAL,
            "required_variables": ["insurance_provider", "policy_number", "coverage_period",
                                   "flight_number", "airline_name", "origin", "destination",
                                   "departure_date", "disruption_status",
                                   "hotel_cost", "meal_cost", "rebooking_cost",
                                   "transport_cost", "total_claim", "currency"],
            "optional_variables": [],
            "attachments_needed": [
                "Travel insurance policy document",
                "Flight cancellation notice",
                "Original flight booking confirmation",
                "Alternative flight booking (if rebooked)",
                "Hotel receipts",
                "Meal receipts",
                "Transportation receipts"
            ],
            "next_steps": [
                "Submit claim online via insurance provider portal if available",
                "Send email with all documentation attached",
                "Note your claim reference number",
                "Keep copies of all correspondence",
                "Follow up after 1–2 weeks for claim status"
            ],
            "version": 1
        },
        {
            "recipient_type": "insurance",
            "message_type": "claim",
            "tone": "firm",
            "disruption_types": ["cancellation", "delay", "weather", "other"],
            "subject_template": "URGENT: Travel Insurance Claim - Flight {flight_number}",
            "body_template": (
                "Dear {insurance_provider} Claims Department,\n\n"
                "I am filing an urgent travel insurance claim under policy #{policy_number} for a "
                "documented flight disruption that has resulted in significant financial losses.\n\n"
                "**Incident:** Flight {flight_number} ({airline_name}) from {origin} to {destination} "
                "on {departure_date} — {disruption_status}.\n\n"
                "**Total Claim: {total_claim} {currency}**\n"
                "Breakdown: Hotel {hotel_cost}, Meals {meal_cost}, Rebooking {rebooking_cost}, "
                "Transport {transport_cost}\n\n"
                "I have attached all required documentation. Under my policy terms, I expect a "
                "claim decision within the timeframe specified in my policy.\n\n"
                "If I do not receive acknowledgement within 48 hours, I will escalate to the "
                "Financial Ombudsman Service or relevant regulatory body.\n\n"
                "Policy Number: {policy_number}\n"
                "[Your Name]\n[Your Contact Details]"
            ),
            "required_variables": ["insurance_provider", "policy_number", "flight_number",
                                   "airline_name", "origin", "destination", "departure_date",
                                   "disruption_status", "hotel_cost", "meal_cost",
                                   "rebooking_cost", "transport_cost", "total_claim", "currency"],
            "optional_variables": [],
            "attachments_needed": [
                "Travel insurance policy document",
                "Flight cancellation notice",
                "All receipts with amounts",
                "Original and rebooked flight confirmations"
            ],
            "next_steps": [
                "Submit online AND send email for double documentation",
                "Set 48-hour acknowledgement deadline",
                "Escalate to Financial Ombudsman if claim is denied without clear reason",
                "Keep all original receipts — do not send originals, send copies"
            ],
            "version": 1
        },
        {
            "recipient_type": "insurance",
            "message_type": "claim",
            "tone": "friendly",
            "disruption_types": ["cancellation", "delay", "weather", "other"],
            "subject_template": "Insurance Claim for Trip Disruption",
            "body_template": INSURANCE_CLAIM_FRIENDLY,
            "required_variables": ["insurance_provider", "policy_number", "flight_number",
                                   "origin", "destination", "departure_date",
                                   "hotel_cost", "meal_cost", "rebooking_cost",
                                   "total_claim", "currency"],
            "optional_variables": [],
            "attachments_needed": [
                "Insurance policy",
                "Receipts for all claimed expenses",
                "Flight cancellation notice"
            ],
            "next_steps": [
                "Submit via online portal if available — faster processing",
                "Send email as backup",
                "Follow up after 1 week if no acknowledgement",
                "Have receipts ready in case they request originals"
            ],
            "version": 1
        },
    ]

    return templates


# =============================================================================
# INGESTION FUNCTIONS
# =============================================================================

async def ingest_rights():
    """Ingest all passenger rights documents into MongoDB"""
    rights_data = build_rights_data()

    logger.info(f"\n{'='*60}")
    logger.info(f"INGESTING PASSENGER RIGHTS ({len(rights_data)} documents)")
    logger.info(f"{'='*60}\n")

    success = 0
    failed = 0

    for doc in rights_data:
        try:
            await save_rights(doc["region"], doc["disruption_type"], {
                # Pass the full doc — save_rights will handle mapping
                **doc,
                # Ensure ExplainRightsResponse-compatible fields are present
                "summary": doc["summary"],
                "rights_bullets": doc["rights_bullets"],
                "compensation_amount": doc.get("default_compensation_amount"),
                "compensation_currency": doc.get("default_compensation_currency", "USD"),
                "next_steps": doc["next_steps"],
                "source_links": doc.get("source_links", []),
                "applicable_regulation": doc["applicable_regulation"],
            })
            logger.info(f"  ✅ {doc['region']:8} | {doc['disruption_type']}")
            success += 1
        except Exception as e:
            logger.error(f"  ❌ {doc['region']:8} | {doc['disruption_type']} — {e}")
            failed += 1

    logger.info(f"\n{'='*60}")
    logger.info(f"RIGHTS INGESTION COMPLETE: {success} success, {failed} failed")
    logger.info(f"{'='*60}\n")


async def ingest_templates():
    """Ingest all draft message templates into MongoDB"""
    templates_data = build_templates_data()

    logger.info(f"\n{'='*60}")
    logger.info(f"INGESTING DRAFT TEMPLATES ({len(templates_data)} documents)")
    logger.info(f"{'='*60}\n")

    success = 0
    failed = 0

    for tmpl in templates_data:
        try:
            await save_draft_template(tmpl)
            logger.info(f"  ✅ {tmpl['recipient_type']:12} | {tmpl['message_type']:20} | {tmpl['tone']}")
            success += 1
        except Exception as e:
            logger.error(f"  ❌ {tmpl['recipient_type']:12} | {tmpl['message_type']:20} | {tmpl['tone']} — {e}")
            failed += 1

    logger.info(f"\n{'='*60}")
    logger.info(f"TEMPLATE INGESTION COMPLETE: {success} success, {failed} failed")
    logger.info(f"{'='*60}\n")


async def main(run_rights: bool = True, run_templates: bool = True):
    """Main ingestion entry point"""
    logger.info(f"\n{'='*60}")
    logger.info("DISRUPTION KNOWLEDGE BASE INGESTION")
    logger.info(f"Started at: {datetime.now(timezone.utc).isoformat()}")
    logger.info(f"{'='*60}\n")

    await connect_to_mongo()

    try:
        # Step 1: Ensure indexes exist
        logger.info("Setting up MongoDB indexes...")
        await ensure_indexes()
        logger.info("✅ Indexes ready\n")

        # Step 2: Ingest rights
        if run_rights:
            await ingest_rights()

        # Step 3: Ingest templates
        if run_templates:
            await ingest_templates()

    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await close_mongo_connection()

    logger.info(f"\n✅ All done! Run 'python scripts/ingest_disruption_knowledge.py --all' to re-run anytime.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest disruption knowledge into MongoDB")
    parser.add_argument("--rights", action="store_true", help="Ingest passenger rights only")
    parser.add_argument("--templates", action="store_true", help="Ingest draft templates only")
    parser.add_argument("--all", action="store_true", help="Ingest both rights and templates")

    args = parser.parse_args()

    # Default to --all if nothing specified
    run_rights = args.rights or args.all or (not args.rights and not args.templates)
    run_templates = args.templates or args.all or (not args.rights and not args.templates)

    asyncio.run(main(run_rights=run_rights, run_templates=run_templates))
