from __future__ import annotations

from typing import Any

from api.utils.cache import apply_filters, frame_payload, numeric_mean, numeric_sum, read_dataset, sort_frame, unique_count


class CustomerService:
    def get_segments(
        self,
        *,
        limit: int,
        offset: int,
        customer_id: int | None = None,
        segment: str | None = None,
        tier: str | None = None,
    ) -> dict[str, Any]:
        frame, spec = read_dataset("customer_segments")
        filters = {"CustomerID": customer_id, "Segment": segment, "CustomerTier": tier}
        frame = apply_filters(frame, filters)
        frame = sort_frame(frame, ["PredictedCLV", "Monetary"], ascending=False)
        summary = {
            "customers": unique_count(frame, "CustomerID"),
            "segments": unique_count(frame, "Segment"),
            "average_clv": numeric_mean(frame, "PredictedCLV"),
            "total_revenue": numeric_sum(frame, "Revenue"),
        }
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)

    def get_rfm(self, *, limit: int, offset: int, customer_id: int | None = None, tier: str | None = None) -> dict[str, Any]:
        frame, spec = read_dataset("rfm_table")
        filters = {"CustomerID": customer_id, "CustomerTier": tier}
        frame = apply_filters(frame, filters)
        frame = sort_frame(frame, ["RFM_Score", "Monetary"], ascending=False)
        summary = {
            "customers": unique_count(frame, "CustomerID"),
            "average_recency": numeric_mean(frame, "Recency"),
            "average_frequency": numeric_mean(frame, "Frequency"),
            "average_monetary": numeric_mean(frame, "Monetary"),
        }
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)

    def get_clv(self, *, limit: int, offset: int, customer_id: int | None = None) -> dict[str, Any]:
        frame, spec = read_dataset("customer_segments")
        filters = {"CustomerID": customer_id}
        frame = apply_filters(frame, filters)
        frame = sort_frame(frame, ["PredictedCLV"], ascending=False)
        summary = {
            "customers": unique_count(frame, "CustomerID"),
            "average_clv": numeric_mean(frame, "PredictedCLV"),
            "total_predicted_clv": numeric_sum(frame, "PredictedCLV"),
            "average_margin": numeric_mean(frame, "CustomerMargin"),
        }
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)

    def get_health(
        self,
        *,
        limit: int,
        offset: int,
        customer_id: int | None = None,
        health_band: str | None = None,
        risk_category: str | None = None,
    ) -> dict[str, Any]:
        frame, spec = read_dataset("customer_health_scores")
        filters = {"CustomerID": customer_id, "HealthBand": health_band, "RiskCategory": risk_category}
        frame = apply_filters(frame, filters)
        frame = sort_frame(frame, ["CustomerHealthScore"], ascending=False)
        summary = {
            "customers": unique_count(frame, "CustomerID"),
            "average_health_score": numeric_mean(frame, "CustomerHealthScore"),
            "health_bands": unique_count(frame, "HealthBand"),
        }
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)


customer_service = CustomerService()

