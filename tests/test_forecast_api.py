from __future__ import annotations


def test_forecast_future_returns_predictions(api_get) -> None:
    response = api_get("/forecast/future?limit=5&horizon_days=30")
    payload = response.json()

    assert response.status_code == 200
    assert payload["metadata"]["dataset"] == "future_predictions"
    assert payload["metadata"]["returned_records"] <= 5
    assert "forecast_revenue" in payload["metadata"]["summary"]


def test_forecast_leaderboard_returns_model_metrics(api_get) -> None:
    response = api_get("/forecast/leaderboard?limit=3")
    payload = response.json()

    assert response.status_code == 200
    assert payload["metadata"]["dataset"] == "leaderboard"
    assert payload["data"]
    assert "model_name" in payload["data"][0]

