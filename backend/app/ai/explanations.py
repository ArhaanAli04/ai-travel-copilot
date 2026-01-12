"""
Activity Explanations - Generate "Why this?" justifications
Uses Qdrant retrieval + Gemini to explain activity recommendations
WITH CACHING for better performance
"""
from typing import Optional
from sqlalchemy.orm import Session
import logging
import time
from google import genai
from google.genai import types

from app.core.config import settings
from app.models.activity import Activity
from app.core.qdrant import get_qdrant_client, get_collection_name

logger = logging.getLogger(__name__)


# Cache validity period (7 days in seconds)
CACHE_VALIDITY_SECONDS = 7 * 24 * 60 * 60


class ActivityExplainer:
    """
    Generate explanations for why activities were recommended
    WITH CACHING to improve performance and reduce API costs
    """
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-2.0-flash-lite"
        self.config = types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=300,  # Short explanations
        )
    
    async def explain_activity(
        self, 
        activity_id: int, 
        db: Session,
        force_refresh: bool = False
    ) -> dict:
        """
        Generate explanation for an activity (with caching)
        
        Args:
            activity_id: ID of the activity
            db: Database session
            force_refresh: Force regeneration even if cached
            
        Returns:
            Dict with explanation and source info
        """
        try:
            # Get activity from database
            activity = db.query(Activity).filter(Activity.id == activity_id).first()
            
            if not activity:
                raise ValueError(f"Activity {activity_id} not found")
            
            # ✅ Check if we have a valid cached explanation
            if not force_refresh and self._has_valid_cache(activity):
                logger.info(f"🎯 Using cached explanation for activity {activity_id}")
                return {
                    "explanation": activity.explanation_cache,
                    "sources": activity.source_refs.get("sources", []) if activity.source_refs else [],
                    "has_sources": bool(activity.source_refs),
                    "cached": True,
                    "generated_at": activity.explanation_generated_at
                }
            
            # No valid cache - generate new explanation
            logger.info(f"🔄 Generating new explanation for activity {activity_id}")
            
            # Get source references
            source_refs = activity.source_refs or {}
            sources = source_refs.get("sources", [])
            
            if not sources:
                # Fallback if no sources stored
                explanation = self._generate_fallback_explanation(activity)
                has_sources = False
            else:
                # Build context from sources
                context = self._build_context_from_sources(sources)
                
                # Generate explanation using Gemini
                explanation = await self._generate_explanation_with_llm(
                    activity=activity,
                    context=context
                )
                has_sources = True
            
            # ✅ Cache the explanation in database
            activity.explanation_cache = explanation
            activity.explanation_generated_at = int(time.time())
            db.commit()
            
            logger.info(f"✅ Cached explanation for activity {activity_id}")
            
            return {
                "explanation": explanation,
                "sources": sources,
                "has_sources": has_sources,
                "cached": False,
                "generated_at": activity.explanation_generated_at
            }
            
        except Exception as e:
            logger.error(f"❌ Explanation generation failed: {e}")
            raise
    
    def _has_valid_cache(self, activity: Activity) -> bool:
        """
        Check if activity has a valid cached explanation
        
        Args:
            activity: Activity object
            
        Returns:
            True if cache is valid, False otherwise
        """
        # Check if cache exists
        if not activity.explanation_cache:
            return False
        
        # Check if cache timestamp exists
        if not activity.explanation_generated_at:
            return False
        
        # Check if cache is still valid (not too old)
        current_time = int(time.time())
        cache_age = current_time - activity.explanation_generated_at
        
        if cache_age > CACHE_VALIDITY_SECONDS:
            logger.info(f"⏰ Cache expired for activity {activity.id} (age: {cache_age}s)")
            return False
        
        return True
    
    def _build_context_from_sources(self, sources: list) -> str:
        """Build context string from source references"""
        context_parts = []
        
        for idx, source in enumerate(sources, 1):
            snippet = source.get("content_snippet", "")
            title = source.get("source_title", "Travel Guide")
            
            context_parts.append(f"Source {idx} ({title}):\n{snippet}")
        
        return "\n\n".join(context_parts)
    
    async def _generate_explanation_with_llm(
        self,
        activity: Activity,
        context: str
    ) -> str:
        """
        Generate explanation using Gemini
        
        Args:
            activity: Activity object
            context: Context from guide sources
            
        Returns:
            2-4 sentence explanation
        """
        prompt = f"""Based on the travel guide information below, explain in 2-4 sentences why "{activity.title}" was recommended for this itinerary.

Activity Details:
- Title: {activity.title}
- Category: {activity.category}
- Location: {activity.location}
- Description: {activity.description}

Travel Guide Context:
{context}

Provide a concise explanation that:
1. Highlights why this activity fits the trip
2. Mentions any unique aspects or local insights
3. Is enthusiastic and helpful

Keep it to 2-4 sentences maximum."""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.config
            )
            
            explanation = response.text.strip()
            
            # Ensure it's not too long
            if len(explanation) > 500:
                explanation = explanation[:497] + "..."
            
            return explanation
            
        except Exception as e:
            logger.error(f"❌ LLM explanation failed: {e}")
            return self._generate_fallback_explanation(activity)
    
    def _generate_fallback_explanation(self, activity: Activity) -> str:
        """Generate simple explanation without LLM"""
        category_intros = {
            "sightseeing": "This landmark offers",
            "dining": "This restaurant provides",
            "entertainment": "This venue features",
            "culture": "This cultural site showcases",
            "shopping": "This location offers",
        }
        
        intro = category_intros.get(
            activity.category or "sightseeing",
            "This activity provides"
        )
        
        explanation = f"{intro} a great experience in {activity.location or 'the area'}."
        
        if activity.description:
            explanation += f" {activity.description[:150]}"
        
        if activity.ai_reasoning:
            explanation += f" {activity.ai_reasoning}"
        
        return explanation


# Singleton instance
_explainer_instance = None


def get_activity_explainer() -> ActivityExplainer:
    """Get or create ActivityExplainer singleton"""
    global _explainer_instance
    if _explainer_instance is None:
        _explainer_instance = ActivityExplainer()
    return _explainer_instance


async def explain_activity(
    activity_id: int, 
    db: Session,
    force_refresh: bool = False
) -> dict:
    """
    Convenience function to explain an activity (with caching)
    
    Args:
        activity_id: ID of the activity
        db: Database session
        force_refresh: Force regeneration even if cached
        
    Returns:
        Dict with explanation and source info
    """
    explainer = get_activity_explainer()
    return await explainer.explain_activity(activity_id, db, force_refresh)
