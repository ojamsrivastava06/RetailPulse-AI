from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from inventory_optimization import (  # noqa: E402
    build_inventory_history,
    compute_abc_xyz,
    create_inventory_recommendations,
    enrich_with_model_predictions,
    simulate_inventory_dataset,
    summarize_inventory_metrics,
    summarize_inventory_risk,
    train_inventory_risk_models,
    write_inventory_notebook,
)


def make_raw_inventory_df(days: int = 180) -> pd.DataFrame:
    start = pd.Timestamp("2024-01-01")
    rows: list[dict[str, object]] = []
    series_specs = [
        ("ALPHA LAMP", "United Kingdom", "Lighting", 10.0, 4.0),
        ("BETA FRAME", "France", "Decor", 6.0, 5.0),
    ]
    for day_offset in range(days):
        for idx, (description, country, category, base_qty, unit_price) in enumerate(series_specs, start=1):
            invoice_date = start + pd.Timedelta(days=day_offset)
            quantity = base_qty + (day_offset % (idx + 4))
            rows.append(
                {
                    "InvoiceDate": invoice_date,
                    "Description": description,
                    "Country": country,
                    "ProductCategory": category,
                    "Quantity": quantity,
                    "Revenue": quantity * unit_price,
                    "InvoiceNo": f"{idx}-{day_offset}",
                    "CustomerID": 1000 + ((day_offset + idx) % 20),
                }
            )
    return pd.DataFrame(rows)


def make_forecast_df() -> pd.DataFrame:
    base_date = pd.Timestamp("2024-07-01")
    rows: list[dict[str, object]] = []
    for horizon in (30, 60):
        for day_offset in range(horizon):
            current_date = base_date + pd.Timedelta(days=day_offset)
            rows.append(
                {
                    "Date": current_date,
                    "ForecastDemand": 18.0 + (day_offset % 5),
                    "ForecastRevenue": (18.0 + (day_offset % 5)) * 4.0,
                    "Lower95Demand": 15.0,
                    "Upper95Demand": 28.0,
                    "SeriesKey": "ALPHA LAMP | United Kingdom | Lighting",
                    "Product": "ALPHA LAMP",
                    "Country": "United Kingdom",
                    "ProductCategory": "Lighting",
                    "Model": "Holt-Winters",
                    "Configuration": "default",
                    "Entity": "ALPHA LAMP",
                    "ForecastLevel": "SKU",
                    "HorizonDays": horizon,
                }
            )
            rows.append(
                {
                    "Date": current_date,
                    "ForecastDemand": 9.0 + ((day_offset + 2) % 4),
                    "ForecastRevenue": (9.0 + ((day_offset + 2) % 4)) * 5.0,
                    "Lower95Demand": 7.0,
                    "Upper95Demand": 16.0,
                    "SeriesKey": "BETA FRAME | France | Decor",
                    "Product": "BETA FRAME",
                    "Country": "France",
                    "ProductCategory": "Decor",
                    "Model": "Holt-Winters",
                    "Configuration": "default",
                    "Entity": "BETA FRAME",
                    "ForecastLevel": "SKU",
                    "HorizonDays": horizon,
                }
            )
    return pd.DataFrame(rows)


def test_inventory_dataset_contains_required_planning_fields() -> None:
    raw_df = make_raw_inventory_df()
    forecast_df = make_forecast_df()

    history = build_inventory_history(raw_df, forecast_df)
    summary, abc_analysis, xyz_analysis, abc_xyz = compute_abc_xyz(history)
    inventory_dataset = simulate_inventory_dataset(summary, forecast_df)

    assert not history.empty
    assert not summary.empty
    assert not abc_analysis.empty
    assert not xyz_analysis.empty
    assert not abc_xyz.empty
    assert not inventory_dataset.empty
    required_columns = {
        "CurrentStock",
        "EstimatedStock",
        "ForecastDemand",
        "LeadTime",
        "SafetyStock",
        "ReorderPoint",
        "ReorderQuantity",
        "EconomicOrderQuantity",
        "InventoryRiskScore",
        "InventoryHealthScore",
    }
    assert required_columns.issubset(inventory_dataset.columns)
    assert {"A", "B", "C"} & set(summary["ABCClass"])
    assert {"X", "Y", "Z"} & set(summary["XYZClass"])


def test_inventory_ml_and_summaries_run_end_to_end() -> None:
    raw_df = make_raw_inventory_df()
    forecast_df = make_forecast_df()

    history = build_inventory_history(raw_df, forecast_df)
    summary, _, _, _ = compute_abc_xyz(history)
    inventory_dataset = simulate_inventory_dataset(summary, forecast_df)
    model_metrics, best_model_payload, prediction_frame = train_inventory_risk_models(inventory_dataset)
    enriched = enrich_with_model_predictions(inventory_dataset, prediction_frame)
    metrics = summarize_inventory_metrics(enriched)
    risk = summarize_inventory_risk(enriched)

    assert not model_metrics.empty
    assert "Logistic Regression" in set(model_metrics["model_name"])
    assert best_model_payload
    assert "PredictedHighRiskProbability" in enriched.columns
    assert not metrics.empty
    assert not risk.empty


def test_inventory_recommendations_generate_business_actions() -> None:
    metrics = pd.DataFrame(
        [
            {
                "SeriesKey": "SKU-1",
                "Product": "ALPHA LAMP",
                "Country": "United Kingdom",
                "ProductCategory": "Lighting",
                "HorizonDays": 30,
                "InventoryRiskScore": 85.0,
                "StockCoverageDays": 4.0,
                "SupplierLeadTime": 8.0,
                "ReorderQuantity": 120.0,
                "PotentialRevenueLoss": 500.0,
                "EconomicOrderQuantity": 100.0,
                "LeadTimeVariability": 4.0,
                "FastMovingItem": True,
                "SlowMovingItem": False,
                "DeadStockCandidate": False,
                "XYZClass": "X",
                "InventorySavings": 90.0,
                "SafetyStock": 40.0,
            },
            {
                "SeriesKey": "SKU-2",
                "Product": "BETA FRAME",
                "Country": "France",
                "ProductCategory": "Decor",
                "HorizonDays": 60,
                "InventoryRiskScore": 62.0,
                "StockCoverageDays": 140.0,
                "SupplierLeadTime": 6.0,
                "ReorderQuantity": 0.0,
                "PotentialRevenueLoss": 0.0,
                "EconomicOrderQuantity": 40.0,
                "LeadTimeVariability": 2.0,
                "FastMovingItem": False,
                "SlowMovingItem": True,
                "DeadStockCandidate": True,
                "XYZClass": "Z",
                "InventorySavings": 150.0,
                "SafetyStock": 20.0,
            },
        ]
    )

    recommendations = create_inventory_recommendations(metrics)

    assert not recommendations.empty
    assert {"Emergency Procurement", "Reduce Stock", "Clear Dead Stock"} & set(recommendations["Recommendation"])


def test_inventory_notebook_generation(tmp_path: Path) -> None:
    notebook_path = write_inventory_notebook(tmp_path)

    assert notebook_path.exists()
    payload = json.loads(notebook_path.read_text(encoding="utf-8"))
    assert payload["nbformat"] == 4
    assert any("Inventory Formulas" in "".join(cell.get("source", [])) for cell in payload["cells"])
