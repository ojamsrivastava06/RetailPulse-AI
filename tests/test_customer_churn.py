from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from customer_churn import (
    build_customer_churn_frame,
    build_shap_summary,
    generate_customer_intelligence_outputs,
    run_phase_five,
    write_customer_churn_notebook,
)


def make_sample_churn_df() -> pd.DataFrame:
    start_date = pd.Timestamp("2024-01-01")
    rows: list[dict[str, object]] = []
    product_rows = [
        ("ALPHA LAMP", "United Kingdom"),
        ("BETA FRAME", "France"),
        ("GAMMA HOLDER", "Germany"),
    ]

    for customer_id in range(1, 7):
        for invoice_index in range(4):
            invoice_date = start_date + pd.Timedelta(days=(customer_id * 18) + (invoice_index * 15))
            invoice_no = f"{customer_id}-{invoice_index}"
            description, country = product_rows[(customer_id + invoice_index) % len(product_rows)]
            for line_index in range(2):
                quantity = 1 + ((customer_id + invoice_index + line_index) % 4)
                unit_price = 8.0 + customer_id + line_index
                rows.append(
                    {
                        "InvoiceNo": invoice_no,
                        "StockCode": f"S{customer_id}{invoice_index}{line_index}",
                        "Description": description,
                        "Quantity": quantity,
                        "InvoiceDate": invoice_date,
                        "UnitPrice": unit_price,
                        "CustomerID": customer_id,
                        "Country": country,
                        "TotalSales": quantity * unit_price,
                    }
                )
    return pd.DataFrame(rows)


def test_build_customer_churn_frame_creates_labels_and_scores() -> None:
    raw_df = make_sample_churn_df()
    customer_frame = build_customer_churn_frame(raw_df)

    expected_columns = {
        "CustomerID",
        "DaysSinceLastPurchase",
        "ExpectedNextPurchase",
        "CustomerTenure",
        "PurchaseGap",
        "RetentionAge",
        "RecencyTrend",
        "FrequencyTrend",
        "RevenueTrend",
        "ChurnLabel_30",
        "ChurnLabel_60",
        "ChurnLabel_90",
        "ChurnLabel_180",
        "CustomerActivityScore",
        "CustomerEngagementScore",
        "CustomerHealthScore",
        "IsChurn",
    }

    assert expected_columns.issubset(customer_frame.columns)
    assert customer_frame["IsChurn"].nunique() == 2
    assert customer_frame["CustomerHealthScore"].between(0, 100).all()
    assert customer_frame["ExpectedNextPurchase"].notna().all()


def test_generate_customer_intelligence_outputs_produces_decision_tables() -> None:
    raw_df = make_sample_churn_df()
    customer_frame = build_customer_churn_frame(raw_df)
    result = generate_customer_intelligence_outputs(customer_frame)

    scored_frame = result["customer_frame"]

    assert result["best_model_name"]
    assert {"ChurnProbability", "RetentionProbability", "RecommendedAction", "ActionReasoning"}.issubset(scored_frame.columns)
    assert scored_frame["ChurnProbability"].between(0, 1).all()
    assert scored_frame["RetentionProbability"].between(0, 1).all()
    assert not result["leaderboard"].empty
    assert not result["feature_importance"].empty


def test_write_customer_churn_notebook(tmp_path: Path) -> None:
    notebook_path = write_customer_churn_notebook(tmp_path)

    payload = json.loads(notebook_path.read_text(encoding="utf-8"))
    assert payload["nbformat"] == 4
    assert any("Business Problem" in "".join(cell.get("source", [])) for cell in payload["cells"])


def test_shap_summary_uses_proxy_fallback() -> None:
    feature_importance = pd.DataFrame(
        {
            "feature": ["DaysSinceLastPurchase", "CustomerVelocity"],
            "importance": [0.8, 0.2],
        }
    )
    permutation_importance = pd.DataFrame(
        {
            "feature": ["DaysSinceLastPurchase", "CustomerVelocity"],
            "importance_mean": [0.4, 0.1],
            "importance_std": [0.02, 0.01],
        }
    )

    shap_summary = build_shap_summary(feature_importance, permutation_importance)

    assert {"feature", "mean_abs_shap", "status"}.issubset(shap_summary.columns)
    assert shap_summary["mean_abs_shap"].gt(0).any()
    assert shap_summary["status"].isin({"proxy", "proxy_fallback"}).all()


def test_run_phase_five_smoke(tmp_path: Path) -> None:
    raw_df = make_sample_churn_df()
    result = run_phase_five(
        input_df=raw_df,
        output_dir=tmp_path / "processed",
        reports_dir=tmp_path / "reports",
        figures_dir=tmp_path / "figures",
        models_dir=tmp_path / "models",
        target_visual_count=8,
        figure_dpi=72,
    )

    assert result["best_model_name"]
    assert result["notebook_path"].exists()
    assert 1 <= len(result["visual_paths"]) <= 8
    assert (tmp_path / "processed" / "customer_churn_predictions.csv").exists()
    assert (tmp_path / "models" / "best_churn_model.pkl").exists()
    assert (tmp_path / "reports" / "customer_churn_report.md").exists()
