from __future__ import annotations


def test_health_version_status_are_open(api_get) -> None:
    for endpoint in ["/health", "/version", "/status"]:
        response = api_get(endpoint, auth=False)
        payload = response.json()

        assert response.status_code == 200
        assert payload["status"] == "success"
        assert "timestamp" in payload


def test_status_reports_artifact_directories(api_get) -> None:
    response = api_get("/status", auth=False)
    payload = response.json()

    assert response.status_code == 200
    assert payload["data"]["processed"] is True
    assert payload["data"]["reports"] is True
    assert payload["data"]["models"] is True

