"""
Unit tests for PlannerAgent
Tests AI-powered itinerary generation with mocked dependencies
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, date, time, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from langchain.schema import Document

from app.core.postgres import Base
from app.models.trip import Trip
from app.models.trip_day import TripDay
from app.models.activity import Activity
from app.ai.planner_agent import PlannerAgent, create_planner_agent
from app.services.weather_service import DailyWeather 


# Test database setup
@pytest.fixture
def test_db():
    """Create in-memory test database"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    
    yield db
    
    db.close()


@pytest.fixture
def sample_trip(test_db):
    """Create a sample trip for testing"""
    trip = Trip(
        title="Paris Adventure",
        origin="New York",
        destinations=["Paris"],
        start_date=datetime(2026, 3, 1),
        end_date=datetime(2026, 3, 3),
        budget=1500.0,
        budget_currency="USD",
        interests=["culture", "food"],
        preferences={"pace": "relaxed"},
        trip_type="solo",
        traveler_count=1,
        status="draft"
    )
    
    test_db.add(trip)
    test_db.commit()
    test_db.refresh(trip)
    
    return trip


@pytest.fixture
def planner_agent(test_db):
    """Create PlannerAgent with mocked Gemini client"""
    with patch('app.ai.planner_agent.genai.Client') as mock_client:
        agent = PlannerAgent(test_db)
        agent.client = Mock()
        agent.client.models = Mock()
        return agent


