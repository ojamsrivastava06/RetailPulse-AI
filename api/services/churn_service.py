from __future__ import annotations

from typing import Any

from api.utils.cache import apply_filters, count_values, frame_payload, numeric_mean, numeric_sum, read_dataset, sort_frame, unique_count


class ChurnService:
    def get_churn(
        self,
        *,
        limit: int,
        offset: int,
        customer_id: int | None = None,
        risk_category: str | None = None,
        health_band: str | None = None,
    ) -> dict[str, Any]:
        frame, spec = read_dataset("customer_churn_predictions")
        filters = {"CustomerID": customer_id, "RiskCategory": risk_category, "HealthBand": health_band}
        frame = apply_filters(frame, filters)
        frame = sort_frame(frame, ["ChurnProbability", "ExpectedLifetimeValue"], ascending=False)
        summary = self._summary(frame)
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)

    def get_predictions(
        self,
        *,
        limit: int,
        offset: int,
        customer_id: int | None = None,
        risk_category: str | None = None,
    ) -> dict[str, Any]:
        frame, spec = read_dataset("customer_churn_predictions")
        filters = {"CustomerID": customer_id, "RiskCategory": risk_category}
        frame = apply_filters(frame, filters)
        columns = [
            column
            for column in [
                "CustomerID",
                "ChurnProbability",
                "RetentionProbability",
                "PredictedChurn",
                "PredictedChurnLabel",
                "RiskCategory",
                "RiskScore",
                "ExpectedLifetimeValue",
                "RecommendedAction",
            ]
            if column in frame.columns
        ]
        frame = frame[columns] if columns else frame
        frame = sort_frame(frame, ["ChurnProbability"], ascending=False)
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=self._summary(frame))

    def get_actions(
        self,
        *,
        limit: int,
        offset: int,
        customer_id: int | None = None,
        risk_category: str | None = None,
        recommended_action: str | None = None,
    ) -> dict[str, Any]:
        frame, spec = read_dataset("customer_business_actions")
        filters = {"CustomerID": customer_id, "RiskCategory": risk_category, "RecommendedAction": recommended_action}
        frame = apply_filters(frame, filters)
        frame = sort_frame(frame, ["ChurnProbability", "ExpectedLifetimeValue"], ascending=False)
        summary = {
            "customers": unique_count(frame, "CustomerID"),
            "action_types": unique_count(frame, "RecommendedAction"),
            "value_at_stake": numeric_sum(frame, "ExpectedLifetimeValue"),
        }
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)

    def get_probabilities(
        self,
        *,
        limit: int,
        offset: int,
        customer_id: int | None = None,
        risk_category: str | None = None,
    ) -> dict[str, Any]:
        frame, spec = read_dataset("customer_probability_scores")
        filters = {"CustomerID": customer_id, "RiskCategory": risk_category}
        frame = apply_filters(frame, filters)
        frame = sort_frame(frame, ["ChurnProbability"], ascending=False)
        summary = {
            "customers": unique_count(frame, "CustomerID"),
            "average_churn_probability": numeric_mean(frame, "ChurnProbability"),
            "average_retention_probability": numeric_mean(frame, "RetentionProbability"),
            "high_risk_customers": count_values(frame, "RiskCategory", {"critical", "high"}),
        }
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)

    @staticmethod
    def _summary(frame) -> dict[str, Any]:
        return {
            "customers": unique_count(frame, "CustomerID"),
            "average_churn_probability": numeric_mean(frame, "ChurnProbability"),
            "average_retention_probability": numeric_mean(frame, "RetentionProbability"),
            "high_risk_customers": count_values(frame, "RiskCategory", {"critical", "high"}),
            "value_at_stake": numeric_sum(frame, "ExpectedLifetimeValue"),
        }


churn_service = ChurnService()

