from fastapi.testclient import TestClient

from backend.app.main import app


def test_dashboard_endpoint_returns_variant_d_mock_contract() -> None:
    client = TestClient(app)
    response = client.get("/api/dashboard")

    assert response.status_code == 200
    data = response.json()
    assert data["overall"]["state"] == "running"
    assert {item["id"] for item in data["statusMatrix"]} == {
        "upload",
        "supabase",
        "storage",
        "grafana",
        "state_store",
    }
    assert data["currentJob"]["status"] == "running"
    assert data["recentJobs"]
    assert data["warningQueue"]
