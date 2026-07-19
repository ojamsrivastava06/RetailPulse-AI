from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from api.core.config import get_settings
from api.utils.cache import (
    count_values,
    dataframe_to_records,
    dataset_specs,
    list_files,
    numeric_mean,
    numeric_sum,
    read_csv_artifact,
    read_dataset,
    source_metadata,
    unique_count,
)


class AnalyticsService:
    def overview(self) -> dict[str, Any]:
        sales, sales_spec = read_dataset("sales")
        forecast, forecast_spec = read_dataset("future_predictions")
        inventory, inventory_spec = read_dataset("inventory_risk")
        churn, churn_spec = read_dataset("customer_probability_scores")
        decisions, decisions_spec = read_dataset("business_decisions")
        data = {
            "sales": {
                "transactions": int(len(sales)),
                "customers": unique_count(sales, "CustomerID"),
                "revenue": numeric_sum(sales, "Revenue") or numeric_sum(sales, "TotalSales"),
                "date_min": self._date_min(sales, "InvoiceDate"),
                "date_max": self._date_max(sales, "InvoiceDate"),
            },
            "forecast": {
                "forecast_revenue": numeric_sum(forecast, "ForecastRevenue"),
                "forecast_demand": numeric_sum(forecast, "ForecastDemand"),
                "horizons": sorted(pd.to_numeric(forecast.get("HorizonDays"), errors="coerce").dropna().astype(int).unique().tolist())
                if "HorizonDays" in forecast
                else [],
            },
            "inventory": {
                "items": unique_count(inventory, "SeriesKey"),
                "average_risk_score": numeric_mean(inventory, "InventoryRiskScore"),
                "potential_revenue_loss": numeric_sum(inventory, "PotentialRevenueLoss"),
            },
            "churn": {
                "customers": unique_count(churn, "CustomerID"),
                "average_churn_probability": numeric_mean(churn, "ChurnProbability"),
                "high_risk_customers": count_values(churn, "RiskCategory", {"critical", "high"}),
            },
            "decision_intelligence": {
                "decisions": int(len(decisions)),
                "financial_impact": numeric_sum(decisions, "FinancialImpact"),
                "average_confidence": numeric_mean(decisions, "Confidence"),
            },
        }
        metadata = {
            "sources": [
                source_metadata(sales_spec.path),
                source_metadata(forecast_spec.path),
                source_metadata(inventory_spec.path),
                source_metadata(churn_spec.path),
                source_metadata(decisions_spec.path),
            ]
        }
        return {"data": data, "metadata": metadata}

    def kpis(self) -> dict[str, Any]:
        overview = self.overview()["data"]
        kpis = [
            {"name": "Total Revenue", "value": overview["sales"]["revenue"], "domain": "Sales"},
            {"name": "Customers", "value": overview["sales"]["customers"], "domain": "Customer"},
            {"name": "Forecast Revenue", "value": overview["forecast"]["forecast_revenue"], "domain": "Forecast"},
            {"name": "Inventory Risk", "value": overview["inventory"]["average_risk_score"], "domain": "Inventory"},
            {"name": "Average Churn Probability", "value": overview["churn"]["average_churn_probability"], "domain": "Churn"},
            {"name": "Decision Financial Impact", "value": overview["decision_intelligence"]["financial_impact"], "domain": "Decision"},
        ]
        return {"data": kpis, "metadata": {"kpi_count": len(kpis)}}

    def summary(self) -> dict[str, Any]:
        settings = get_settings()
        specs = dataset_specs(settings)
        coverage = []
        for key, spec in specs.items():
            meta = source_metadata(spec.path)
            coverage.append({"dataset": key, **meta})
        reports = list_files(settings.reports_dir, (".md",))
        models = list_files(settings.models_dir, (".pkl", ".joblib"))
        figures = list_files(settings.figures_dir, (".png", ".jpg", ".jpeg", ".webp"))
        data = {
            "artifact_coverage": coverage,
            "counts": {
                "datasets": len(coverage),
                "available_datasets": sum(1 for item in coverage if item["exists"]),
                "reports": len(reports),
                "models": len(models),
                "figures": len(figures),
            },
        }
        return {"data": data, "metadata": {"project_root": str(settings.project_root)}}

    @staticmethod
    def _date_min(frame, column: str) -> str | None:
        if frame.empty or column not in frame.columns:
            return None
        value = pd.to_datetime(frame[column], errors="coerce").min()
        return None if pd.isna(value) else value.isoformat()

    @staticmethod
    def _date_max(frame, column: str) -> str | None:
        if frame.empty or column not in frame.columns:
            return None
        value = pd.to_datetime(frame[column], errors="coerce").max()
        return None if pd.isna(value) else value.isoformat()


class ReportService:
    ALLOWED_SUFFIXES = (".md", ".csv", ".png", ".jpg", ".jpeg", ".webp", ".pkl", ".joblib")

    def list_reports(self) -> dict[str, Any]:
        settings = get_settings()
        reports = list_files(settings.reports_dir, (".md",))
        figures = list_files(settings.figures_dir, (".png", ".jpg", ".jpeg", ".webp"))
        processed = list_files(settings.processed_output_dir, (".csv",))
        curated = list_files(settings.processed_data_dir, (".csv",))
        models = list_files(settings.models_dir, (".pkl", ".joblib"))
        data = {
            "reports": reports,
            "figures": figures,
            "processed": processed,
            "curated_datasets": curated,
            "models": models,
        }
        metadata = {
            "total_files": sum(len(group) for group in data.values()),
            "directories": {
                "reports": str(settings.reports_dir),
                "figures": str(settings.figures_dir),
                "processed": str(settings.processed_output_dir),
                "curated_datasets": str(settings.processed_data_dir),
                "models": str(settings.models_dir),
            },
        }
        return {"data": data, "metadata": metadata}

    def resolve_download(self, filename: str) -> Path:
        settings = get_settings()
        candidates = [
            settings.reports_dir / filename,
            settings.figures_dir / filename,
            settings.processed_output_dir / filename,
            settings.processed_data_dir / filename,
            settings.models_dir / filename,
        ]
        for path in candidates:
            if path.exists() and path.is_file() and path.suffix.lower() in self.ALLOWED_SUFFIXES:
                return path
        raise FileNotFoundError(filename)

    def preview_csv(self, filename: str, *, limit: int, offset: int) -> dict[str, Any]:
        path = self.resolve_download(filename)
        if path.suffix.lower() != ".csv":
            return {"data": {}, "metadata": source_metadata(path)}
        frame = read_csv_artifact(path)
        rows = frame.iloc[offset : offset + limit]
        return {
            "data": dataframe_to_records(rows),
            "metadata": {
                **source_metadata(path),
                "total_records": int(len(frame)),
                "returned_records": int(len(rows)),
                "limit": limit,
                "offset": offset,
            },
        }


analytics_service = AnalyticsService()
report_service = ReportService()

