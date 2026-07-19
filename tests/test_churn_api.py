from __future__ import annotations


def test_churn_predictions_probabilities_and_actions(api_get) -> None:
    predictions = api_get("/churn/predictions?limit=3").json()
    probabilities = api_get("/churn/probabilities?limit=3").json()
    actions = api_get("/churn/actions?limit=3").json()

    assert predictions["metadata"]["dataset"] == "customer_churn_predictions"
    assert probabilities["metadata"]["dataset"] == "customer_probability_scores"
    assert actions["metadata"]["dataset"] == "customer_business_actions"
    assert "average_churn_probability" in probabilities["metadata"]["summary"]

