from __future__ import annotations

from typing import Any

from api.utils.cache import (
    apply_filters,
    count_values,
    frame_payload,
    numeric_mean,
    numeric_sum,
    read_dataset,
    sort_frame,
    unique_count,
)


class InventoryService:
    def get_inventory(
        self,
        *,
        limit: int,
        offset: int,
        product: str | None = None,
        country: str | None = None,
        category: str | None = None,
        warehouse: str | None = None,
        risk_level: str | None = None,
        horizon_days: int | None = None,
    ) -> dict[str, Any]:
        frame, spec = read_dataset("inventory_dataset")
        filters = {
            "Product": product,
            "Country": country,
            "ProductCategory": category,
            "Warehouse": warehouse,
            "InventoryRiskLevel": risk_level,
            "HorizonDays": horizon_days,
        }
        frame = apply_filters(frame, filters)
        frame = sort_frame(frame, ["InventoryRiskScore"], ascending=False)
        summary = {
            "sku_count": unique_count(frame, "SeriesKey"),
            "warehouse_count": unique_count(frame, "Warehouse"),
            "inventory_cost": numeric_sum(frame, "TotalInventoryCost"),
            "inventory_savings": numeric_sum(frame, "InventorySavings"),
            "average_risk_score": numeric_mean(frame, "InventoryRiskScore"),
        }
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)

    def get_recommendations(self, *, limit: int, offset: int, priority: str | None = None) -> dict[str, Any]:
        frame, spec = read_dataset("inventory_recommendations")
        filters = {"Priority": priority}
        frame = apply_filters(frame, filters)
        frame = sort_frame(frame, ["Priority", "TriggerValue"], ascending=False)
        summary = {
            "recommendation_count": int(len(frame)),
            "products": unique_count(frame, "Product"),
            "total_suggested_quantity": numeric_sum(frame, "SuggestedQuantity"),
        }
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)

    def get_risk(self, *, limit: int, offset: int, risk_level: str | None = None) -> dict[str, Any]:
        frame, spec = read_dataset("inventory_risk")
        filters = {"InventoryRiskLevel": risk_level}
        frame = apply_filters(frame, filters)
        frame = sort_frame(frame, ["InventoryRiskScore"], ascending=False)
        summary = {
            "high_risk_items": count_values(frame, "InventoryRiskLevel", {"high", "critical"}),
            "average_health_score": numeric_mean(frame, "InventoryHealthScore"),
            "potential_revenue_loss": numeric_sum(frame, "PotentialRevenueLoss"),
        }
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)

    def get_abc(self, *, limit: int, offset: int, abc_class: str | None = None) -> dict[str, Any]:
        frame, spec = read_dataset("abc_analysis")
        filters = {"ABCClass": abc_class}
        frame = apply_filters(frame, filters)
        frame = sort_frame(frame, ["TotalRevenue"], ascending=False)
        summary = {"total_revenue": numeric_sum(frame, "TotalRevenue"), "classes": unique_count(frame, "ABCClass")}
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)

    def get_xyz(self, *, limit: int, offset: int, xyz_class: str | None = None) -> dict[str, Any]:
        frame, spec = read_dataset("xyz_analysis")
        filters = {"XYZClass": xyz_class}
        frame = apply_filters(frame, filters)
        frame = sort_frame(frame, ["DemandCV"], ascending=False)
        summary = {
            "average_demand_cv": numeric_mean(frame, "DemandCV"),
            "classes": unique_count(frame, "XYZClass"),
        }
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)


inventory_service = InventoryService()

