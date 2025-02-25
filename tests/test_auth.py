import pytest
from fastapi.testclient import TestClient
from main import app
from database import users_collection
from passlib.context import CryptContext

client = TestClient(app)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@pytest.fixture
def test_user():
    """Create a test user in the database before running tests."""
    user = {
        "name": "Test User",
        "email": "testuser@example.com",
        "password": pwd_context.hash("Test@123"),
        "is_verified": True
    }
    users_collection.insert_one(user)
    yield user
    users_collection.delete_one({"email": user["email"]})  # Cleanup after test

def test_signup():
    response = client.post("/api/auth/signup", json={
        "name": "New User",
        "email": "newuser@example.com",
        "password": "SecurePass@123"
    })
    assert response.status_code == 200
    assert "Signup successful" in response.json()["message"]

def test_login(test_user):
    response = client.post("/api/auth/login", json={
        "email": test_user["email"],
        "password": "Test@123"
    })
    assert response.status_code == 200
    assert "token" in response.json()

def test_login_unverified_user():
    response = client.post("/api/auth/login", json={
        "email": "unverified@example.com",
        "password": "Unverified@123"
    })
    assert response.status_code == 403
    assert "Email not verified" in response.json()["detail"]

def test_invalid_login():
    response = client.post("/api/auth/login", json={
        "email": "wrong@example.com",
        "password": "WrongPass"
    })
    assert response.status_code == 400
    assert "User not found" in response.json()["detail"]

def test_verify_email():
    response = client.post("/api/auth/verify-email", json={
        "email": "testuser@example.com",
        "otp": "123456"  # Assume the correct OTP
    })
    assert response.status_code == 200
    assert "Email verified successfully" in response.json()["message"]
