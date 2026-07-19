from __future__ import annotations


def test_decision_alerts_scenarios_and_recommendations(api_get) -> None:
    decisions = api_get("/decision?limit=3").json()
    alerts = api_get("/decision/alerts?limit=3").json()
    scenarios = api_get("/decision/scenarios?limit=3").json()
    recommendations = api_get("/decision/recommendations?limit=3").json()

    assert decisions["metadata"]["dataset"] == "business_decisions"
    assert alerts["metadata"]["dataset"] == "business_alerts"
    assert scenarios["metadata"]["dataset"] == "scenario_analysis"
    assert recommendations["metadata"]["dataset"] == "priority_actions"


def test_decision_executive_summary(api_get) -> None:
    executive = api_get("/decision/executive?limit=3").json()

    assert executive["metadata"]["dataset"] == "executive_summary"
    assert isinstance(executive["data"], list)

