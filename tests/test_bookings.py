import pytest
from fastapi.testclient import TestClient
from main import app
from database import bookings_collection, users_collection
from auth.jwt_handler import create_access_token

client = TestClient(app)

@pytest.fixture
def test_user():
    """Create a test user in the database before running tests."""
    user = {
        "name": "Booking User",
        "email": "bookinguser@example.com",
        "password": "SecurePass@123",
        "is_verified": True
    }
    users_collection.insert_one(user)
    yield user
    users_collection.delete_one({"email": user["email"]})  # Cleanup after test

@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers for tests."""
    token = create_access_token(test_user["email"])
    return {"Authorization": f"Bearer {token}"}

def test_create_booking(auth_headers):
    response = client.post("/api/bookings", json={
        "email": "bookinguser@example.com",
        "name": "John Doe",
        "phone": "9876543210",
        "address": "123 Main Street",
        "serviceName": "Plumbing",
        "providerName": "ABC Plumbers",
        "remarks": "Fix leaking pipe"
    }, headers=auth_headers)

    assert response.status_code == 200
    assert "Booking confirmed" in response.json()["message"]

def test_create_booking_unauthorized():
    response = client.post("/api/bookings", json={
        "email": "unauth@example.com",
        "name": "Jane Doe",
        "phone": "9876543210",
        "address": "456 Market Street",
        "serviceName": "Cleaning",
        "providerName": "XYZ Cleaners",
        "remarks": "Deep cleaning"
    })
    assert response.status_code == 401
    assert "Authorization token missing" in response.json()["detail"]

def test_get_user_bookings(auth_headers):
    response = client.get("/api/bookings", headers=auth_headers)
    assert response.status_code in [200, 404]  # If no bookings exist, it should return 404
