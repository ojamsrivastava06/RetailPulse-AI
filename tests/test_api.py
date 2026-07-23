from __future__ import annotations


def assert_envelope(payload: dict) -> None:
    assert {"status", "message", "timestamp", "data", "metadata"}.issubset(payload)


def test_openapi_schema_includes_retailpulse_paths(api_get) -> None:
    response = api_get("/openapi.json", auth=False)

    assert response.status_code == 200
    payload = response.json()
    assert "/forecast/future" in payload["paths"]
    assert "/inventory/recommendations" in payload["paths"]
    assert "/decision/executive" in payload["paths"]


def test_business_endpoint_requires_authentication(api_get) -> None:
    response = api_get("/forecast?limit=1", auth=False)

    assert response.status_code == 401
    assert_envelope(response.json())


def test_all_required_json_endpoints_return_standard_envelope(api_get) -> None:
    endpoints = [
        "/health",
        "/version",
        "/status",
        "/forecast?limit=1",
        "/forecast/leaderboard?limit=1",
        "/forecast/metrics?limit=1",
        "/forecast/future?limit=1",
        "/inventory?limit=1",
        "/inventory/recommendations?limit=1",
        "/inventory/risk?limit=1",
        "/inventory/abc?limit=1",
        "/inventory/xyz?limit=1",
        "/customer/segments?limit=1",
        "/customer/rfm?limit=1",
        "/customer/clv?limit=1",
        "/customer/health?limit=1",
        "/churn?limit=1",
        "/churn/predictions?limit=1",
        "/churn/actions?limit=1",
        "/churn/probabilities?limit=1",
        "/decision?limit=1",
        "/decision/alerts?limit=1",
        "/decision/scenarios?limit=1",
        "/decision/recommendations?limit=1",
        "/decision/executive?limit=1",
        "/analytics/overview",
        "/analytics/kpis",
        "/analytics/summary",
        "/reports",
    ]

    for endpoint in endpoints:
        response = api_get(endpoint, auth=endpoint not in {"/health", "/version", "/status"})
        assert response.status_code == 200, endpoint
        payload = response.json()
        assert_envelope(payload)
        assert payload["status"] == "success"

