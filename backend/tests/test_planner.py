from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime

client = TestClient(app)


def test_create_trip():
    """Test creating a new trip"""
    trip_data = {
        "title": "Test Trip",
        "origin": "Mumbai",
        "destinations": ["Dubai", "Abu Dhabi"],
        "start_date": "2026-07-01T00:00:00",
        "end_date": "2026-07-05T00:00:00",
        "budget": 2000,
        "trip_type": "solo",
        "traveler_count": 1
    }
    
    response = client.post("/api/trips/", json=trip_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Trip"
    assert data["status"] == "draft"
    assert "id" in data
    
    return data["id"]


def test_list_trips():
    """Test listing all trips"""
    response = client.get("/api/trips/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_trip():
    """Test getting a specific trip"""
    trip_id = test_create_trip()
    response = client.get(f"/api/trips/{trip_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == trip_id
    assert data["days"] == []  # No days yet


def test_update_trip():
    """Test updating a trip"""
    trip_id = test_create_trip()
    update_data = {"budget": 2500, "notes": "Updated budget"}
    
    response = client.put(f"/api/trips/{trip_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["budget"] == 2500
    assert data["notes"] == "Updated budget"


def test_delete_trip():
    """Test deleting a trip"""
    trip_id = test_create_trip()
    response = client.delete(f"/api/trips/{trip_id}")
    assert response.status_code == 204
    
    # Verify deletion
    response = client.get(f"/api/trips/{trip_id}")
    assert response.status_code == 404
