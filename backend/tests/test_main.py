from fastapi.testclient import TestClient
import pytest
from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.parametrize("url", ["/docs", "/redoc", "/openapi.json"])
def test_docs_url(url):
    response = client.get(url)
    assert response.status_code == 404
