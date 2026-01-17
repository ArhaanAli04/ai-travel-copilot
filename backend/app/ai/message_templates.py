"""
Email Templates for Disruption Resolution
Structured templates for different recipient types and tones
"""

# ===== AIRLINE TEMPLATES =====

AIRLINE_REFUND_FORMAL = """Dear {airline_name} Customer Service,

I am writing to request a full refund and compensation for my cancelled flight under {regulation}.

**Flight Details:**
- Flight Number: {flight_number}
- Route: {origin} → {destination}
- Scheduled Departure: {departure_date}
- Booking Reference: {pnr}

**Reason for Request:**
My flight was {disruption_status}. Under {regulation}, I am entitled to:
1. Full refund of the ticket price
2. Compensation of {compensation_amount} {compensation_currency}

**Requested Action:**
Please process:
- Full ticket refund to my original payment method
- Compensation payment of {compensation_amount} {compensation_currency}

I have attached proof of the flight cancellation and booking confirmation. I expect the refund to be processed within 7 business days as required by law.

Thank you for your prompt attention to this matter.

Sincerely,
[Your Name]
"""

AIRLINE_REFUND_FIRM = """Subject: URGENT: Flight Cancellation Refund & Compensation Required

To Whom It May Concern,

This is a formal demand for immediate refund and compensation for flight {flight_number} on {departure_date}.

**Legal Entitlement:**
Under {regulation}, you are LEGALLY REQUIRED to provide:
1. FULL ticket refund within 7 days
2. Compensation of {compensation_amount} {compensation_currency}

**Flight Information:**
- Flight: {flight_number} ({airline_name})
- Route: {origin} to {destination}
- Booking Reference: {pnr}
- Disruption: {disruption_status}

**Action Required:**
I expect full compliance with passenger rights regulations. Failure to process this refund within 7 business days will result in:
- Complaint filed with {enforcement_body}
- Claim filed through alternative dispute resolution
- Potential legal action for statutory damages

Process my refund immediately.

[Your Name]
Passenger Rights Reference: {regulation}
"""

AIRLINE_REFUND_FRIENDLY = """Hi {airline_name} Team,

I hope this message finds you well. I'm reaching out regarding my recent flight disruption and would appreciate your help.

**My Flight:**
- Flight Number: {flight_number}
- Route: {origin} → {destination}
- Date: {departure_date}
- Booking Reference: {pnr}

**What Happened:**
Unfortunately, my flight was {disruption_status}. I understand these situations happen, but this has significantly impacted my travel plans.

**What I'm Requesting:**
Based on {regulation}, I believe I'm entitled to:
- A full refund of my ticket
- Compensation of {compensation_amount} {compensation_currency}

I'd really appreciate it if you could help me process this. I've had great experiences with {airline_name} in the past and I'm confident we can resolve this smoothly.

Please let me know what documentation you need from me.

Thank you so much for your help!

Best regards,
[Your Name]
"""

AIRLINE_REBOOKING_FORMAL = """Dear {airline_name} Customer Service,

I am writing to request rebooking on an alternative flight following the {disruption_type} of flight {flight_number}.

**Original Flight:**
- Flight Number: {flight_number}
- Route: {origin} → {destination}
- Scheduled: {departure_date}
- Booking Reference: {pnr}

**Requested Alternative:**
- Flight Number: {alternative_flight}
- Departure: {alternative_departure}

As per {regulation}, I am entitled to rebooking at no additional cost. Please confirm my rebooking on the alternative flight mentioned above.

If this flight is not available, please provide the next available option to {destination}.

Thank you for your assistance.

Sincerely,
[Your Name]
"""

# ===== HOTEL TEMPLATES =====

HOTEL_CANCELLATION_FORMAL = """Dear {hotel_name} Reservations,

I am writing to request a waiver of cancellation fees for my upcoming reservation due to flight cancellation.

**Reservation Details:**
- Confirmation Number: {booking_reference}
- Guest Name: [Your Name]
- Check-in Date: {checkin_date}
- Check-out Date: {checkout_date}

**Reason for Cancellation:**
My flight ({flight_number}) from {origin} to {destination} scheduled for {departure_date} was cancelled by the airline. Due to this unforeseen circumstance beyond my control, I am unable to honor my hotel reservation.

**Request:**
I respectfully request that you waive the cancellation fee and provide a full refund, as this cancellation is due to airline disruption, not personal choice.

I have attached:
- Flight cancellation notice from {airline_name}
- Original hotel booking confirmation

I appreciate your understanding and look forward to staying at {hotel_name} on a future visit.

Thank you for your consideration.

Sincerely,
[Your Name]
"""

