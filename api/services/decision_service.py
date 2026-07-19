from __future__ import annotations

from typing import Any

from api.utils.cache import apply_filters, count_values, frame_payload, numeric_mean, numeric_sum, read_dataset, sort_frame, unique_count


class DecisionService:
    def get_decisions(
        self,
        *,
        limit: int,
        offset: int,
        domain: str | None = None,
        decision_type: str | None = None,
        priority_band: str | None = None,
        risk_level: str | None = None,
        time_sensitivity: str | None = None,
    ) -> dict[str, Any]:
        frame, spec = read_dataset("business_decisions")
        filters = {
            "Domain": domain,
            "DecisionType": decision_type,
            "PriorityBand": priority_band,
            "RiskLevel": risk_level,
            "TimeSensitivity": time_sensitivity,
        }
        frame = apply_filters(frame, filters)
        frame = sort_frame(frame, ["PriorityScore", "FinancialImpact"], ascending=False)
        summary = self._decision_summary(frame)
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)

    def get_alerts(self, *, limit: int, offset: int, severity: str | None = None, domain: str | None = None) -> dict[str, Any]:
        frame, spec = read_dataset("business_alerts")
        filters = {"Severity": severity, "Domain": domain}
        frame = apply_filters(frame, filters)
        frame = sort_frame(frame, ["PriorityScore", "FinancialImpact"], ascending=False)
        summary = {
            "alerts": int(len(frame)),
            "critical_or_high": count_values(frame, "Severity", {"critical", "high"}),
            "financial_impact": numeric_sum(frame, "FinancialImpact"),
        }
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)

    def get_scenarios(self, *, limit: int, offset: int, risk_level: str | None = None) -> dict[str, Any]:
        frame, spec = read_dataset("scenario_analysis")
        filters = {"RiskLevel": risk_level}
        frame = apply_filters(frame, filters)
        frame = sort_frame(frame, ["RiskScore"], ascending=False)
        summary = {
            "scenarios": int(len(frame)),
            "worst_profit_impact": numeric_mean(frame.tail(1), "ProfitImpact") if "ProfitImpact" in frame else None,
            "average_risk_score": numeric_mean(frame, "RiskScore"),
        }
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)

    def get_recommendations(
        self,
        *,
        limit: int,
        offset: int,
        domain: str | None = None,
        time_sensitivity: str | None = None,
    ) -> dict[str, Any]:
        frame, spec = read_dataset("priority_actions")
        filters = {"Domain": domain, "TimeSensitivity": time_sensitivity}
        frame = apply_filters(frame, filters)
        frame = sort_frame(frame, ["PriorityScore", "ExpectedROI"], ascending=False)
        summary = self._decision_summary(frame)
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)

    def get_executive(self, *, limit: int, offset: int, priority: str | None = None) -> dict[str, Any]:
        frame, spec = read_dataset("executive_summary")
        filters = {"Priority": priority}
        frame = apply_filters(frame, filters)
        summary = {"summary_items": int(len(frame)), "owners": unique_count(frame, "Owner")}
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)

    @staticmethod
    def _decision_summary(frame) -> dict[str, Any]:
        return {
            "decisions": int(len(frame)),
            "domains": unique_count(frame, "Domain"),
            "p0_p1_actions": count_values(frame, "PriorityBand", {"p0", "p1"}),
            "financial_impact": numeric_sum(frame, "FinancialImpact"),
            "average_confidence": numeric_mean(frame, "Confidence"),
            "average_priority_score": numeric_mean(frame, "PriorityScore"),
        }


decision_service = DecisionService()

