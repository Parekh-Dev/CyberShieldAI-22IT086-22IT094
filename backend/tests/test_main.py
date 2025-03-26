from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)

def test_home_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to CyberShield AI"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_analyze_endpoint_normal_text():
    response = client.post(
        "/analyze",
        json={"text": "This is a normal friendly message"}
    )
    assert response.status_code == 200
    assert "isHateSpeech" in response.json()
    assert response.json()["isHateSpeech"] == False

def test_analyze_endpoint_hate_speech():
    response = client.post(
        "/analyze",
        json={"text": "I hate everyone"}
    )
    assert response.status_code == 200
    assert "isHateSpeech" in response.json()
    assert response.json()["isHateSpeech"] == True

def test_analyze_endpoint_invalid_request():
    response = client.post(
        "/analyze",
        json={}
    )
    assert response.status_code == 422  # FastAPI validation error

if __name__ == "__main__":
    pytest.main(["-v"])