HOTEL_CANCELLATION_FRIENDLY = """Hi {hotel_name} Team,

I hope you're doing well! I'm reaching out about a reservation I need to cancel due to an unexpected flight cancellation.

**My Reservation:**
- Confirmation: {booking_reference}
- Check-in: {checkin_date}

**What Happened:**
My flight to {destination} was cancelled by {airline_name}, so unfortunately I can't make it to my stay. I know your cancellation policy, but I'm hoping you might be able to help given the circumstances.

I have the flight cancellation notice from the airline if you need it. I'd really appreciate any flexibility you can offer - I was really looking forward to staying with you!

Hopefully I can rebook for another time soon.

Thanks so much for understanding!

Best,
[Your Name]
"""

# ===== INSURANCE TEMPLATES =====

INSURANCE_CLAIM_FORMAL = """Dear {insurance_provider} Claims Department,

I am filing a travel insurance claim under policy #{policy_number} for trip disruption due to flight cancellation.

**Policy Information:**
- Policy Number: {policy_number}
- Policyholder: [Your Name]
- Coverage Period: {coverage_period}

**Incident Details:**
- Flight: {flight_number} ({airline_name})
- Route: {origin} → {destination}
- Scheduled Departure: {departure_date}
- Disruption: {disruption_status}

**Claimed Expenses:**
1. Hotel rebooking: {hotel_cost} {currency}
2. Meal expenses: {meal_cost} {currency}
3. Alternative flight: {rebooking_cost} {currency}
4. Ground transportation: {transport_cost} {currency}

**Total Claim Amount: {total_claim} {currency}**

**Attached Documentation:**
- Flight cancellation notice from airline
- Original and rebooked flight confirmations
- Hotel receipts
- Meal receipts
- Ground transportation receipts
- Copy of travel insurance policy

As per the policy terms, I believe this claim falls under "Trip Interruption" coverage. I request prompt processing of this claim.

Please confirm receipt and provide a claim reference number.

Sincerely,
[Your Name]
Policy Number: {policy_number}
Contact: [Your Phone/Email]
"""

INSURANCE_CLAIM_FRIENDLY = """Hi {insurance_provider} Team,

I need to file a claim for my recent trip that was disrupted by a flight cancellation. Here are the details:

**My Policy:**
- Number: {policy_number}
- Name: [Your Name]

**What Happened:**
My flight {flight_number} from {origin} to {destination} was cancelled on {departure_date}. This caused me to incur unexpected expenses for rebooking and accommodation.

**Expenses I'm Claiming:**
- Hotel: {hotel_cost} {currency}
- Meals: {meal_cost} {currency}
- Rebooking: {rebooking_cost} {currency}
- Total: {total_claim} {currency}

I've attached all my receipts and the cancellation notice from the airline. Let me know if you need anything else!

Thanks for your help with this.

Best regards,
[Your Name]
"""

# ===== TEMPLATE MAPPING =====

TEMPLATES = {
    ("airline", "refund", "formal"): AIRLINE_REFUND_FORMAL,
    ("airline", "refund", "firm"): AIRLINE_REFUND_FIRM,
    ("airline", "refund", "friendly"): AIRLINE_REFUND_FRIENDLY,
    ("airline", "rebooking", "formal"): AIRLINE_REBOOKING_FORMAL,
    ("airline", "rebooking", "friendly"): AIRLINE_REBOOKING_FORMAL,  # Reuse formal
    ("airline", "rebooking", "firm"): AIRLINE_REBOOKING_FORMAL,
    
    ("hotel", "cancellation", "formal"): HOTEL_CANCELLATION_FORMAL,
    ("hotel", "cancellation", "friendly"): HOTEL_CANCELLATION_FRIENDLY,
    ("hotel", "cancellation", "firm"): HOTEL_CANCELLATION_FORMAL,  # Reuse formal
    
    ("insurance", "claim", "formal"): INSURANCE_CLAIM_FORMAL,
    ("insurance", "claim", "friendly"): INSURANCE_CLAIM_FRIENDLY,
    ("insurance", "claim", "firm"): INSURANCE_CLAIM_FORMAL,  # Reuse formal
}


def get_template(recipient_type: str, message_type: str, tone: str) -> str:
    """
    Get email template based on recipient, message type, and tone
    
    Args:
        recipient_type: "airline", "hotel", "insurance"
        message_type: "refund", "rebooking", "cancellation", "claim"
        tone: "formal", "firm", "friendly"
        
    Returns:
        Template string
    """
    key = (recipient_type.lower(), message_type.lower(), tone.lower())
    return TEMPLATES.get(key, AIRLINE_REFUND_FORMAL)  # Default fallback
