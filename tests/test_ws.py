import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Signaling Server API" in response.json()["message"]


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_user():
    """Test user registration"""
    user_data = {"email": "test@example.com", "password": "testpassword"}
    response = client.post("/register", json=user_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["email"] == "test@example.com"


def test_register_duplicate_user():
    """Test registering duplicate user"""
    user_data = {"email": "test2@example.com", "password": "testpassword"}
    # First registration should succeed
    response1 = client.post("/register", json=user_data)
    assert response1.status_code == 200

    # Second registration should fail
    response2 = client.post("/register", json=user_data)
    assert response2.status_code == 400
    assert "already registered" in response2.json()["detail"]


def test_login_user():
    """Test user login"""
    # First register a user
    user_data = {"email": "test3@example.com", "password": "testpassword"}
    client.post("/register", json=user_data)

    # Then login
    login_data = {"email": "test3@example.com", "password": "testpassword"}
    response = client.post("/login", json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    login_data = {"email": "nonexistent@example.com", "password": "wrongpassword"}
    response = client.post("/login", json=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]
