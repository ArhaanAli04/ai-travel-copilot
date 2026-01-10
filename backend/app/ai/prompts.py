"""
AI Prompts for PlannerAgent
Structured prompts for Gemini itinerary generation
"""
from typing import List, Dict
from datetime import date


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
