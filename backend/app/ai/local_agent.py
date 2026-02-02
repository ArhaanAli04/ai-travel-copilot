"""
Local Discovery Agent - RAG-powered POI recommendations using Gemini
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging
from difflib import get_close_matches
from app.services.local_discovery_service import local_discovery_service
from app.ai.gemini_client import get_gemini_client
from app.core.mongo import get_database

logger = logging.getLogger(__name__)


class LocalDiscoveryAgent:
    """Agent for generating personalized local recommendations using RAG"""
    
    def __init__(self):
        """Initialize the agent"""
        self.gemini_client = None
    
    def _get_client(self):
        """Lazy load Gemini client"""
        if self.gemini_client is None:
            self.gemini_client = get_gemini_client()
        return self.gemini_client
    
    async def suggest_local_experiences(
        self,
        user_query: str,
        lat: float,
        lon: float,
        city: str,
        preferences: Optional[Dict[str, Any]] = None,
        radius_km: float = 5.0,
        max_results: int = 5
    ) -> Dict:
        """
        Generate personalized local recommendations using RAG
        
        Args:
            user_query: User's search query (e.g., "romantic dinner spot")
            lat: User's latitude
            lon: User's longitude
            city: City name
            preferences: User preferences (dietary, budget, time, etc.)
            radius_km: Search radius in kilometers
            max_results: Maximum number of recommendations
            
        Returns:
            Dict with recommendations and sources
        """
        try:
            logger.info(f"🤖 Local Agent - Processing query: '{user_query}'")
            logger.info(f"🎯 Preferences received: {preferences}")
            
            # ✅ NEW: Extract preferences from query if not provided
            if not preferences or not any(preferences.values()):
                logger.info("  🧠 No preferences set, extracting from query...")
                extracted_prefs = await self._extract_preferences_from_query(user_query)
                preferences = extracted_prefs
                logger.info(f"  ✅ Extracted preferences: {preferences}")

            # Step 1: Get POI candidates + context using hybrid search
            search_results = await local_discovery_service.hybrid_search(
                query=user_query,
                user_location={"lat": lat, "lon": lon},
                city=city,
                radius_km=radius_km,
                categories=self._extract_categories_from_preferences(preferences),
                cuisines=self._extract_cuisines_from_preferences(preferences),
                limit=15,  # Get more candidates for better selection
                include_context=True
            )
            
            pois = search_results.get("pois", [])

            # NEW: Fallback if no results with filters
            if not pois and (preferences and (preferences.get("cuisines") or preferences.get("categories"))):
                logger.warning("  ⚠️ No POIs found with filters, retrying without cuisine filter...")
                
                # Retry with only category filter (no cuisine)
                search_results = await local_discovery_service.hybrid_search(
                    query=user_query,
                    user_location={"lat": lat, "lon": lon},
                    city=city,
                    radius_km=radius_km,
                    categories=self._extract_categories_from_preferences(preferences),
                    cuisines=None,  # Remove cuisine filter
                    limit=15,
                    include_context=True
                )
                pois = search_results.get("pois", [])
                
                # If still no results, remove all filters
                if not pois:
                    logger.warning("  ⚠️ No POIs found with category filter, retrying without filters...")
                    search_results = await local_discovery_service.hybrid_search(
                        query=user_query,
                        user_location={"lat": lat, "lon": lon},
                        city=city,
                        radius_km=radius_km,
                        categories=None,
                        cuisines=None,
                        limit=15,
                        include_context=True
                    )
                    pois = search_results.get("pois", [])

            context_docs = search_results.get("context", [])
            
            if not pois:
                return {
                    "recommendations": [],
                    "total_found": 0,
                    "query": user_query,
                    "location": {"lat": lat, "lon": lon},
                    "city": city,
                    "sources": [],
                    "search_radius_km": radius_km,
                    "message": f"No places found matching '{user_query}' within {radius_km}km"
                }
            
            logger.info(f"  Found {len(pois)} POI candidates")
            logger.info(f"  Found {len(context_docs)} context documents")
            
            # Step 2: Build RAG prompt
            rag_prompt = self._build_rag_prompt(
                user_query=user_query,
                user_location={"lat": lat, "lon": lon},
                preferences=preferences or {},
                pois=pois[:15],  # Limit POIs in prompt
                context_docs=context_docs[:10]  # Limit context
            )
            
            # Step 3: Generate recommendations with Gemini
            logger.info("  Generating recommendations with Gemini...")
            recommendations = await self._generate_recommendations(
                rag_prompt,
                max_results=max_results
            )
            
            # ✅ NEW: Fallback if no recommendations
            if not recommendations and len(pois) >= 3:
                logger.warning("  ⚠️ No recommendations generated, retrying with relaxed prompt...")
                
                # Build a simpler prompt without strict filtering
                fallback_prompt = self._build_fallback_prompt(
                    user_query=user_query,
                    pois=pois[:10]
                )
                
                recommendations = await self._generate_recommendations(
                    fallback_prompt,
                    max_results=max_results
                )

            # Step 4: Enrich recommendations with full POI data
            enriched_recommendations = await self._enrich_recommendations(
                recommendations,
                pois
            )
            
            # Step 4.5: Remove duplicates (NEW)
            enriched_recommendations = self._deduplicate_recommendations(enriched_recommendations)

            # Step 5: Extract sources
            sources = self._extract_sources(context_docs)
            
            return {
                "recommendations": enriched_recommendations,
                "total_found": len(pois),
                "query": user_query,
                "location": {"lat": lat, "lon": lon},
                "city": city,
                "sources": sources,
                "search_radius_km": radius_km
            }
        
        except Exception as e:
            logger.error(f"❌ Error in suggest_local_experiences: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _extract_categories_from_preferences(
        self,
        preferences: Optional[Dict]
    ) -> Optional[List[str]]:
        """Extract categories from preferences"""
        if not preferences:
            return None
        
        categories = preferences.get("categories") or []
        categories=list(categories)

        # Also check cuisines for category-like values (cafe, restaurant, bar, etc.)
        cuisines = preferences.get("cuisines") or []
        category_keywords = ["cafe", "restaurant", "bar", "pub", "bakery", "fast_food"]

        for cuisine in cuisines:
            if cuisine and cuisine.lower() in category_keywords and cuisine not in categories:
                categories.append(cuisine.lower())
        
        logger.info(f"  📂 Extracted categories: {categories}")
        return categories if categories else None
    
    def _extract_cuisines_from_preferences(
        self,
        preferences: Optional[Dict]
    ) -> Optional[List[str]]:
        """Extract cuisines from preferences"""
        if not preferences:
            return None
        
        # Get cuisines from preferences
        cuisines = preferences.get("cuisines")
        if not cuisines:
            return None
        
        # Ensure it's a list
        if not isinstance(cuisines, list):
            cuisines = [cuisines]
        
        # Filter out category-like values
        category_keywords = ["cafe", "restaurant", "bar", "pub", "bakery", "fast_food"]
        actual_cuisines = [
            cuisine for cuisine in cuisines 
            if cuisine and cuisine.lower() not in category_keywords
        ]
        # ✅ Use print instead of logger to debug
        if actual_cuisines:
            logger.info("  🍽️ Extracted cuisines: %s", actual_cuisines)
        
        
        return actual_cuisines if actual_cuisines else None
    
    def _build_rag_prompt(
        self,
        user_query: str,
        user_location: Dict,
        preferences: Dict,
        pois: List[Dict],
        context_docs: List[Dict]
    ) -> str:
        """
        Build RAG prompt with user context, POIs, and supporting documents
        
        This creates a comprehensive prompt that includes:
        1. System instructions (local guide expert)
        2. User context (location, time, preferences)
        3. POI candidates (name, category, distance, tags)
        4. Supporting context (blog posts, tips, reviews)
        5. Output format instructions (structured JSON)
        """
        
        # Current time
        current_time = datetime.now()
        time_str = current_time.strftime("%A, %I:%M %p")
        
        # Build user context section
        user_context = f"""
        **User Context:**
        - Query: "{user_query}"
        - Location: ({user_location['lat']}, {user_location['lon']})
        - Current Time: {time_str}
        """
        
        # Add preferences if provided
        if preferences:
            user_context += "\n**User Preferences (IMPORTANT - Follow these strictly):**\n"
            
            if preferences.get("dietary"):
                user_context += f"  - ⚠️ DIETARY RESTRICTIONS: {', '.join(preferences['dietary'])} (MUST match)\n"
            
            if preferences.get("cuisines"):
                user_context += f"  - 🍽️ CUISINE PREFERENCES: {', '.join(preferences['cuisines'])} (Prioritize these)\n"
            
            if preferences.get("categories"):
                user_context += f"  - 📂 PLACE CATEGORIES: {', '.join(preferences['categories'])} (Filter by these)\n"
            
            if preferences.get("budget"):
                user_context += f"  - 💰 Budget: {preferences['budget']}\n"
            
            if preferences.get("time_constraint"):
                user_context += f"  - ⏱️ Time Available: {preferences['time_constraint']}\n"
            
            if preferences.get("group_size"):
                user_context += f"  - 👥 Group Size: {preferences['group_size']} people\n"
        
        # Build POI candidates section
        poi_section = "\n**Available Places (POI Candidates):**\n"
        for idx, poi in enumerate(pois[:15], 1):
            name = poi.get("name", "Unknown")
            category = poi.get("category", "unknown")
            distance_text = poi.get("distance_text", "N/A")
            
            tags = poi.get("tags", {})
            cuisine = tags.get("cuisine", "")
            hours = poi.get("hours", "Hours not available")
            
            poi_section += f"""
            {idx}. **{name}** (Cuisine: {cuisine})
            - Category: {category}
            - Distance: {distance_text}
            - Cuisine: {cuisine if cuisine else 'N/A'}
            - Hours: {hours}
            """
            
            # Add dietary info if available
            dietary_info = []
            if tags.get("diet:vegetarian") == "yes":
                dietary_info.append("vegetarian-friendly")
            if tags.get("diet:vegan") == "yes":
                dietary_info.append("vegan options")
            if tags.get("diet:halal") == "yes":
                dietary_info.append("halal")
            
            if dietary_info:
                poi_section += f"   - Dietary: {', '.join(dietary_info)}\n"
            
            # Add special features
            features = []
            if tags.get("outdoor_seating") == "yes":
                features.append("outdoor seating")
            if tags.get("wifi") == "yes":
                features.append("WiFi")
            if tags.get("wheelchair") == "yes":
                features.append("wheelchair accessible")
            
            if features:
                poi_section += f"   - Features: {', '.join(features)}\n"
        
        # Build context section (blogs, tips, reviews)
        context_section = "\n**Local Insights & Context:**\n"
        if context_docs:
            for idx, doc in enumerate(context_docs[:10], 1):
                payload = doc.get("payload", {})
                source = payload.get("source", "unknown")
                
                if source == "blog":
                    title = payload.get("title", "")
                    preview = payload.get("content_preview", "")
                    context_section += f"{idx}. [Blog] {title}\n   {preview[:200]}...\n\n"
                
                elif source == "foursquare_tip":
                    tip_text = payload.get("text", "")
                    context_section += f"{idx}. [Local Tip] {tip_text[:200]}...\n\n"
                
                elif source == "osm":
                    poi_name = payload.get("name", "")
                    description = payload.get("description", "")
                    context_section += f"{idx}. [POI Info] {poi_name}: {description[:150]}...\n\n"
        else:
            context_section += "No additional context available.\n"
        
        # Build the complete RAG prompt
        prompt = f"""You are a local guide expert helping travelers discover amazing experiences. Your goal is to provide personalized, practical recommendations based on the user's query and preferences.

        {user_context}

        {poi_section}

        {context_section}

        **Instructions:**
        1. Analyze the user's query and preferences carefully
        2. **IMPORTANT:** Select ONLY from the "Available Places (POI Candidates)" list above
        3. **CRITICAL:** Use the EXACT POI names as written in the candidates list - copy them character-by-character
        4. **DO NOT make up, modify, or invent any place names**
        5. **DO NOT add extra words or change spelling of POI names** (e.g., don't change "Mainland China" to "Mainlaand China")
        6. If user preferences are provided, STRICTLY FILTER by dietary restrictions and category preferences
        7. If NO preferences are set but the query mentions constraints (e.g., "Chinese cuisine", "moderate budget", "group of 4"), use the POI list flexibly and match based on the query context and available POI information
        8. Consider: relevance to query, distance, opening hours, dietary needs, and user preferences/query requirements
        9. Prioritize POIs that best match the query intent, even if not perfect matches
        10. If you cannot find 5 suitable places, return fewer recommendations (quality over quantity)

        **CRITICAL RULE:** The "poi_name" in your response MUST be an EXACT CHARACTER-BY-CHARACTER COPY from the "Available Places" list above. Look at the list, find the place, and copy-paste the name precisely. Do not modify or invent names.
        
        **Matching Strategy:**
        - If user preferences are set (cuisines, categories, dietary): Follow them STRICTLY
        - If NO preferences but query mentions requirements: Match based on POI tags, cuisine info, and context - be flexible and use best judgment
        - Always prioritize relevance to the user's stated needs

        **Output Format (JSON):**
        Return ONLY a valid JSON object with this structure:
        ```json
        {{
        "recommendations": [
            {{
            "poi_name": "Exact name from POI list -copy it precisely",
            "reason": "Why this place matches the user's needs(2-3 sentences)",
            "highlights": ["key feature 1", "key feature 2"],
            "best_for": "Quick description of ideal use case"
            }}
        ]
        }}
        Example of CORRECT name matching:

            POI list has: "Mainland China"

            Your response: "poi_name": "Mainland China" ✅

            NOT: "Mainlaand China" ❌

            NOT: "Mainland China Restaurant" ❌
        Generate recommendations now:"""
        return prompt
    
    async def _generate_recommendations(
        self,
        rag_prompt: str,
        max_results: int = 5
    ) -> List[Dict]:
        """
        Generate recommendations using Gemini
        
        Args:
            rag_prompt: Complete RAG prompt
            max_results: Maximum recommendations to return
            
        Returns:
            List of recommendation dicts
        """
        try:
            client = self._get_client()
            
            # Call Gemini with JSON response mode
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=rag_prompt,
                config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                    "response_mime_type": "application/json"
                }
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()
            
            recommendations_data = json.loads(response_text)
            recommendations = recommendations_data.get("recommendations", [])
            
            logger.info(f"  ✅ Generated {len(recommendations)} recommendations")
            
            return recommendations[:max_results]
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response.text}")
            return []
        
        except Exception as e:
            logger.error(f"❌ Failed to generate recommendations: {e}")
            return []

    async def _enrich_recommendations(
        self,
        recommendations: List[Dict],
        pois: List[Dict]
    ) -> List[Dict]:
        """
        Enrich recommendations with full POI data
        
        Matches recommendation names with POI objects and adds complete details
        Uses fuzzy matching to handle slight name variations
        """
        enriched = []
        
        # Create POI lookup by name (case-insensitive)
        poi_lookup = {poi["name"].lower(): poi for poi in pois}
        poi_names = list(poi_lookup.keys())
        
        for rec in recommendations:
            poi_name = rec.get("poi_name", "")
            poi_name_lower = poi_name.lower()
            
            # Try exact match first
            poi = poi_lookup.get(poi_name_lower)
            
            # If no exact match, try fuzzy matching
            if not poi and poi_name:
                logger.warning(f"  🔍 Exact match failed for: '{poi_name}', trying fuzzy match...")
                
                # Find close matches (allows for minor typos/spacing)
                close_matches = get_close_matches(
                    poi_name_lower,
                    poi_names,
                    n=1,
                    cutoff=0.75  # 75% similarity threshold
                )
                
                if close_matches:
                    matched_name = close_matches[0]
                    poi = poi_lookup[matched_name]
                    logger.info(f"  ✅ Fuzzy matched '{poi_name}' → '{poi['name']}'")
                else:
                    logger.warning(f"  ⚠️ Could not find POI: '{poi_name}' (no close matches)")
                    continue
            
            if poi:
                enriched.append({
                    "poi_id": str(poi.get("_id")),
                    "name": poi.get("name"),
                    "category": poi.get("category"),
                    "distance_km": poi.get("distance_km"),
                    "distance_text": poi.get("distance_text"),
                    "location": poi.get("location"),
                    "address": poi.get("address"),
                    "phone": poi.get("phone"),
                    "website": poi.get("website"),
                    "hours": poi.get("hours"),
                    "tags": poi.get("tags", {}),
                    "reason": rec.get("reason", ""),
                    "highlights": rec.get("highlights", []),
                    "best_for": rec.get("best_for", ""),
                    "relevance_score": poi.get("relevance_score"),
                    # Feedback stats
                    "average_rating": poi.get("average_rating", 0.0),
                    "feedback_count": poi.get("feedback_count", 0),
                    "positive_feedback_count": poi.get("positive_feedback_count", 0),
                    "negative_feedback_count": poi.get("negative_feedback_count", 0)
                })
        
        return enriched

    def _deduplicate_recommendations(self, recommendations: List[Dict]) -> List[Dict]:
        """
        Remove duplicate places based on name and address
        
        Sometimes the same place appears multiple times in the database
        with slightly different coordinates or IDs
        """
        seen = set()
        deduplicated = []
        
        for rec in recommendations:
            # Create unique key from name + address
            name = (rec.get("name") or "").lower().strip()
            address = (rec.get("address") or "").lower().strip()
            
            # Use first 50 chars of address to handle minor variations
            key = f"{name}_{address[:50]}"
            
            if key not in seen:
                seen.add(key)
                deduplicated.append(rec)
            else:
                logger.warning(f"  🚫 Removed duplicate: {rec.get('name')}")
        
        return deduplicated

    def _extract_sources(self, context_docs: List[Dict]) -> List[Dict]:
        """Extract source information from context documents"""
        sources = []
        seen_urls = set()
        
        for doc in context_docs[:5]:  # Limit to top 5 sources
            payload = doc.get("payload", {})
            source_type = payload.get("source", "unknown")
            
            if source_type == "blog":
                url = payload.get("url", "")
                if url and url not in seen_urls:
                    sources.append({
                        "type": "blog",
                        "title": payload.get("title", ""),
                        "url": url,
                        "blog_name": payload.get("blog_name", "")
                    })
                    seen_urls.add(url)
            
            elif source_type == "foursquare_tip":
                sources.append({
                    "type": "local_tip",
                    "text": payload.get("text", "")[:150]
                })
        
        return sources

    async def get_poi_details(self, poi_id: str) -> Optional[Dict]:
        """
        Get full POI details from MongoDB
        
        Args:
            poi_id: MongoDB ObjectId of the POI
            
        Returns:
            Full POI document or None
        """
        try:
            from bson import ObjectId
            
            db = get_database()
            poi_doc = await db.pois.find_one({"_id": ObjectId(poi_id)})
            
            if not poi_doc:
                return None
            
            # Convert ObjectId to string for JSON serialization
            poi_doc["_id"] = str(poi_doc["_id"])
            
            return poi_doc
        
        except Exception as e:
            logger.error(f"❌ Error fetching POI {poi_id}: {e}")
            return None

    def _build_fallback_prompt(self, user_query: str, pois: List[Dict]) -> str:
        """Build a simpler prompt when strict filtering fails"""
        
        poi_list = "\n".join([
            f"{i+1}. **{poi.get('name')}** - {poi.get('category')} - {poi.get('tags', {}).get('cuisine', 'N/A')} cuisine"
            for i, poi in enumerate(pois)
        ])
        
        return f"""You are a helpful local guide. The user asked: "{user_query}"

    Here are nearby places:
    {poi_list}

    Recommend the top 3-5 places that best match the user's request. Use EXACT names from the list above.

    Return JSON:
    {{
    "recommendations": [
        {{
        "poi_name": "EXACT name from list",
        "reason": "Why this matches",
        "highlights": ["feature 1", "feature 2"],
        "best_for": "Use case"
        }}
    ]
    }}"""

    async def _extract_preferences_from_query(self, query: str) -> Dict[str, Any]:
        """
        Extract preferences from natural language query using Gemini
        
        Examples:
        - "Mexican cuisine" → cuisines: ['Mexican']
        - "high budget" → budget: 'expensive'
        - "for a couple" → group_size: 2
        """
        try:
            client = self._get_client()
            
            extraction_prompt = f"""Extract dining preferences from this query. Return JSON.

    Query: "{query}"

    Extract:
    - cuisines: List of cuisine types mentioned (e.g., ["Chinese", "Mexican","Italian","Indian"])
    - categories: List of place types (e.g., ["restaurant", "cafe", "bar"])
    - budget: One of: "budget", "moderate", "expensive", "luxury" (or null)
    - group_size: Number of people (extract from "couple"=2, "group"=4-6, "solo"=1, or null)

    Return ONLY valid JSON:
    {{
    "cuisines": [],
    "categories": [],
    "budget": null,
    "group_size": null
    }}"""

            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=extraction_prompt,
                config={
                    "temperature": 0.3,
                    "response_mime_type": "application/json"
                }
            )
            
            extracted = json.loads(response.text.strip())
            logger.info(f"  🧠 NLU extracted from query: {extracted}")
            return extracted
        
        except Exception as e:
            logger.error(f"❌ Failed to extract preferences: {e}")
            return {}
#Singleton instance
local_agent = LocalDiscoveryAgent()