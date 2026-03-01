"""
Disruption Agent - AI agent for explaining passenger rights and suggesting options

Uses:
- RightsRetriever to fetch policies
- Gemini AI to synthesize explanations
- LangChain for structured outputs
"""
from typing import Dict, List, Optional
from datetime import datetime,timezone,timedelta
import logging
from google import genai
from google.genai import types
import json
from app.core.config import settings
from app.ai.retrievers import create_rights_retriever
from app.models.disruption import DisruptionCase, DisruptionType,DisruptionOption
from langchain_core.documents import Document
from sqlalchemy.orm import Session
from app.services import disruption_mongo_service
from app.utils.region_mapper import get_region_from_country

logger = logging.getLogger(__name__)


class DisruptionAgent:
    """
    AI Agent for travel disruption assistance
    
    Capabilities:
    - Explain passenger rights based on region and airline
    - Calculate compensation amounts
    - Suggest actionable next steps
    - Provide source citations
    """
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-2.5-flash-lite"  # or "gemini-2.5-flash-lite"
        self.config = types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=2048,
        )

    async def explain_rights(
        self,
        disruption_case: DisruptionCase,
        airline_code: Optional[str] = None,
        booking_class: Optional[str] = None,
        insurance_provider: Optional[str] = None
    ) -> Dict:
        """
        Explain passenger rights for a disruption case

        3-Layer lookup:
        Layer 1: MongoDB exact match (region + disruption_type) → instant, no Gemini
        Layer 2: Qdrant RAG retriever (existing policy docs)
        Layer 3: Gemini synthesis → result saved back to MongoDB for future use

        Args:
            disruption_case: The disruption case
            airline_code: Optional airline IATA code
            booking_class: Optional booking class (economy, business, etc.)
            insurance_provider: Optional insurance provider name

        Returns:
            Dict with:
            - summary: Plain-language explanation
            - rights_bullets: Actionable bullet points
            - compensation_amount: Estimated compensation
            - source_links: Citations
            - cached: Whether data was served from MongoDB cache
        """
        logger.info(f"🤖 Explaining rights for case {disruption_case.id}")

        try:
            # 1. Extract route information
            origin_country = self._extract_country_from_airport_or_city(disruption_case.origin)
            destination_country = self._extract_country_from_airport_or_city(disruption_case.destination)

            logger.info(f"📍 Route: {disruption_case.origin} ({origin_country}) → {disruption_case.destination} ({destination_country})")

            # ✅ PHASE 5 — Layer 1: Map country code → regulation region
            region = get_region_from_country(origin_country)
            disruption_type_str = disruption_case.disruption_type.value

            logger.info(f"🗺️ Region mapped: {origin_country} → {region}")

            # ✅ PHASE 5 — Layer 1: MongoDB exact-match lookup
            cached_rights = await disruption_mongo_service.get_rights(region, disruption_type_str)

            if cached_rights:
                logger.info(
                    f"⚡ MongoDB cache HIT — returning instantly "
                    f"(region={region}, type={disruption_type_str}), no Gemini call"
                )
                # cached_rights already matches ExplainRightsResponse shape exactly
                return cached_rights

            logger.info(
                f"💨 MongoDB cache MISS — falling through to Qdrant + Gemini "
                f"(region={region}, type={disruption_type_str})"
            )

            # ✅ PHASE 5 — Layer 2: Qdrant retriever (existing logic, unchanged)
            retriever = create_rights_retriever(
                airline=disruption_case.airline,
                origin_country=origin_country,
                destination_country=destination_country,
                disruption_type=disruption_type_str,
                provider_type="airline",
                k=5,
                use_cache=True
            )

            # Query for rights
            query = self._build_rights_query(disruption_case)
            policy_docs = await retriever._aget_relevant_documents(query)

            cached = len(policy_docs) > 0

            # 3. Get flight metadata for context
            flight_status = disruption_case.meta_data.get("flight_status", {}) if disruption_case.meta_data else {}
            delay_minutes = self._extract_delay_minutes(flight_status, disruption_case)

            # ✅ PHASE 5 — Layer 3: Gemini synthesis (existing logic, unchanged)
            explanation = await self._synthesize_explanation(
                disruption_case=disruption_case,
                policy_docs=policy_docs,
                origin_country=origin_country,
                destination_country=destination_country,
                delay_minutes=delay_minutes,
                booking_class=booking_class
            )

            # 5. Extract source links
            source_links = self._extract_sources(policy_docs)

            result = {
                "summary": explanation.get("summary", ""),
                "rights_bullets": explanation.get("rights_bullets", []),
                "compensation_amount": explanation.get("compensation_amount"),
                "compensation_currency": explanation.get("compensation_currency", "USD"),
                "next_steps": explanation.get("next_steps", []),
                "source_links": source_links,
                "cached": cached,
                "region": region,  # ✅ PHASE 5 — use mapped region, not raw country code
                "applicable_regulation": explanation.get("applicable_regulation", ""),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }

            # ✅ PHASE 5 — Save Gemini result to MongoDB so next request hits cache
            # Fire-and-forget: don't await failure, never block the user response
            try:
                await disruption_mongo_service.save_rights(region, disruption_type_str, result)
                logger.info(
                    f"💾 Saved Gemini result to MongoDB cache "
                    f"(region={region}, type={disruption_type_str})"
                )
            except Exception as save_err:
                logger.warning(f"⚠️ Failed to cache rights to MongoDB (non-critical): {save_err}")

            logger.info(f"✅ Generated rights explanation for case {disruption_case.id}")
            return result

        except Exception as e:
            logger.error(f"❌ Failed to explain rights: {e}")
            return {
                "summary": "Unable to determine your rights at this time. Please contact your airline directly.",
                "rights_bullets": [],
                "compensation_amount": None,
                "source_links": [],
                "cached": False,
                "error": str(e)
            }
    
    async def _synthesize_explanation(
        self,
        disruption_case: DisruptionCase,
        policy_docs: List[Document],
        origin_country: str,
        destination_country: str,
        delay_minutes: Optional[int],
        booking_class: Optional[str]
    ) -> Dict:
        """
        Use Gemini to synthesize policy documents into user-friendly explanation
        """
        try:
            # Build context from policy documents
            policy_context = "\n\n".join([
                f"Source: {doc.metadata.get('source_title', 'Unknown')}\n{doc.page_content}"
                for doc in policy_docs[:3]  # Use top 3 most relevant
            ])
            
            # Build prompt
            prompt = self._build_synthesis_prompt(
                disruption_case=disruption_case,
                policy_context=policy_context,
                origin_country=origin_country,
                destination_country=destination_country,
                delay_minutes=delay_minutes,
                booking_class=booking_class
            )
            
            # Generate response
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.config
            )
            
            # Parse response
            parsed = self._parse_gemini_response(response.text)
            
            return parsed
            
        except Exception as e:
            logger.error(f"❌ Synthesis failed: {e}")
            return {
                "summary": "Unable to generate explanation.",
                "rights_bullets": [],
                "compensation_amount": None
            }
    
    def _build_synthesis_prompt(
        self,
        disruption_case: DisruptionCase,
        policy_context: str,
        origin_country: str,
        destination_country: str,
        delay_minutes: Optional[int],
        booking_class: Optional[str]
    ) -> str:
        """
        Build prompt for Gemini to synthesize rights explanation
        """
        prompt = f"""You are a travel rights expert helping passengers understand their compensation and refund rights.

**Flight Details:**
- Flight: {disruption_case.flight_number} ({disruption_case.airline})
- Route: {disruption_case.origin} ({origin_country}) → {disruption_case.destination} ({destination_country})
- Disruption Type: {disruption_case.disruption_type.value}
- Status: {disruption_case.current_status}
- Delay: {delay_minutes} minutes (if applicable)
- Booking Class: {booking_class or 'Unknown'}
- Date: {disruption_case.disruption_date}

**Relevant Policies:**
{policy_context if policy_context else "No specific policies found. Use general aviation regulations."}

**Your Task:**
Analyze this disruption and explain the passenger's rights in clear, actionable language.

**Determine:**
1. What regulation applies (EU261, DOT, etc.)?
2. Is the passenger entitled to compensation? How much?
3. What are the passenger's rights (refund, rebooking, care)?
4. What should the passenger do next?

**Response Format (use exactly this structure):**

REGULATION: [Name of applicable regulation, e.g., "EU Regulation 261/2004"]

SUMMARY:
[2-3 sentence plain-language explanation of the passenger's rights and an overview of the passenger's situation]

COMPENSATION:
Amount: [Amount in local currency, or "Not applicable"]
Currency: [EUR, USD, GBP, etc.]
Reason: [Why this amount, or why not applicable]

RIGHTS:
- [Bullet point 1]
- [Bullet point 2]
- [Bullet point 3]

NEXT_STEPS:
- [Action 1]
- [Action 2]
- [Action 3]

**Important Rules:**
- Be specific about amounts (e.g., "€600 under EU261")
- Only promise compensation if clearly entitled
- If unclear, say "may be entitled" or "contact airline"
- Use plain language, not legal jargon
- Be helpful and empathetic
"""
        
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> Dict:
        """
        Parse Gemini's structured response into a dictionary
        """
        try:
            lines = response_text.strip().split("\n")
            
            result = {
                "summary": "",
                "rights_bullets": [],
                "compensation_amount": None,
                "compensation_currency": "USD",
                "next_steps": [],
                "applicable_regulation": ""
            }
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    continue
                
                # Detect sections
                if line.startswith("REGULATION:"):
                    result["applicable_regulation"] = line.replace("REGULATION:", "").strip()
                elif line.startswith("SUMMARY:"):
                    current_section = "summary"
                elif line.startswith("COMPENSATION:"):
                    current_section = "compensation"
                elif line.startswith("RIGHTS:"):
                    current_section = "rights"
                elif line.startswith("NEXT_STEPS:"):
                    current_section = "next_steps"
                
                # Parse content
                elif current_section == "summary":
                    result["summary"] += line + " "
                
                elif current_section == "compensation":
                    if line.startswith("Amount:"):
                        amount_str = line.replace("Amount:", "").strip()
                        # Extract numeric value
                        import re
                        numbers = re.findall(r'\d+', amount_str)
                        if numbers:
                            result["compensation_amount"] = int(numbers[0])
                    elif line.startswith("Currency:"):
                        result["compensation_currency"] = line.replace("Currency:", "").strip()
                
                elif current_section == "rights":
                    if line.startswith("-"):
                        result["rights_bullets"].append(line[1:].strip())
                
                elif current_section == "next_steps":
                    if line.startswith("-"):
                        result["next_steps"].append(line[1:].strip())
            
            # Clean up summary
            result["summary"] = result["summary"].strip()
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to parse response: {e}")
            return {
                "summary": response_text[:500],  # Use first 500 chars as fallback
                "rights_bullets": [],
                "compensation_amount": None
            }
    
    def _build_rights_query(self, disruption_case: DisruptionCase) -> str:
        """
        Build semantic search query for rights retrieval
        """
        disruption_type = disruption_case.disruption_type.value
        
        if disruption_type == DisruptionType.CANCELLATION.value:
            return f"flight cancellation compensation rights refund {disruption_case.airline}"
        elif disruption_type == DisruptionType.DELAY.value:
            return f"flight delay compensation rights {disruption_case.airline}"
        else:
            return f"passenger rights {disruption_type} {disruption_case.airline}"

    def _extract_country_from_airport_or_city(self, location: str) -> str:
        """
        Extract country code from airport code (e.g., "JFK") or city name
        
        Priority:
        1. Check if location is IATA code (3 letters) → lookup in airport DB
        2. Search by city name in airport DB (returns most common country)
        3. Fallback to manual mapping
        """
        try:
            from app.services.disruption_service import disruption_service
            from collections import Counter
            
            airports_db = disruption_service.airports_db
            
            if not airports_db:
                logger.warning("⚠️ Airport database is empty")
                return self._fallback_country_lookup(location)
            
            location_clean = location.strip().upper()
            
            # PRIORITY 1: Check if it's an IATA code (e.g., "JFK", "LHR")
            if len(location_clean) == 3 and location_clean.isalpha():
                if location_clean in airports_db:
                    country = airports_db[location_clean].get("country", "UNKNOWN")
                    logger.debug(f"✅ Found airport code {location_clean} → {country}")
                    return country
            
            # PRIORITY 2: Search by city name
            # Problem: Multiple cities with same name (e.g., London, Paris in different countries)
            # Solution: Find ALL matches, return most common country
            location_lower = location.lower().strip()
            matching_countries = []
            
            for iata_code, airport_data in airports_db.items():
                airport_city = airport_data.get("city", "").lower()
                
                if airport_city == location_lower:
                    country = airport_data.get("country", "UNKNOWN")
                    matching_countries.append(country)
                    logger.debug(f"   Found {iata_code} in {airport_city} → {country}")
            
            # ✅ If we found matches, return the MOST COMMON country
            if matching_countries:
                # Count occurrences of each country
                country_counts = Counter(matching_countries)
                
                # Get most common country
                most_common_country = country_counts.most_common(1)[0][0]
                
                logger.debug(f"✅ City '{location}' found in countries: {dict(country_counts)}")
                logger.debug(f"✅ Selected most common: {most_common_country}")
                
                return most_common_country
            
            # PRIORITY 3: Fallback manual mapping
            return self._fallback_country_lookup(location)
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to extract country from '{location}': {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return self._fallback_country_lookup(location)

    def _fallback_country_lookup(self, location: str) -> str:
        """
        Fallback manual mapping for common locations
        
        Used when airport database lookup fails or for well-known city names
        """
        location_lower = location.lower().strip()
        
        # Airport codes fallback
        airport_to_country = {
            "jfk": "US", "lga": "US", "ewr": "US",
            "lhr": "GB", "lhw": "GB", "lgw": "GB", "stn": "GB",
            "cdg": "FR", "ory": "FR",
            "bom": "IN", "del": "IN", "blr": "IN",
            "dxb": "AE", "nrt": "JP", "hnd": "JP",
            "sin": "SG", "syd": "AU", "yyz": "CA",
            "hkg": "HK", "icn": "KR", "pek": "CN"
        }
        
        if location_lower in airport_to_country:
            return airport_to_country[location_lower]
        
        # City names fallback (for major cities)
        city_to_country = {
            # US cities
            "new york": "US", "nyc": "US",
            "los angeles": "US", "la": "US",
            "san francisco": "US", "sf": "US",
            "chicago": "US", "miami": "US",
            "seattle": "US", "boston": "US",
            
            # European cities
            "london": "GB",  # Default to UK, not Canada
            "paris": "FR",
            "berlin": "DE", "munich": "DE", "frankfurt": "DE",
            "rome": "IT", "milan": "IT",
            "madrid": "ES", "barcelona": "ES",
            "amsterdam": "NL", "brussels": "BE",
            
            # Asian cities
            "mumbai": "IN", "delhi": "IN", "bangalore": "IN",
            "dubai": "AE", "abu dhabi": "AE",
            "tokyo": "JP", "osaka": "JP",
            "singapore": "SG",
            "hong kong": "HK",
            "beijing": "CN", "shanghai": "CN",
            
            # Other major cities
            "sydney": "AU", "melbourne": "AU",
            "toronto": "CA", "vancouver": "CA"
        }
        
        return city_to_country.get(location_lower, "UNKNOWN")

    def _extract_country_from_city(self, city: str) -> str:
        """
        Extract country code from city name using airport database
        
        Leverages the airports.json database loaded by DisruptionService
        
        DEPRECATED: Use _extract_country_from_airport_or_city instead
        """
        # ✅ Just delegate to the enhanced method
        return self._extract_country_from_airport_or_city(city)

    def _extract_delay_minutes(
        self,
        flight_status: Dict,
        disruption_case: DisruptionCase
    ) -> Optional[int]:
        """
        Extract delay in minutes from flight status or calculate from timestamps
        """
        try:
            # Try to get delay from API response
            if "departure" in flight_status and "delay" in flight_status["departure"]:
                delay = flight_status["departure"]["delay"]
                if delay:
                    return int(delay)
            
            if "arrival" in flight_status and "delay" in flight_status["arrival"]:
                delay = flight_status["arrival"]["delay"]
                if delay:
                    return int(delay)
            
            # Calculate from scheduled vs actual times
            departure = flight_status.get("departure", {})
            scheduled = departure.get("scheduled")
            actual = departure.get("actual")
            
            if scheduled and actual:
                from datetime import datetime
                sched_time = datetime.fromisoformat(scheduled.replace("Z", "+00:00"))
                actual_time = datetime.fromisoformat(actual.replace("Z", "+00:00"))
                
                delay_seconds = (actual_time - sched_time).total_seconds()
                return max(0, int(delay_seconds / 60))
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Could not extract delay: {e}")
            return None
    
    def _extract_sources(self, policy_docs: List[Document]) -> List[Dict]:
        """
        Extract source citations from policy documents
        """
        sources = []
        seen_urls = set()
        
        for doc in policy_docs:
            url = doc.metadata.get("source_url")
            
            if url and url not in seen_urls:
                sources.append({
                    "title": doc.metadata.get("source_title", "Policy Document"),
                    "url": url,
                    "type": doc.metadata.get("type", "airline"),
                    "region": doc.metadata.get("region", "")
                })
                seen_urls.add(url)
        
        return sources

    async def suggest_options(
        self,
        disruption_case: DisruptionCase,
        db: Session,
        max_options: int = 5
    ) -> List[DisruptionOption]:
        """
        Generate AI-powered alternative options for a disruption case
        
        Args:
            disruption_case: The disruption case
            db: Database session
            max_options: Maximum number of options to generate
            
        Returns:
            List of DisruptionOption objects (saved to database)
        """
        logger.info(f"🤖 Generating options for case {disruption_case.id}")
        
        try:
            from app.services.disruption_service import disruption_service
            from app.models.disruption import DisruptionOption, OptionType
            
            options = []
            
            # 1. Get passenger rights (reuse Day 13 logic)
            rights_explanation = await self.explain_rights(disruption_case)
            
            # 2. Extract flight details
            flight_status = disruption_case.meta_data.get("flight_status", {}) if disruption_case.meta_data else {}
            origin_iata = flight_status.get("departure", {}).get("iata") or self._extract_airport_code(disruption_case.origin)
            destination_iata = flight_status.get("arrival", {}).get("iata") or self._extract_airport_code(disruption_case.destination)
            
            # 3. Generate ALTERNATIVE FLIGHT options
            if disruption_case.disruption_type in [DisruptionType.CANCELLATION, DisruptionType.DELAY]:
                flight_options = await self._generate_alternative_flight_options(
                    disruption_case=disruption_case,
                    origin_iata=origin_iata,
                    destination_iata=destination_iata,
                    db=db
                )
                options.extend(flight_options)
            
            # 4. Generate REFUND option
            refund_option = await self._generate_refund_option(
                disruption_case=disruption_case,
                rights_explanation=rights_explanation,
                db=db
            )
            if refund_option:
                options.append(refund_option)
            
            # 5. Generate HOTEL CANCELLATION option
            hotel_option = await self._generate_hotel_cancellation_option(
                disruption_case=disruption_case,
                db=db
            )
            if hotel_option:
                options.append(hotel_option)
            
            # 6. Generate INSURANCE CLAIM option (if applicable)
            insurance_option = await self._generate_insurance_claim_option(
                disruption_case=disruption_case,
                rights_explanation=rights_explanation,
                db=db
            )
            if insurance_option:
                options.append(insurance_option)
            
            # 7. Rank options using AI
            ranked_options = await self._rank_options_with_ai(
                options=options,
                disruption_case=disruption_case,
                rights_explanation=rights_explanation
            )
            
            # 8. Limit to max_options
            final_options = ranked_options[:max_options]
            
            logger.info(f"✅ Generated {len(final_options)} options for case {disruption_case.id}")
            
            return final_options
            
        except Exception as e:
            logger.error(f"❌ Failed to generate options: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
        
    async def generate_message(
        self,
        disruption_case: DisruptionCase,
        disruption_option: Optional[DisruptionOption],
        recipient_type: str,  # "airline", "hotel", "insurance"
        tone: str = "formal",  # "formal", "firm", "friendly"
        recipient_name: Optional[str] = None,
        db: Session = None
    ) -> Dict:
        """
        Generate professional email/message for disruption resolution
        
        
        Template lookup order:
        1. MongoDB draft_message_templates (exact match by recipient/type/tone)
        2. Python dict in message_templates.py (fallback)
        3. Gemini AI generation (fallback if template variable filling fails)
        Args:
            disruption_case: The disruption case
            disruption_option: Optional specific option this message relates to
            recipient_type: Who to send to ("airline", "hotel", "insurance")
            tone: Message tone ("formal", "firm", "friendly")
            recipient_name: Optional recipient name override
            db: Database session (to save draft message)
            
        Returns:
            Dict with subject, body, recipient_email, attachments_needed, next_steps
        """
        logger.info(f"✉️ Generating {tone} message to {recipient_type} for case {disruption_case.id}")
        
        try:
            from app.ai.message_templates import get_template
            from app.models.draft_message import DraftMessage, MessageRecipientType, MessageTone
            import json
            
            #  Deduplication check
            if db:
                
                # Check for duplicate drafts created in last 5 minutes
                five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
                
                try:
                    existing_draft = db.query(DraftMessage).filter(
                        DraftMessage.disruption_case_id == disruption_case.id,
                        DraftMessage.recipient_type == MessageRecipientType(recipient_type.lower()),
                        DraftMessage.tone == MessageTone(tone.lower()),
                        DraftMessage.created_at >= five_minutes_ago
                    ).first()
                    
                    if existing_draft:
                        age_seconds = int((datetime.now(timezone.utc) - existing_draft.created_at).total_seconds())
                        logger.info(f"♻️ Reusing recent {tone} draft {existing_draft.id} (created {age_seconds}s ago)")
                        
                        # Return existing draft
                        return {
                            "id": existing_draft.id,
                            "subject": existing_draft.subject,
                            "body": existing_draft.body,
                            "recipient_type": existing_draft.recipient_type.value,
                            "recipient_name": existing_draft.recipient_name,
                            "recipient_email": existing_draft.recipient_email,
                            "tone": existing_draft.tone.value,
                            "attachments_needed": json.loads(existing_draft.attachments_needed) if existing_draft.attachments_needed else [],
                            "next_steps": [],
                            "generated_at": existing_draft.created_at.isoformat()
                        }
                except Exception as dedupe_error:
                    logger.warning(f"⚠️ Deduplication check failed: {dedupe_error}")
                    # Continue with generation if check fails
            # END OF DEDUPLICATION BLOCK

            # 1. Determine message type based on option or disruption
            message_type = self._determine_message_type(disruption_option, disruption_case)
            
             # ✅ PHASE 6 — Step 2: MongoDB template lookup first, Python dict as fallback
            mongo_template = await disruption_mongo_service.get_draft_template(
                recipient_type, message_type, tone
            )

            if mongo_template:
                logger.info(
                    f"⚡ MongoDB template HIT: "
                    f"{recipient_type}/{message_type}/{tone} — no Gemini needed"
                )
                template = mongo_template["body_template"]
                mongo_subject = mongo_template.get("subject_template")
            else:
                logger.info(
                    f"💨 MongoDB template MISS: "
                    f"{recipient_type}/{message_type}/{tone} — falling back to Python dict"
                )
                template = get_template(recipient_type, message_type, tone)
                mongo_subject = None
            
            # 3. Get rights explanation for context
            rights_explanation = await self.explain_rights(disruption_case)
            
            # 4. Build template variables
            template_vars = await self._build_template_variables(
                disruption_case=disruption_case,
                disruption_option=disruption_option,
                rights_explanation=rights_explanation,
                recipient_type=recipient_type,
                recipient_name=recipient_name
            )
            
            # 5. Fill template
            try:
                body = template.format(**template_vars)
            except KeyError as e:
                logger.warning(f"⚠️ Missing template variable: {e}, using AI generation")
                # Fallback to AI generation if template fails
                body = await self._generate_message_with_ai(
                    disruption_case, disruption_option, recipient_type, tone, template_vars
                )
            
            # ✅ PHASE 6 — Step 6: Subject from MongoDB if available, else generate
            if mongo_subject:
                try:
                    subject = mongo_subject.format(
                        flight_number=disruption_case.flight_number,
                        airline_name=disruption_case.airline,
                        origin=disruption_case.origin,
                        destination=disruption_case.destination,
                    )
                    logger.info(f"⚡ Using MongoDB subject template: {subject}")
                except KeyError:
                    subject = self._generate_subject_line(
                        disruption_case, message_type, recipient_type, tone
                    )
            else:
                subject = self._generate_subject_line(
                    disruption_case, message_type, recipient_type, tone
                )
            
            # 7. Determine recipient email
            recipient_email = self._get_recipient_email(
                recipient_type, recipient_name or disruption_case.airline
            )
            
            # 8. List required attachments
            # ✅ PHASE 6 — prefer MongoDB attachments_needed if available
            if mongo_template and mongo_template.get("attachments_needed"):
                attachments_needed = mongo_template["attachments_needed"]
            else:
                attachments_needed = self._get_required_attachments(recipient_type, message_type)
            
            # ✅ PHASE 6 — 9.prefer MongoDB next_steps if available
            if mongo_template and mongo_template.get("next_steps"):
                next_steps = mongo_template["next_steps"]
            else:
                next_steps = self._generate_next_steps(recipient_type, message_type)

            
            # 10. Save to database if db session provided
            draft_message = None
            if db:
                draft_message = DraftMessage(
                    disruption_case_id=disruption_case.id,
                    disruption_option_id=disruption_option.id if disruption_option else None,
                    recipient_type=MessageRecipientType(recipient_type),
                    recipient_name=recipient_name or disruption_case.airline,
                    recipient_email=recipient_email,
                    subject=subject,
                    body=body,
                    tone=MessageTone(tone),
                    language="en",
                    generated_by="ai",
                    ai_model=self.model_name,
                    attachments_needed=json.dumps(attachments_needed)
                )
                
                db.add(draft_message)
                db.commit()
                db.refresh(draft_message)
                
                logger.info(f"✅ Saved draft message {draft_message.id}")
            
            result = {
                "id": draft_message.id if draft_message else None,
                "subject": subject,
                "body": body,
                "recipient_type": recipient_type,
                "recipient_name": recipient_name or disruption_case.airline,
                "recipient_email": recipient_email,
                "tone": tone,
                "attachments_needed": attachments_needed,
                "next_steps": next_steps,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"✅ Generated message for {recipient_type}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to generate message: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                "subject": f"Regarding Flight {disruption_case.flight_number}",
                "body": f"Dear {recipient_name or 'Customer Service'},\n\nI am writing regarding my disrupted flight {disruption_case.flight_number}.\n\n[Please provide details]\n\nSincerely,\n[Your Name]",
                "recipient_email": None,
                "error": str(e)
            }

    def _determine_message_type(
        self,
        disruption_option: Optional[DisruptionOption],
        disruption_case: DisruptionCase
    ) -> str:
        """
        Determine message type based on option or disruption
        """
        if disruption_option:
            option_type = disruption_option.option_type.value
            
            if "refund" in option_type or "compensation" in option_type:
                return "refund"
            elif "alternative_flight" in option_type or "rebooking" in option_type:
                return "rebooking"
            elif "hotel" in option_type:
                return "cancellation"
        
        # Fallback based on disruption type
        if disruption_case.disruption_type == DisruptionType.CANCELLATION:
            return "refund"
        else:
            return "rebooking"


    async def _build_template_variables(
        self,
        disruption_case: DisruptionCase,
        disruption_option: Optional[DisruptionOption],
        rights_explanation: Dict,
        recipient_type: str,
        recipient_name: Optional[str]
    ) -> Dict:
        """
        Build variables for email template
        """
        from datetime import datetime
        
        # Extract flight details
        flight_status = disruption_case.meta_data.get("flight_status", {}) if disruption_case.meta_data else {}
        
        departure_date_str = disruption_case.disruption_date.strftime("%B %d, %Y at %I:%M %p")
        
        # Base variables
        vars = {
            "airline_name": recipient_name or disruption_case.airline,
            "flight_number": disruption_case.flight_number,
            "origin": disruption_case.origin,
            "destination": disruption_case.destination,
            "departure_date": departure_date_str,
            "pnr": disruption_case.pnr or "[Booking Reference]",
            "disruption_type": disruption_case.disruption_type.value,
            "disruption_status": disruption_case.current_status,
            "regulation": rights_explanation.get("applicable_regulation", "applicable passenger rights regulations"),
            "compensation_amount": rights_explanation.get("compensation_amount", 0) or 0,
            "compensation_currency": rights_explanation.get("compensation_currency", "EUR"),
            "enforcement_body": self._get_enforcement_body(rights_explanation.get("region", "UNKNOWN")),
        }
        
        # Option-specific variables
        if disruption_option:
            # Try to access meta_data safely
            try:
                option_meta = disruption_option.meta_data if hasattr(disruption_option, 'meta_data') else None
            except AttributeError:
                logger.warning("⚠️ DisruptionOption missing meta_data attribute")
                option_meta = None
            
            if option_meta:
                # Alternative flight details
                if "flight_details" in option_meta:
                    flight_details = option_meta["flight_details"]
                    vars["alternative_flight"] = flight_details.get("flight_number", "")
                    
                    alt_departure = flight_details.get("departure_time")
                    if alt_departure:
                        try:
                            alt_dt = datetime.fromisoformat(alt_departure)
                            vars["alternative_departure"] = alt_dt.strftime("%B %d, %Y at %I:%M %p")
                        except:
                            vars["alternative_departure"] = alt_departure
                
                # Insurance claim details
                if "insurance_details" in option_meta:
                    ins_details = option_meta["insurance_details"]
                    covered = ins_details.get("covered_expenses", {})
                    
                    vars["hotel_cost"] = covered.get("hotel", 0)
                    vars["meal_cost"] = covered.get("meals", 0)
                    vars["rebooking_cost"] = covered.get("rebooking", 0)
                    vars["transport_cost"] = 0
                    vars["total_claim"] = covered.get("total", 0)
                    vars["currency"] = ins_details.get("currency", "EUR")
                    vars["policy_number"] = "[Your Policy Number]"
                    vars["insurance_provider"] = recipient_name or "[Insurance Provider]"
                    vars["coverage_period"] = "[Coverage Period]"
        
        # Hotel-specific variables
        if recipient_type == "hotel":
            vars["hotel_name"] = recipient_name or "[Hotel Name]"
            vars["booking_reference"] = "[Hotel Confirmation Number]"
            
            # Estimate check-in/out dates
            checkin = disruption_case.disruption_date
            vars["checkin_date"] = checkin.strftime("%B %d, %Y")
            vars["checkout_date"] = (checkin + timedelta(days=2)).strftime("%B %d, %Y")
        
        return vars


    async def _generate_message_with_ai(
        self,
        disruption_case: DisruptionCase,
        disruption_option: Optional[DisruptionOption],
        recipient_type: str,
        tone: str,
        template_vars: Dict
    ) -> str:
        """
        Fallback: Generate message using Gemini AI if template fails
        """
        try:
            prompt = f"""Generate a {tone} email to {recipient_type} regarding flight disruption.

    **Flight Details:**
    - Flight: {template_vars.get('flight_number')}
    - Route: {template_vars.get('origin')} → {template_vars.get('destination')}
    - Date: {template_vars.get('departure_date')}
    - Disruption: {template_vars.get('disruption_status')}

    **Rights:**
    - Regulation: {template_vars.get('regulation')}
    - Compensation: {template_vars.get('compensation_amount')} {template_vars.get('compensation_currency')}

    **Tone:** {tone} ({"assertive and demanding" if tone == "firm" else "professional" if tone == "formal" else "friendly and cooperative"})

    Write a complete email body (no subject line needed):"""
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.config
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"❌ AI generation failed: {e}")
            return f"Dear Customer Service,\n\nI am writing regarding flight {disruption_case.flight_number}.\n\n[Message could not be generated]\n\nSincerely,\n[Your Name]"


    def _generate_subject_line(
        self,
        disruption_case: DisruptionCase,
        message_type: str,
        recipient_type: str,
        tone: str
    ) -> str:
        """
        Generate email subject line
        """
        flight_num = disruption_case.flight_number
        
        subjects = {
            ("airline", "refund", "formal"): f"Refund Request - Flight {flight_num} Cancellation",
            ("airline", "refund", "firm"): f"URGENT: Mandatory Refund & Compensation - Flight {flight_num}",
            ("airline", "refund", "friendly"): f"Refund Request for Flight {flight_num}",
            ("airline", "rebooking", "formal"): f"Rebooking Request - Flight {flight_num}",
            ("airline", "rebooking", "firm"): f"IMMEDIATE Rebooking Required - Flight {flight_num}",
            ("airline", "rebooking", "friendly"): f"Rebooking Assistance Needed - Flight {flight_num}",
            ("hotel", "cancellation", "formal"): f"Cancellation Fee Waiver Request - Flight Disruption",
            ("hotel", "cancellation", "friendly"): f"Help Needed: Cancellation Due to Flight Issue",
            ("insurance", "claim", "formal"): f"Travel Insurance Claim - Flight {flight_num} Disruption",
            ("insurance", "claim", "friendly"): f"Insurance Claim for Trip Disruption",
        }
        
        key = (recipient_type, message_type, tone)
        return subjects.get(key, f"Regarding Flight {flight_num}")


    def _get_recipient_email(self, recipient_type: str, recipient_name: str) -> Optional[str]:
        """
        Get recipient email based on type and name
        """
        # Common airline emails
        airline_emails = {
            "British Airways": "customer.relations@ba.com",
            "American Airlines": "customer.relations@aa.com",
            "Delta": "customer.care@delta.com",
            "United": "customer.care@united.com",
            "Air France": "customer.relations@airfrance.fr",
            "Lufthansa": "customer.relations@dlh.de",
        }
        
        if recipient_type == "airline":
            return airline_emails.get(recipient_name, "customer.service@airline.com")
        elif recipient_type == "hotel":
            return "[hotel_reservations@email.com]"
        elif recipient_type == "insurance":
            return "[claims@insurance.com]"
        
        return None


    def _get_required_attachments(self, recipient_type: str, message_type: str) -> List[str]:
        """
        List required attachments for this message type
        """
        attachments = []
        
        if recipient_type == "airline":
            attachments.extend([
                "Booking confirmation",
                "Flight cancellation notice (if available)"
            ])
            
            if message_type == "refund":
                attachments.append("Payment receipt (original booking)")
        
        elif recipient_type == "hotel":
            attachments.extend([
                "Hotel booking confirmation",
                "Flight cancellation notice from airline"
            ])
        
        elif recipient_type == "insurance":
            attachments.extend([
                "Travel insurance policy document",
                "Flight cancellation notice",
                "Original flight booking confirmation",
                "Alternative flight booking (if rebooked)",
                "Hotel receipts",
                "Meal receipts",
                "Transportation receipts"
            ])
        
        return attachments


    def _generate_next_steps(self, recipient_type: str, message_type: str) -> List[str]:
        """
        Generate actionable next steps after sending message
        """
        steps = []
        
        if recipient_type == "airline":
            steps.extend([
                f"Send this email to the airline's customer service email",
                "Keep a copy of all correspondence for your records",
                "Follow up in 48-72 hours if no response received"
            ])
            
            if message_type == "refund":
                steps.append("Track refund processing (typically 7-10 business days)")
                steps.append("If denied, escalate to aviation authority or use alternative dispute resolution")
        
        elif recipient_type == "hotel":
            steps.extend([
                "Send email to hotel reservations department",
                "Call hotel directly to confirm receipt and discuss",
                "Keep flight cancellation notice handy for reference"
            ])
        
        elif recipient_type == "insurance":
            steps.extend([
                "Submit claim online via insurance provider portal (if available)",
                "Send email with all required documentation",
                "Keep copies of all receipts and correspondence",
                "Note claim reference number for tracking",
                "Follow up after 1-2 weeks for claim status"
            ])
        
        return steps


    def _get_enforcement_body(self, region: str) -> str:
        """
        Get regulatory enforcement body for region
        """
        # ✅ PHASE 5 — expanded to cover all regions in region_mapper
        bodies = {
            "EU": "National Enforcement Body (e.g., CAA in UK, Luftfahrt-Bundesamt in DE)",
            "UK": "UK Civil Aviation Authority (CAA) — caa.co.uk",
            "US": "U.S. Department of Transportation (DOT) — transportation.gov",
            "IN": "Directorate General of Civil Aviation (DGCA) — dgca.gov.in",
            "CA": "Canadian Transportation Agency (CTA) — otc-cta.gc.ca",
            "AU": "Airline Customer Advocate — airlinecustomeradvocate.com.au",
            "AE": "General Civil Aviation Authority (GCAA) — gcaa.gov.ae",
            "GB": "UK Civil Aviation Authority (CAA) — caa.co.uk",  # legacy key
            "GENERAL": "National civil aviation authority of your departure country"
        }
        
        return bodies.get(region, "relevant aviation authority")

    async def _generate_alternative_flight_options(
        self,
        disruption_case: DisruptionCase,
        origin_iata: str,
        destination_iata: str,
        db: Session
    ) -> List[DisruptionOption]:
        """
        Generate alternative flight options using SerpAPI
        """
        try:
            from app.services.disruption_service import disruption_service
            from app.models.disruption import DisruptionOption, OptionType
            import json
            
            logger.info(f"✈️ Searching alternative flights: {origin_iata} → {destination_iata}")
            
            # Get departure date
            departure_date = disruption_case.disruption_date.strftime("%Y-%m-%d")
            
            # Search alternative flights
            alternative_flights = await disruption_service.search_alternative_flights(
                origin_iata=origin_iata,
                destination_iata=destination_iata,
                departure_date=departure_date,
                cabin_class="economy",
                max_results=3
            )

            # ✅ ADD THIS - Log what SerpAPI returned
            logger.info(f"🔍 SerpAPI returned flights:")
            for idx, flight in enumerate(alternative_flights):
                logger.info(f"  Flight {idx+1}: {flight['flight_number']}")
                logger.info(f"    Departure: {flight['departure_time']}")
                logger.info(f"    Arrival: {flight['arrival_time']}")
                logger.info(f"    Duration: {flight['duration_minutes']} minutes ({flight['duration_minutes']/60:.1f} hours)")
                logger.info(f"    Stops: {flight['stops']}")
                logger.info(f"    Price: ${flight['price_amount']}")
            
            if not alternative_flights:
                logger.warning("⚠️ No alternative flights found")
                return []
            
            # Create DisruptionOption for each flight
            flight_options = []
            
            for i, flight in enumerate(alternative_flights):
                # Calculate time difference
                original_time = disruption_case.disruption_date
                new_departure = datetime.fromisoformat(flight["departure_time"])
                time_diff_hours = (new_departure - original_time).total_seconds() / 3600
                
                # Build pros/cons
                pros = []
                cons = []
                
                if flight["stops"] == 0:
                    pros.append("Direct flight")
                else:
                    cons.append(f"{flight['stops']} stop(s)")
                
                if flight["airline"] == disruption_case.airline:
                    pros.append("Same airline - easier rebooking")
                else:
                    cons.append("Different airline - may require new booking")
                
                if abs(time_diff_hours) < 2:
                    pros.append("Similar departure time")
                elif time_diff_hours > 0:
                    cons.append(f"Departs {int(time_diff_hours)} hours later")
                
                # Duration check
                if flight["duration_minutes"] < 300:  # < 5 hours
                    pros.append("Short flight time")
                
                # Create option
                option = DisruptionOption(
                    disruption_case_id=disruption_case.id,
                    option_type=OptionType.ALTERNATIVE_FLIGHT,
                    title=f"Rebook on {flight['flight_number']} ({flight['airline']})",
                    description=f"Alternative flight departing at {new_departure.strftime('%I:%M %p')}",
                    estimated_cost=flight["price_amount"],
                    action_required=f"Contact {flight['airline']} or use booking link to rebook",
                    booking_url=flight.get("booking_url"),
                    contact_info=f"{flight['airline']} customer service",
                    priority_rank=100 - (i * 10),  # First flight gets highest rank
                    ai_reasoning=f"Alternative flight with {flight['stops']} stop(s), duration {flight['duration_minutes']}min"
                    
                )
                option.meta_data =json.dumps( {
                    "flight_details": {
                        "flight_number": flight["flight_number"],
                        "airline": flight["airline"],
                        "departure_time": flight["departure_time"],
                        "arrival_time": flight["arrival_time"],
                        "duration_minutes": flight["duration_minutes"],
                        "stops": flight["stops"],
                        "price_amount": flight["price_amount"],
                        "price_currency": flight["price_currency"],
                        "price_difference": 0,
                    },
                    "pros": pros,
                    "cons": cons,
                    "recommended": i == 0
                })
                db.add(option)
                flight_options.append(option)
            
            db.commit()
            
            # Refresh to get IDs
            for option in flight_options:
                db.refresh(option)
            
            logger.info(f"✅ Generated {len(flight_options)} alternative flight options")
            
            return flight_options
            
        except Exception as e:
            logger.error(f"❌ Failed to generate flight options: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    async def _generate_refund_option(
        self,
        disruption_case: DisruptionCase,
        rights_explanation: Dict,
        db: Session
    ) -> Optional[DisruptionOption]:
        """
        Generate refund + compensation option based on passenger rights
        """
        try:
            from app.models.disruption import DisruptionOption, OptionType
            import json
            
            # Extract compensation info from rights explanation
            compensation_amount = rights_explanation.get("compensation_amount", 0) or 0
            compensation_currency = rights_explanation.get("compensation_currency", "EUR")
            
            # Estimate ticket refund (we don't have actual ticket price, so estimate)
            # In production, fetch from booking system
            estimated_ticket_price = self._estimate_ticket_price(
                disruption_case.origin,
                disruption_case.destination
            )
            
            total_refund = compensation_amount + estimated_ticket_price
            
            # Build pros/cons
            pros = []
            cons = []
            
            if compensation_amount > 0:
                pros.append(f"EU261 compensation: {compensation_currency}{compensation_amount}")
                pros.append("Full ticket refund")
                pros.append("Guaranteed by regulation")
            else:
                pros.append("Full ticket refund (if eligible)")
                cons.append("No mandatory compensation in this region")
            
            cons.append("Need to book alternative flight separately")
            cons.append("Processing time: 7-10 business days")
            
            # Create option
            option = DisruptionOption(
                disruption_case_id=disruption_case.id,
                option_type=OptionType.REFUND,
                title=f"Request full refund" + (f" + €{compensation_amount} compensation" if compensation_amount > 0 else ""),
                description=f"Claim ticket refund and {rights_explanation.get('applicable_regulation', 'passenger rights')} compensation",
                estimated_cost=-total_refund,  # Negative = money back
                action_required="File refund claim via airline website or email",
                contact_info=f"{disruption_case.airline} customer service",
                priority_rank=80,  # High priority if compensation > 0, else medium
                ai_reasoning=f"Entitled to {compensation_currency}{compensation_amount} under {rights_explanation.get('applicable_regulation', 'regulations')}"
            )
            option.meta_data = {
                "refund_details": {
                    "ticket_refund": estimated_ticket_price,
                    "compensation": compensation_amount,
                    "total": total_refund,
                    "currency": compensation_currency,
                    "regulation": rights_explanation.get("applicable_regulation")
                },
                "pros": pros,
                "cons": cons,
                "recommended": compensation_amount >= 250
            }
            db.add(option)
            db.commit()
            db.refresh(option)
            
            logger.info(f"✅ Generated refund option: {compensation_currency}{total_refund}")
            
            return option
            
        except Exception as e:
            logger.error(f"❌ Failed to generate refund option: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def _generate_hotel_cancellation_option(
        self,
        disruption_case: DisruptionCase,
        db: Session
    ) -> Optional[DisruptionOption]:
        """
        Generate hotel cancellation option (generic advice)
        """
        try:
            from app.models.disruption import DisruptionOption, OptionType
            import json
            
            # Estimate average hotel cost for destination
            estimated_hotel_cost = self._estimate_hotel_cost(disruption_case.destination)
            
            pros = [
                "Most hotels waive fees for flight cancellations",
                "Save cancellation penalty",
                "Get full refund if documented"
            ]
            
            cons = [
                "Need to contact hotel directly",
                "Requires proof of flight cancellation",
                "May need to rebook for new dates"
            ]
            
            option = DisruptionOption(
                disruption_case_id=disruption_case.id,
                option_type=OptionType.HOTEL_VOUCHER,
                title="Request hotel cancellation",
                description="Contact hotel to waive cancellation fee due to flight disruption",
                estimated_cost=-estimated_hotel_cost,  # Potential savings
                action_required="Call hotel with flight cancellation proof",
                contact_info="Hotel front desk or reservations",
                priority_rank=70,
                ai_reasoning="Hotels typically honor cancellations for documented flight disruptions"
            )
            option.meta_data = {
                "hotel_details": {
                    "estimated_refund": estimated_hotel_cost,
                    "currency": "EUR"
                },
                "pros": pros,
                "cons": cons,
                "recommended": True
            }
            db.add(option)
            db.commit()
            db.refresh(option)
            
            logger.info(f"✅ Generated hotel cancellation option")
            
            return option
            
        except Exception as e:
            logger.error(f"❌ Failed to generate hotel option: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def _generate_insurance_claim_option(
        self,
        disruption_case: DisruptionCase,
        rights_explanation: Dict,
        db: Session
    ) -> Optional[DisruptionOption]:
        """
        Generate travel insurance claim option
        """
        try:
            from app.models.disruption import DisruptionOption, OptionType
            import json
            
            # Only suggest if delay/cancellation is significant
            flight_status = disruption_case.meta_data.get("flight_status", {}) if disruption_case.meta_data else {}
            delay_minutes = self._extract_delay_minutes(flight_status, disruption_case)
            
            # Skip if delay is minor (< 3 hours)
            if delay_minutes and delay_minutes < 180:
                return None
            
            # Estimate covered expenses
            hotel_cost = self._estimate_hotel_cost(disruption_case.destination)
            meal_cost = 50  # Estimate
            rebooking_cost = 200  # Estimate
            
            total_claim = hotel_cost + meal_cost + rebooking_cost
            
            pros = [
                "Covers expenses beyond airline compensation",
                "May include hotel, meals, rebooking",
                "Additional to EU261/DOT rights"
            ]
            
            cons = [
                "Requires comprehensive travel insurance",
                "Need documentation (receipts, notices)",
                "Processing time: 2-4 weeks"
            ]
            
            option = DisruptionOption(
                disruption_case_id=disruption_case.id,
                option_type=OptionType.COMPENSATION,
                title="File travel insurance claim",
                description="Claim reimbursement for disruption expenses",
                estimated_cost=-total_claim,
                action_required="Submit claim with receipts and cancellation notice",
                contact_info="Insurance provider claims department",
                priority_rank=60,
                ai_reasoning="Most comprehensive policies cover delays >3 hours or cancellations"
            )
            option.meta_data = {
                "insurance_details": {
                    "covered_expenses": {
                        "hotel": hotel_cost,
                        "meals": meal_cost,
                        "rebooking": rebooking_cost,
                        "total": total_claim
                    },
                    "currency": "EUR"
                },
                "pros": pros,
                "cons": cons,
                "recommended": False
            }
            db.add(option)
            db.commit()
            db.refresh(option)
            
            logger.info(f"✅ Generated insurance claim option: EUR{total_claim}")
            
            return option
            
        except Exception as e:
            logger.error(f"❌ Failed to generate insurance option: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def _rank_options_with_ai(
        self,
        options: List[DisruptionOption],
        disruption_case: DisruptionCase,
        rights_explanation: Dict
    ) -> List[DisruptionOption]:
        """
        Use Gemini AI to intelligently rank options based on passenger situation
        """
        try:
            if not options:
                return []
            
            # Build prompt for AI ranking
            prompt = f"""You are a travel expert helping rank disruption resolution options for a passenger.

    **Passenger Situation:**
    - Flight: {disruption_case.flight_number} ({disruption_case.airline})
    - Route: {disruption_case.origin} → {disruption_case.destination}
    - Disruption: {disruption_case.disruption_type.value}
    - Status: {disruption_case.current_status}
    - Rights: {rights_explanation.get('applicable_regulation', 'Unknown')}

    **Available Options:**
    """
            
            for i, option in enumerate(options):
                pros = option.meta_data.get("pros", []) if option.meta_data else []
                cons = option.meta_data.get("cons", []) if option.meta_data else []
                
                prompt += f"\n{i+1}. {option.title} ({option.option_type.value})"
                prompt += f"\n   Cost: {option.estimated_cost}"
                prompt += f"\n   Pros: {', '.join(pros)}"
                prompt += f"\n   Cons: {', '.join(cons)}\n"
            
            prompt += """
    **Your Task:**
    Rank these options from BEST to WORST for this passenger. Consider:
    - Financial benefit (money saved/received)
    - Convenience (ease of execution)
    - Time to resolution
    - Certainty of success

    **Response Format:**
    Return ONLY a comma-separated list of option numbers in ranked order (best first).
    Example: 2,1,4,3

    Your ranking:"""
            
            # Call Gemini
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.config
            )
            
            # Parse ranking
            ranking_text = response.text.strip()
            logger.info(f"🤖 AI ranking: {ranking_text}")
            
            # Extract numbers
            import re
            numbers = re.findall(r'\d+', ranking_text)
            
            if numbers:
                # Reorder options based on AI ranking
                ranked_options = []
                for num in numbers:
                    idx = int(num) - 1  # Convert to 0-based index
                    if 0 <= idx < len(options):
                        ranked_options.append(options[idx])
                
                # Add any missing options at the end
                for option in options:
                    if option not in ranked_options:
                        ranked_options.append(option)
                
                # Update priority_rank based on new order
                for i, option in enumerate(ranked_options):
                    option.priority_rank = 100 - (i * 10)
                
                return ranked_options
            else:
                # Fallback: keep original order
                return options
            
        except Exception as e:
            logger.error(f"❌ AI ranking failed: {e}")
            # Fallback: sort by estimated_cost (most savings first)
            return sorted(options, key=lambda x: x.estimated_cost)

    async def chat(
        self,
        disruption_case: DisruptionCase,
        user_message: str,
        conversation_history: List = None,
        db: Session = None
    ) -> str:
        """
        Chat with user about their disruption case
        
        Provides context-aware responses using:
        - Case details (flight, dates, status)
        - Passenger rights (EU261, DOT, etc.)
        - Available options (flights, refunds, hotels)
        - Policy documents from RAG
        """
        logger.info(f"💬 Chat for case {disruption_case.id}: {user_message[:50]}...")
        
        try:
            # Build context about the case
            case_context = f"""
    Current Disruption Case:
    - Flight: {disruption_case.flight_number} ({disruption_case.airline})
    - Route: {disruption_case.origin} → {disruption_case.destination}
    - Date: {disruption_case.disruption_date.strftime('%B %d, %Y')}
    - Status: {disruption_case.current_status}
    - Severity: {disruption_case.severity.value}
    - Type: {disruption_case.disruption_type.value}
    """
            
            # Get rights explanation
            try:
                rights = await self.explain_rights(disruption_case)
                rights_context = f"""
    Passenger Rights:
    - Regulation: {rights.get('applicable_regulation', 'Unknown')}
    - Compensation: {rights.get('compensation_currency', '')}{rights.get('compensation_amount', 0) or 'Not eligible'}
    - Key Rights: {', '.join(rights.get('rights_bullets', [])[:3])}
    """
            except:
                rights_context = "Passenger rights information not available."
            
            # Get available options
            try:
                options = db.query(DisruptionOption).filter(
                    DisruptionOption.disruption_case_id == disruption_case.id
                ).limit(3).all() if db else []
                
                options_context = "Available Options:\n"
                for opt in options:
                    options_context += f"- {opt.title}: {opt.description}\n"
            except:
                options_context = "Options information not available."
            
            # ✅ Build conversation history - Handle both dict and Pydantic objects
            history_text = ""
            if conversation_history:
                for msg in conversation_history[-5:]:  # Last 5 messages
                    # Check if it's a Pydantic object or dict
                    if hasattr(msg, 'role'):
                        role = msg.role
                        content = msg.content
                    else:
                        role = msg.get('role', 'user')
                        content = msg.get('content', '')
                    history_text += f"{role.title()}: {content}\n"
            
            # Create prompt
            prompt = f"""You are an AI travel assistant helping a passenger with a flight disruption.

    {case_context}

    {rights_context}

    {options_context}

    Recent Conversation:
    {history_text if history_text else "This is the start of the conversation."}

    User Question: {user_message}

    Instructions:
    1. Provide helpful, accurate information about the disruption
    2. Reference specific details from the case context above
    3. If asked about rights, mention the compensation amount and key entitlements
    4. If asked about options, suggest the best alternatives from the list
    5. Be concise (2-3 sentences) but informative
    6. Use a friendly, professional tone
    7. If you don't have specific information, be honest and suggest checking the dashboard cards

    Response:"""

            # ✅ Generate response using existing model instance
            response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=self.config
        )
            
            answer = response.text.strip()
            
            logger.info(f"✅ Chat response generated ({len(answer)} chars)")
            
            return answer
            
        except Exception as e:
            logger.error(f"❌ Chat failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Fallback response
            return f"I apologize, but I encountered an error processing your question. Please check the dashboard cards for information about your disruption, or try asking your question differently."


    def _extract_airport_code(self, location: str) -> str:
        """
        Extract IATA airport code from location string
        """
        # If already an IATA code (3 letters)
        if len(location) == 3 and location.isalpha():
            return location.upper()
        
        # Try to extract from airport database
        try:
            from app.services.disruption_service import disruption_service
            
            airports_db = disruption_service.airports_db
            location_lower = location.lower().strip()
            
            # Search by city name
            for iata_code, airport_data in airports_db.items():
                if airport_data.get("city", "").lower() == location_lower:
                    return iata_code
            
        except Exception as e:
            logger.warning(f"⚠️ Could not extract airport code: {e}")
        
        # Fallback: return original
        return location.upper()


    def _estimate_ticket_price(self, origin: str, destination: str) -> float:
        """
        Estimate ticket price based on route (simplified)
        In production, fetch from booking system or flight search API
        """
        # Simple estimates based on route distance/popularity
        estimates = {
            ("London", "Paris"): 150,
            ("New York", "Los Angeles"): 300,
            ("Mumbai", "Paris"): 500,
        }
        
        # Try to find matching route
        for (orig, dest), price in estimates.items():
            if orig.lower() in origin.lower() or dest.lower() in destination.lower():
                return price
        
        # Default estimate
        return 250


    def _estimate_hotel_cost(self, destination: str) -> float:
        """
        Estimate average hotel cost for destination
        """
        # Simple estimates by city
        estimates = {
            "Paris": 180,
            "London": 200,
            "New York": 220,
            "Los Angeles": 150,
            "Mumbai": 80,
        }
        
        for city, cost in estimates.items():
            if city.lower() in destination.lower():
                return cost
        
        # Default
        return 150

# Singleton instance
disruption_agent = DisruptionAgent()
