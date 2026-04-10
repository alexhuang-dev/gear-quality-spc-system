from fastapi.testclient import TestClient

from api.main import app


def test_dashboard_summary_endpoint():
    client = TestClient(app)
    response = client.get("/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "recent_runs" in data
    assert "status_counts" in data


def test_regression_endpoint():
    client = TestClient(app)
    response = client.post("/regression")
    assert response.status_code == 200
    data = response.json()
    assert "passed" in data
    assert "results" in data
