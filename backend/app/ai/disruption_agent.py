"""
Disruption Agent - AI agent for explaining passenger rights and suggesting options

Uses:
- RightsRetriever to fetch policies
- Gemini AI to synthesize explanations
- LangChain for structured outputs
"""
from typing import Dict, List, Optional
from datetime import datetime,timezone
import logging
from google import genai
from google.genai import types

from app.core.config import settings
from app.ai.retrievers import create_rights_retriever
from app.models.disruption import DisruptionCase, DisruptionType
from langchain.schema import Document


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
            - cached: Whether data was cached
        """
        logger.info(f"🤖 Explaining rights for case {disruption_case.id}")
        
        try:
            # 1. Extract route information
            origin_country = self._extract_country_from_airport_or_city(disruption_case.origin)
            destination_country = self._extract_country_from_airport_or_city(disruption_case.destination)
            
            logger.info(f"📍 Route: {disruption_case.origin} ({origin_country}) → {disruption_case.destination} ({destination_country})")
            # 2. Retrieve relevant policies using RightsRetriever
            retriever = create_rights_retriever(
                airline=disruption_case.airline,
                origin_country=origin_country,
                destination_country=destination_country,
                disruption_type=disruption_case.disruption_type.value,
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
            
            # 4. Synthesize explanation using Gemini
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
                "region": origin_country,
                "applicable_regulation": explanation.get("applicable_regulation", ""),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
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


# Singleton instance
disruption_agent = DisruptionAgent()
