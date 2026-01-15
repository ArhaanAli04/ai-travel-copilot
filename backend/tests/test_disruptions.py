"""
Unit tests for disruption API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.main import app
from app.models.disruption import DisruptionCase, DisruptionOption, DisruptionType, OptionType


client = TestClient(app)


# ===== Test Data =====

def create_test_case_data():
    """Create test disruption case data"""
    return {
        "flight_number": "AA123",
        "airline": "American Airlines",
        "origin": "New York (JFK)",
        "destination": "London (LHR)",
        "disruption_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "pnr": "ABC123",
        "notes": "Flight cancelled due to weather"
    }


# ===== CRUD Tests =====

def test_create_disruption_case():
    """Test creating a disruption case"""
    case_data = create_test_case_data()
    
    response = client.post("/api/disruptions/", json=case_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["flight_number"] == "AA123"
    assert data["airline"] == "American Airlines"
    assert data["disruption_type"] == "cancellation"  # Detected from notes
    assert "id" in data
    assert "created_at" in data


def test_get_disruption_case():
    """Test getting a disruption case"""
    # Create a case first
    case_data = create_test_case_data()
    create_response = client.post("/api/disruptions/", json=case_data)
    case_id = create_response.json()["id"]
    
    # Get the case
    response = client.get(f"/api/disruptions/{case_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == case_id
    assert data["flight_number"] == "AA123"
    assert "options" in data  # Should include options array


def test_get_nonexistent_case():
    """Test getting a non-existent case"""
    response = client.get("/api/disruptions/99999")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_disruption_cases():
    """Test listing disruption cases"""
    # Create a few cases
    for i in range(3):
        case_data = create_test_case_data()
        case_data["flight_number"] = f"AA{100 + i}"
        client.post("/api/disruptions/", json=case_data)
    
    # List cases
    response = client.get("/api/disruptions/")
    
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "cases" in data
    assert data["total"] >= 3
    assert len(data["cases"]) >= 3


def test_update_disruption_case():
    """Test updating a disruption case"""
    # Create a case
    case_data = create_test_case_data()
    create_response = client.post("/api/disruptions/", json=case_data)
    case_id = create_response.json()["id"]
    
    # Update the case
    update_data = {
        "current_status": "Delayed by 3 hours",
        "severity": "medium",
        "notes": "Updated notes"
    }
    response = client.put(f"/api/disruptions/{case_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["current_status"] == "Delayed by 3 hours"
    assert data["severity"] == "medium"
    assert data["notes"] == "Updated notes"


def test_delete_disruption_case():
    """Test soft deleting a disruption case"""
    # Create a case
    case_data = create_test_case_data()
    create_response = client.post("/api/disruptions/", json=case_data)
    case_id = create_response.json()["id"]
    
    # Delete the case
    response = client.delete(f"/api/disruptions/{case_id}")
    
    assert response.status_code == 204
    
    # Verify case is soft deleted (can't be retrieved)
    get_response = client.get(f"/api/disruptions/{case_id}")
    assert get_response.status_code == 404


# ===== Option Tests =====

def test_create_disruption_option():
    """Test creating an option for a case"""
    # Create a case first
    case_data = create_test_case_data()
    create_response = client.post("/api/disruptions/", json=case_data)
    case_id = create_response.json()["id"]
    
    # Create an option
    option_data = {
        "disruption_case_id": case_id,
        "option_type": "alternative_flight",
        "title": "Alternative Flight UA456",
        "description": "Departs 3 hours later",
        "estimated_cost": 0.0,
        "priority_rank": 8,
        "ai_reasoning": "Best available option with no extra cost"
    }
    response = client.post(f"/api/disruptions/{case_id}/options", json=option_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Alternative Flight UA456"
    assert data["option_type"] == "alternative_flight"
    assert data["priority_rank"] == 8


def test_list_disruption_options():
    """Test listing options for a case"""
    # Create a case
    case_data = create_test_case_data()
    create_response = client.post("/api/disruptions/", json=case_data)
    case_id = create_response.json()["id"]
    
    # Create multiple options
    for i in range(3):
        option_data = {
            "disruption_case_id": case_id,
            "option_type": "alternative_flight",
            "title": f"Option {i+1}",
            "priority_rank": i + 5
        }
        client.post(f"/api/disruptions/{case_id}/options", json=option_data)
    
    # List options
    response = client.get(f"/api/disruptions/{case_id}/options")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    # Should be ordered by priority_rank descending
    assert data[0]["priority_rank"] >= data[1]["priority_rank"]


# ===== Disruption Type Detection Tests =====

def test_disruption_type_detection_cancellation():
    """Test auto-detection of cancellation"""
    case_data = create_test_case_data()
    case_data["notes"] = "Flight was cancelled by the airline"
    
    response = client.post("/api/disruptions/", json=case_data)
    
    assert response.status_code == 201
    assert response.json()["disruption_type"] == "cancellation"


def test_disruption_type_detection_weather():
    """Test auto-detection of weather disruption"""
    case_data = create_test_case_data()
    case_data["notes"] = "Delayed due to bad weather conditions"
    
    response = client.post("/api/disruptions/", json=case_data)
    
    assert response.status_code == 201
    assert response.json()["disruption_type"] == "weather"


def test_disruption_type_detection_delay():
    """Test auto-detection of delay"""
    case_data = create_test_case_data()
    case_data["notes"] = "Flight is delayed by 2 hours"
    
    response = client.post("/api/disruptions/", json=case_data)
    
    assert response.status_code == 201
    assert response.json()["disruption_type"] == "delay"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
