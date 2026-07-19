from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from forecasting_enhanced import (  # noqa: E402
    FittedModelBundle,
    aggregate_leaderboard,
    feature_columns,
    generate_future_predictions,
    prepare_feature_dataset,
    run_deep_learning_suite,
    select_best_model,
)


def make_forecast_input(days: int = 240) -> pd.DataFrame:
    start = pd.Timestamp("2024-01-01")
    rows: list[dict[str, object]] = []
    series_specs = [
        ("ALPHA LAMP", "United Kingdom", "Lighting", 12.0, 3.5),
        ("BETA FRAME", "France", "Decor", 8.0, 4.2),
    ]

    for offset in range(days):
        day = start + pd.Timedelta(days=offset)
        for idx, (description, country, category, base_qty, unit_price) in enumerate(series_specs, start=1):
            quantity = base_qty + (offset % 7) + (idx * 0.5)
            rows.append(
                {
                    "InvoiceDate": day,
                    "Description": description,
                    "Country": country,
                    "ProductCategory": category,
                    "Quantity": quantity,
                    "Revenue": quantity * unit_price,
                    "InvoiceNo": f"{idx}-{offset}",
                    "CustomerID": 1000 + ((offset + idx) % 25),
                }
            )
    return pd.DataFrame(rows)


def test_prepare_feature_dataset_builds_required_enterprise_features() -> None:
    raw_df = make_forecast_input()

    prepared, selected_meta, historical_daily, selected_frames = prepare_feature_dataset(
        raw_df,
        top_n_series=1,
        min_history=120,
    )

    assert not prepared.empty
    assert not selected_meta.empty
    assert not historical_daily.empty
    assert selected_frames
    assert set(feature_columns()).issubset(prepared.columns)
    assert prepared["SeriesKey"].nunique() == 1


def test_generate_future_predictions_returns_all_business_levels() -> None:
    raw_df = make_forecast_input()
    prepared, _, _, selected_frames = prepare_feature_dataset(raw_df, top_n_series=1, min_history=120)
    series_key, frame = next(iter(selected_frames.items()))

    bundle = FittedModelBundle(
        model_name="Naive",
        kind="baseline",
        estimator=None,
        feature_columns=feature_columns(),
        selected_features=feature_columns(),
        params={},
        metadata={
            "configuration": "default",
            "residual_std": 5.0,
            "avg_unit_price": 3.5,
            "avg_orders": 1.0,
            "avg_customers": 1.0,
            "CountryDemand": float(frame["Sales"].tail(30).sum()),
            "CategoryDemand": float(frame["Sales"].tail(30).sum()),
            "ProductDemand": float(frame["Sales"].tail(30).sum()),
            "AverageOrderValue": float(frame["Revenue"].tail(30).sum()),
            "BasketSize": float(frame["Sales"].tail(30).mean()),
        },
    )

    future_predictions, dashboard = generate_future_predictions(
        selected_frames={series_key: frame},
        fitted_models={series_key: bundle},
        horizons=(30, 60),
    )

    assert not future_predictions.empty
    assert not dashboard.empty
    assert {30, 60}.issubset(set(future_predictions["HorizonDays"].dropna().unique()))
    assert {"SKU", "Category", "Country", "Revenue", "Demand"} == set(future_predictions["ForecastLevel"].unique())
    assert (future_predictions["ForecastDemand"] >= 0).all()
    assert (future_predictions["ForecastRevenue"] >= 0).all()


def test_select_best_model_prefers_full_coverage_candidates() -> None:
    metrics_df = pd.DataFrame(
        [
            {
                "model_name": "Naive",
                "configuration": "default",
                "series_key": "S1",
                "status": "evaluated",
                "reason": "",
                "mae": 12.0,
                "rmse": 15.0,
                "mape": 8.0,
                "smape": 7.0,
                "r2": 0.70,
                "mase": 1.10,
            },
            {
                "model_name": "Naive",
                "configuration": "default",
                "series_key": "S2",
                "status": "evaluated",
                "reason": "",
                "mae": 13.0,
                "rmse": 16.0,
                "mape": 8.5,
                "smape": 7.5,
                "r2": 0.68,
                "mase": 1.12,
            },
            {
                "model_name": "Random Forest",
                "configuration": "default",
                "series_key": "S1",
                "status": "evaluated",
                "reason": "",
                "mae": 8.0,
                "rmse": 10.0,
                "mape": 6.0,
                "smape": 5.0,
                "r2": 0.82,
                "mase": 0.90,
            },
            {
                "model_name": "Random Forest",
                "configuration": "default",
                "series_key": "S2",
                "status": "evaluated",
                "reason": "",
                "mae": 9.0,
                "rmse": 11.0,
                "mape": 6.5,
                "smape": 5.5,
                "r2": 0.80,
                "mase": 0.92,
            },
            {
                "model_name": "LSTM",
                "configuration": "default",
                "series_key": "S1",
                "status": "evaluated",
                "reason": "",
                "mae": 5.0,
                "rmse": 6.0,
                "mape": 4.0,
                "smape": 3.0,
                "r2": 0.91,
                "mase": 0.60,
            },
        ]
    )

    leaderboard = aggregate_leaderboard(metrics_df)
    best = select_best_model(leaderboard)

    lstm_row = leaderboard.loc[leaderboard["model_name"] == "LSTM"].iloc[0]
    rf_row = leaderboard.loc[leaderboard["model_name"] == "Random Forest"].iloc[0]

    assert bool(lstm_row["selection_eligible"]) is False
    assert bool(rf_row["selection_eligible"]) is True
    assert best["model_name"] == "Random Forest"
    assert "excluded from auto-selection" in best["reason"]


def test_run_deep_learning_suite_skips_cleanly_without_tensorflow(tmp_path: Path) -> None:
    series = pd.DataFrame(
        {
            "SeriesKey": ["ANCHOR"] * 150,
            "Target": np.linspace(10.0, 20.0, 150),
        }
    )

    metrics, artifacts, history = run_deep_learning_suite(series, tmp_path)

    assert artifacts == {}
    assert history.empty
    assert set(metrics["model_name"]) == {"LSTM", "Bidirectional LSTM", "GRU", "CNN-LSTM"}
    assert set(metrics["status"]) == {"unavailable"}