@pytest.fixture
def mock_weather_forecast():
    """Mock weather forecast response (WeatherForecast object)"""
    from app.services.weather_service import WeatherForecast, DailyWeather
    
    return WeatherForecast(
        city="Paris",
        latitude=48.8566,
        longitude=2.3522,
        daily_forecasts=[
            DailyWeather(
                date=date(2026, 3, 1),
                temp_max=15.0,
                temp_min=8.0,
                condition="Partly cloudy",
                condition_code=1,
                precipitation_probability=10.0,
                icon="⛅"
            ),
            DailyWeather(
                date=date(2026, 3, 2),
                temp_max=18.0,
                temp_min=10.0,
                condition="Clear sky",
                condition_code=0,
                precipitation_probability=5.0,
                icon="☀️"
            ),
            DailyWeather(
                date=date(2026, 3, 3),
                temp_max=12.0,
                temp_min=6.0,
                condition="Moderate rain",
                condition_code=63,
                precipitation_probability=80.0,
                icon="🌧️"
            )
        ],
        cached_at=datetime.now()
    )


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response with valid itinerary JSON"""
    return {
        "day_theme": "Cultural Immersion",
        "day_description": "Explore iconic Parisian landmarks and enjoy authentic French cuisine.",
        "activities": [
            {
                "title": "Visit the Louvre Museum",
                "description": "Explore world-famous art collections including the Mona Lisa",
                "category": "sightseeing",
                "start_time": "09:00",
                "duration_minutes": 180,
                "location": "Louvre Museum, Paris",
                "estimated_cost": 17.0,
                "reasoning": "Perfect morning activity, avoid crowds by arriving early"
            },
            {
                "title": "Lunch at Le Comptoir du Relais",
                "description": "Traditional French bistro with excellent prix fixe menu",
                "category": "dining",
                "start_time": "12:30",
                "duration_minutes": 90,
                "location": "Le Comptoir du Relais, Saint-Germain",
                "estimated_cost": 35.0,
                "reasoning": "Highly rated local restaurant, authentic French cuisine"
            },
            {
                "title": "Eiffel Tower Visit",
                "description": "Iconic landmark with stunning city views",
                "category": "sightseeing",
                "start_time": "15:00",
                "duration_minutes": 120,
                "location": "Eiffel Tower, Champ de Mars",
                "estimated_cost": 26.0,
                "reasoning": "Weather is good for outdoor activities, less crowded in afternoon"
            }
        ]
    }


# ==================== BASIC FUNCTIONALITY TESTS ====================

def test_planner_agent_initialization(test_db):
    """Test PlannerAgent initializes correctly"""
    with patch('app.ai.planner_agent.genai.Client'):
        agent = PlannerAgent(test_db)
        
        assert agent.db == test_db
        assert agent.model_name == "gemini-2.0-flash-exp"
        assert agent.config.temperature == 0.7
        assert agent.config.max_output_tokens == 2048


def test_calculate_daily_budget(planner_agent, sample_trip):
    """Test daily budget calculation"""
    # 3 days trip, $1500 budget, 70% for activities = $1050
    # $1050 / 3 = $350/day
    daily_budget = planner_agent._calculate_daily_budget(sample_trip)
    assert daily_budget == 350.0


def test_calculate_daily_budget_no_budget(planner_agent, sample_trip):
    """Test daily budget with no budget set"""
    sample_trip.budget = None
    daily_budget = planner_agent._calculate_daily_budget(sample_trip)
    assert daily_budget == 100.0  # Default


def test_parse_gemini_response_valid_json(planner_agent):
    """Test parsing valid JSON from Gemini"""
    json_response = '{"day_theme": "Test", "activities": []}'
    result = planner_agent._parse_gemini_response(json_response)
    
    assert result is not None
    assert result["day_theme"] == "Test"
    assert result["activities"] == []


def test_parse_gemini_response_with_markdown(planner_agent):
    """Test parsing JSON wrapped in markdown code blocks"""
    markdown_response = '''```json
    {"day_theme": "Test", "activities": []}
    ```'''
    
    result = planner_agent._parse_gemini_response(markdown_response)
    
    assert result is not None
    assert result["day_theme"] == "Test"


def test_parse_gemini_response_invalid_json(planner_agent):
    """Test handling of invalid JSON"""
    invalid_response = "This is not valid JSON"
    result = planner_agent._parse_gemini_response(invalid_response)
    
    assert result is None


def test_create_activity_from_data(planner_agent):
    """Test creating Activity object from parsed data"""
    activity_data = {
        "title": "Visit Museum",
        "description": "Explore art collections",
        "category": "sightseeing",
        "start_time": "09:00",
        "duration_minutes": 120,
        "location": "Museum of Art",
        "estimated_cost": 15.0,
        "reasoning": "Morning is best time"
    }
    
    activity = planner_agent._create_activity(
        trip_day_id=1,
        order=1,
        activity_data=activity_data
    )
    
    assert activity.title == "Visit Museum"
    assert activity.category == "sightseeing"
    assert activity.start_time == time(9, 0)
    assert activity.end_time == time(11, 0)  # 9:00 + 120min
    assert activity.duration_minutes == 120
    assert activity.estimated_cost == 15.0
    assert activity.order == 1


# ==================== WEATHER INTEGRATION TESTS ====================

def test_get_day_weather_with_forecast(planner_agent, mock_weather_forecast):
    """Test extracting weather for specific day from forecast"""
    target_date = date(2026, 3, 1)
    
    with patch('app.ai.planner_agent.weather_service.get_day_weather') as mock_get_day:
        mock_get_day.return_value = DailyWeather(
            date=target_date,
            temp_max=15.0,
            temp_min=8.0,
            condition="Partly Cloudy",
            condition_code=1,
            precipitation_probability=10.0,
            icon="⛅"
        )
        
        result = planner_agent._get_day_weather(mock_weather_forecast, target_date)
        
        assert result["temp_high"] == 15.0
        assert result["temp_low"] == 8.0
        assert result["condition"] == "Partly Cloudy"
        assert result["icon"] == "⛅"
        assert result["precipitation_prob"] == 10.0


def test_get_day_weather_without_forecast(planner_agent):
    """Test default weather when no forecast available"""
    result = planner_agent._get_day_weather(None, date(2026, 3, 1))
    
    assert result["temp_high"] == 20.0
    assert result["temp_low"] == 15.0
    assert result["condition"] == "Unknown"
    assert result["icon"] == "🌤️"


@pytest.mark.asyncio
async def test_fetch_weather_success(planner_agent, sample_trip, mock_weather_forecast):
    """Test successful weather fetch"""
    with patch('app.ai.planner_agent.weather_service.get_forecast', new_callable=AsyncMock) as mock_get_forecast:
        mock_get_forecast.return_value = mock_weather_forecast
        
        result = await planner_agent._fetch_weather(sample_trip)
        
        assert result == mock_weather_forecast
        mock_get_forecast.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_weather_failure(planner_agent, sample_trip):
    """Test weather fetch failure handling"""
    with patch('app.ai.planner_agent.weather_service.get_forecast', new_callable=AsyncMock) as mock_get_forecast:
        mock_get_forecast.side_effect = Exception("API Error")
        
        result = await planner_agent._fetch_weather(sample_trip)
        
        assert result is None  # Should return None, not raise


# ==================== GUIDE CONTEXT TESTS ====================

@pytest.mark.asyncio
async def test_fetch_guide_context_success(planner_agent):
    """Test fetching guide context with retriever"""
    mock_docs = [
        Document(
            page_content="The Louvre is a must-visit museum...",
            metadata={"city": "Paris", "theme": "culture", "source_title": "Paris Guide"}
        ),
        Document(
            page_content="Try authentic croissants at local bakeries...",
            metadata={"city": "Paris", "theme": "food", "source_title": "Food Guide"}
        )
    ]
    
    mock_retriever = Mock()
    mock_retriever._get_relevant_documents = Mock(return_value=mock_docs)
    
    with patch('app.ai.planner_agent.create_travel_guide_retriever', return_value=mock_retriever):
        result = await planner_agent._fetch_guide_context("Paris", ["culture", "food"])
        
        assert "Louvre" in result
        assert "croissants" in result
        assert "Paris Guide" in result


@pytest.mark.asyncio
async def test_fetch_guide_context_maps_interests_to_themes(planner_agent):
    """Test interest to theme mapping"""
    with patch('app.ai.planner_agent.create_travel_guide_retriever') as mock_create:
        mock_retriever = Mock()
        mock_retriever._get_relevant_documents = Mock(return_value=[])
        mock_create.return_value = mock_retriever
        
        await planner_agent._fetch_guide_context("Paris", ["culture", "adventure", "food"])
        
        # Check that create_travel_guide_retriever was called with correct themes
        call_args = mock_create.call_args
        themes = call_args[1]['themes']
        
        assert "culture" in themes
        assert "food" in themes
        assert "attractions" in themes  # adventure maps to attractions


@pytest.mark.asyncio
async def test_fetch_guide_context_fallback(planner_agent):
    """Test fallback when retriever fails"""
    with patch('app.ai.planner_agent.create_travel_guide_retriever', side_effect=Exception("Connection error")):
        result = await planner_agent._fetch_guide_context("Paris", ["culture"])
        
        assert "general knowledge" in result.lower()
        assert "Paris" in result


# ==================== ITINERARY GENERATION TESTS ====================

@pytest.mark.asyncio
async def test_generate_day_plan_complete_flow(planner_agent, sample_trip, mock_weather_forecast, mock_gemini_response):
    """Test complete day plan generation flow"""
    target_date = date(2026, 3, 1)
    
    # Mock weather
    mock_day_weather = DailyWeather(
        date=target_date,
        temp_max=15.0,
        temp_min=8.0,
        condition="Partly Cloudy",
        condition_code=1,
        precipitation_probability=10.0,
        icon="⛅"
    )
    
    # Mock guide context
    mock_docs = [Document(page_content="Great museums in Paris", metadata={})]
    mock_retriever = Mock()
    mock_retriever._get_relevant_documents = Mock(return_value=mock_docs)
    
    # Mock Gemini response
    mock_response = Mock()
    import json
    mock_response.text = json.dumps(mock_gemini_response)
    
    with patch('app.ai.planner_agent.weather_service.get_day_weather', return_value=mock_day_weather), \
         patch('app.ai.planner_agent.create_travel_guide_retriever', return_value=mock_retriever), \
         patch.object(planner_agent.client.models, 'generate_content', return_value=mock_response):
        
        day = await planner_agent._generate_day_plan(
            trip=sample_trip,
            day_number=1,
            date=target_date,
            city="Paris",
            weather_forecast=mock_weather_forecast,
            budget_per_day=350.0
        )
        
        # Verify TripDay was created
        assert day is not None
        assert day.day_number == 1
        assert day.city == "Paris"
        assert day.theme == "Cultural Immersion"
        assert day.weather_temp_high == 15.0
        
        # Verify activities were created
        activities = planner_agent.db.query(Activity).filter(Activity.trip_day_id == day.id).all()
        assert len(activities) == 3
        assert activities[0].title == "Visit the Louvre Museum"
        assert activities[1].category == "dining"


@pytest.mark.asyncio
async def test_generate_itinerary_single_day(planner_agent, sample_trip, mock_weather_forecast, mock_gemini_response):
    """Test generating itinerary for single-day trip"""
    # Make it a 1-day trip
    sample_trip.end_date = sample_trip.start_date
    
    mock_response = Mock()
    import json
    mock_response.text = json.dumps(mock_gemini_response)
    
    mock_day_weather = DailyWeather(
        date=date(2026, 3, 1),
        temp_max=15.0,
        temp_min=8.0,
        condition="Clear",
        condition_code=0,
        precipitation_probability=5.0,
        icon="☀️"
    )
    
    with patch('app.ai.planner_agent.weather_service.get_forecast', new_callable=AsyncMock, return_value=mock_weather_forecast), \
         patch('app.ai.planner_agent.weather_service.get_day_weather', return_value=mock_day_weather), \
         patch('app.ai.planner_agent.create_travel_guide_retriever'), \
         patch.object(planner_agent.client.models, 'generate_content', return_value=mock_response):
        
        trip = await planner_agent.generate_itinerary(sample_trip.id)
        
        assert trip.status == "planned"
        days = planner_agent.db.query(TripDay).filter(TripDay.trip_id == trip.id).all()
        assert len(days) == 1


@pytest.mark.asyncio
async def test_generate_itinerary_rainy_weather(planner_agent, sample_trip, mock_weather_forecast):
    """Test itinerary adjusts for rainy weather"""
    rainy_response = {
        "day_theme": "Indoor Adventures",
        "day_description": "Explore museums and cafes due to rainy weather.",
        "activities": [
            {
                "title": "Louvre Museum",
                "description": "Indoor art exploration",
                "category": "sightseeing",
                "start_time": "10:00",
                "duration_minutes": 180,
                "location": "Louvre",
                "estimated_cost": 17.0,
                "reasoning": "Perfect indoor activity for rainy day"
            }
        ]
    }
    
    sample_trip.end_date = sample_trip.start_date
    
    mock_response = Mock()
    import json
    mock_response.text = json.dumps(rainy_response)
    
    mock_day_weather = DailyWeather(
        date=date(2026, 3, 1),
        temp_max=12.0,
        temp_min=6.0,
        condition="Rainy",
        condition_code=61,
        precipitation_probability=80.0,
        icon="🌧️"
    )
    
    with patch('app.ai.planner_agent.weather_service.get_forecast', new_callable=AsyncMock, return_value=mock_weather_forecast), \
         patch('app.ai.planner_agent.weather_service.get_day_weather', return_value=mock_day_weather), \
         patch('app.ai.planner_agent.create_travel_guide_retriever'), \
         patch.object(planner_agent.client.models, 'generate_content', return_value=mock_response):
        
        trip = await planner_agent.generate_itinerary(sample_trip.id)
        
        day = planner_agent.db.query(TripDay).filter(TripDay.trip_id == trip.id).first()
        assert day.weather_precipitation_prob == 80.0
        assert day.theme == "Indoor Adventures"


# ==================== EDGE CASE TESTS ====================

@pytest.mark.asyncio
async def test_trip_not_found(planner_agent):
    """Test handling of non-existent trip"""
    with pytest.raises(ValueError, match="Trip 9999 not found"):
        await planner_agent.generate_itinerary(9999)


@pytest.mark.asyncio
async def test_database_rollback_on_error(planner_agent, sample_trip):
    """Test database rollback when generation fails"""
    sample_trip.end_date = sample_trip.start_date
    
    # Mock Gemini to return invalid response causing parsing failure
    mock_response = Mock()
    mock_response.text = "INVALID JSON RESPONSE"
    
    mock_day_weather = DailyWeather(
        date=date(2026, 3, 1),
        temp_max=15.0,
        temp_min=8.0,
        condition="Clear",
        condition_code=0,
        precipitation_probability=5.0,
        icon="☀️"
    )
    
    with patch('app.ai.planner_agent.weather_service.get_forecast', new_callable=AsyncMock, return_value=None), \
         patch('app.ai.planner_agent.weather_service.get_day_weather', return_value=mock_day_weather), \
         patch('app.ai.planner_agent.create_travel_guide_retriever'), \
         patch.object(planner_agent.client.models, 'generate_content', return_value=mock_response):
        
        # Generate itinerary - will complete but with 0 days due to parse failures
        trip = await planner_agent.generate_itinerary(sample_trip.id)
        
        # Verify no days were created (because JSON parsing failed)
        days = planner_agent.db.query(TripDay).filter(TripDay.trip_id == trip.id).all()
        assert len(days) == 0
        
        # Trip status still gets updated to "planned" even with 0 days
        # This is current behavior - could be enhanced to check if days exist
        assert trip.status == "planned"


def test_factory_function(test_db):
    """Test create_planner_agent factory function"""
    with patch('app.ai.planner_agent.genai.Client'):
        agent = create_planner_agent(test_db)
        
        assert isinstance(agent, PlannerAgent)
        assert agent.db == test_db
