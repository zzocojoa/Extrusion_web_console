from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "extrusion-web-console-api"
    assert body["version"] == "0.1.0"
    assert body["environment"] == "dev"
    assert body["localhost_only"] is True
    assert body["lan_security"] == {
        "enabled": False,
        "status": "localhost_only",
        "bind_host_class": "loopback",
        "cors_origin_classes": ["loopback_origin"],
        "shared_local_token_allowed": False,
        "reasons": [],
    }
    assert body["startup_id"].startswith("api_")
    assert body["started_at"]
    assert isinstance(body["process_id"], int)
