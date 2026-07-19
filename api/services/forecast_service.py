from __future__ import annotations

from typing import Any

import pandas as pd

from api.utils.cache import apply_filters, frame_payload, numeric_mean, numeric_sum, read_dataset, sort_frame, unique_count


class ForecastService:
    def get_forecast(
        self,
        *,
        limit: int,
        offset: int,
        product: str | None = None,
        country: str | None = None,
        category: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        frame, spec = read_dataset("forecast_results")
        filters = {"Product": product, "Country": country, "ProductCategory": category, "Model": model}
        frame = apply_filters(frame, filters)
        frame = sort_frame(frame, ["Date"], ascending=False)
        summary = {
            "series": unique_count(frame, "SeriesKey"),
            "models": unique_count(frame, "Model"),
            "actual_total": numeric_sum(frame, "Actual"),
            "forecast_total": numeric_sum(frame, "Forecast"),
            "average_residual": numeric_mean(frame, "Residual"),
        }
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)

    def get_leaderboard(self, *, limit: int, offset: int) -> dict[str, Any]:
        frame, spec = read_dataset("leaderboard")
        if not frame.empty and {"selection_eligible", "mape", "rmse"}.issubset(frame.columns):
            frame = frame.sort_values(["selection_eligible", "mape", "rmse"], ascending=[False, True, True])
        summary = {
            "models_compared": unique_count(frame, "model_name"),
            "best_mape": numeric_mean(frame.head(1), "mape"),
            "eligible_models": int(frame["selection_eligible"].fillna(False).sum()) if "selection_eligible" in frame else None,
        }
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, summary=summary)

    def get_metrics(
        self,
        *,
        limit: int,
        offset: int,
        model: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        frame, spec = read_dataset("forecast_metrics")
        filters = {"model_name": model, "status": status}
        frame = apply_filters(frame, filters)
        if not frame.empty and {"mape", "rmse"}.issubset(frame.columns):
            frame = frame.sort_values(["mape", "rmse"], ascending=[True, True])
        summary = {
            "evaluated_rows": int((frame["status"].astype(str).str.lower() == "evaluated").sum()) if "status" in frame else None,
            "average_mape": numeric_mean(frame, "mape"),
            "average_rmse": numeric_mean(frame, "rmse"),
        }
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)

    def get_future(
        self,
        *,
        limit: int,
        offset: int,
        product: str | None = None,
        country: str | None = None,
        category: str | None = None,
        model: str | None = None,
        horizon_days: int | None = None,
        forecast_level: str | None = None,
    ) -> dict[str, Any]:
        frame, spec = read_dataset("future_predictions")
        filters = {
            "Product": product,
            "Country": country,
            "ProductCategory": category,
            "Model": model,
            "HorizonDays": horizon_days,
            "ForecastLevel": forecast_level,
        }
        frame = apply_filters(frame, filters)
        frame = sort_frame(frame, ["Date"], ascending=True)
        summary = {
            "forecast_demand": numeric_sum(frame, "ForecastDemand"),
            "forecast_revenue": numeric_sum(frame, "ForecastRevenue"),
            "horizons": sorted(pd.to_numeric(frame["HorizonDays"], errors="coerce").dropna().astype(int).unique().tolist())
            if "HorizonDays" in frame
            else [],
            "forecast_levels": sorted(frame["ForecastLevel"].dropna().astype(str).unique().tolist())
            if "ForecastLevel" in frame
            else [],
        }
        return frame_payload(frame, spec=spec, limit=limit, offset=offset, filters=filters, summary=summary)


forecast_service = ForecastService()

