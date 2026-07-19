from __future__ import annotations

import os
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np

from evidently import Report, Dataset, DataDefinition
from evidently.presets import DataDriftPreset, DataSummaryPreset

from config import FINAL_PROCESSED_DATA_PATH, REPORTS_DIR
from mlflow_utils import SafeMLflowRun, log_metrics, log_metric, log_artifact

logger = logging.getLogger("retailpulse.monitoring")


def run_data_monitoring(
    reference_df: pd.DataFrame | None = None,
    current_df: pd.DataFrame | None = None,
    output_dir: Path | None = None
) -> dict:
    """Run data drift and data quality reports using Evidently AI.
    
    Compares reference processed dataset with the latest processed dataset.
    Logs monitoring metrics to MLflow and saves reports.
    """
    logger.info("Starting data monitoring and drift detection...")
    
    if output_dir is None:
        output_dir = REPORTS_DIR / "evidently"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data if not provided
    if reference_df is None or current_df is None:
        if not FINAL_PROCESSED_DATA_PATH.exists():
            # Generate dummy fallback data for robustness/tests if file doesn't exist
            logger.warning(f"Dataset path {FINAL_PROCESSED_DATA_PATH} not found. Synthesizing data.")
            df = pd.DataFrame({
                'Quantity': np.random.randint(1, 10, size=100),
                'UnitPrice': np.random.uniform(1.0, 100.0, size=100),
                'Revenue': np.random.uniform(10.0, 1000.0, size=100),
                'Profit': np.random.uniform(1.0, 100.0, size=100),
                'CustomerTenure': np.random.randint(1, 365, size=100),
                'CustomerID': np.random.randint(10000, 20000, size=100),
                'InvoiceDate': pd.date_range("2026-01-01", periods=100)
            })
        else:
            df = pd.read_csv(FINAL_PROCESSED_DATA_PATH)
            if "InvoiceDate" in df.columns:
                df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
        
        # Sort and split 50/50
        if "InvoiceDate" in df.columns:
            df = df.sort_values("InvoiceDate").reset_index(drop=True)
        split_idx = len(df) // 2
        reference_df = df.iloc[:split_idx].copy()
        current_df = df.iloc[split_idx:].copy()

    # Column Mapping and Dataset setup for Evidently
    all_cols = set(reference_df.columns)
    
    # Identify datetime columns
    datetime_cols = []
    for col in reference_df.columns:
        if pd.api.types.is_datetime64_any_dtype(reference_df[col]) or col == "InvoiceDate":
            datetime_cols.append(col)
            
    # Filter numeric and categorical columns
    numeric_candidates = [
        'Quantity', 'UnitPrice', 'TotalSales', 'Revenue', 'Profit',
        'CustomerTenure', 'CustomerFrequency', 'DaysSinceLastPurchase', 'CLV', 'AverageBasketValue'
    ]
    numerical_features = [c for c in numeric_candidates if c in all_cols]
    
    categorical_candidates = ['Country', 'ProductCategory']
    categorical_features = [c for c in categorical_candidates if c in all_cols]
    
    # Construct DataDefinition
    timestamp_col = datetime_cols[0] if datetime_cols else None
    data_def = DataDefinition(
        timestamp=timestamp_col,
        numerical_columns=numerical_features,
        categorical_columns=categorical_features
    )
    
    # Convert pandas DataFrames to Evidently Datasets
    reference_dataset = Dataset.from_pandas(reference_df, data_definition=data_def)
    current_dataset = Dataset.from_pandas(current_df, data_definition=data_def)

    # 1. Run Data Drift Report
    drift_report = Report(metrics=[DataDriftPreset()])
    drift_snapshot = drift_report.run(
        reference_data=reference_dataset,
        current_data=current_dataset
    )
    drift_html_path = output_dir / "data_drift_report.html"
    drift_snapshot.save_html(str(drift_html_path))
    
    # 2. Run Data Quality Report
    quality_report = Report(metrics=[DataSummaryPreset()])
    quality_snapshot = quality_report.run(
        reference_data=reference_dataset,
        current_data=current_dataset
    )
    quality_html_path = output_dir / "data_quality_report.html"
    quality_snapshot.save_html(str(quality_html_path))
    
    # 3. Parse report metrics for summaries
    drift_data = drift_snapshot.dict()
    quality_data = quality_snapshot.dict()
    
    drift_summary_metrics = {}
    feature_drift_details = {}
    
    # Parse Data Drift metrics
    for metric in drift_data.get("metrics", []):
        metric_name = metric.get("metric_name", "")
        metric_type = metric.get("config", {}).get("type", "")
        val = metric.get("value")
        
        if "DriftedColumnsCount" in metric_type or "DriftedColumnsCount" in metric_name:
            if isinstance(val, dict):
                drift_summary_metrics["drift_count"] = val.get("count")
                drift_summary_metrics["drift_share"] = val.get("share")
        elif "ValueDrift" in metric_type or "ValueDrift" in metric_name:
            col_name = metric.get("config", {}).get("column")
            threshold = metric.get("config", {}).get("threshold", 0.05)
            if col_name is not None and val is not None:
                is_drifted = val < threshold
                feature_drift_details[col_name] = {
                    "p_value": float(val),
                    "threshold": threshold,
                    "drifted": bool(is_drifted)
                }
                
    # Add a fallback for overall dataset drift status
    drift_share = drift_summary_metrics.get("drift_share", 0.0)
    dataset_drifted = drift_share >= 0.5
    drift_summary_metrics["dataset_drifted"] = dataset_drifted

    # Parse Data Quality / Summary metrics
    quality_summary_metrics = {}
    for metric in quality_data.get("metrics", []):
        metric_name = metric.get("metric_name", "")
        metric_type = metric.get("config", {}).get("type", "")
        val = metric.get("value")
        
        if "RowCount" in metric_type or "RowCount" in metric_name:
            quality_summary_metrics["row_count"] = val
        elif "ColumnCount" in metric_type or "ColumnCount" in metric_name:
            col_type = metric.get("config", {}).get("column_type")
            if col_type is None:
                quality_summary_metrics["column_count"] = val
        elif "DatasetMissingValueCount" in metric_type or "DatasetMissingValueCount" in metric_name:
            if isinstance(val, dict):
                quality_summary_metrics["missing_values_count"] = val.get("count")
                quality_summary_metrics["missing_values_share"] = val.get("share")
        elif "DuplicatedRowCount" in metric_type or "DuplicatedRowCount" in metric_name:
            quality_summary_metrics["duplicated_rows_count"] = val

    # Combine into a single summary dict
    summary_dict = {
        "drift_summary": drift_summary_metrics,
        "quality_summary": quality_summary_metrics,
        "feature_drift": feature_drift_details
    }
    
    # Save JSON summary
    json_path = output_dir / "drift_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=2)
        
    # Save CSV summary (flat table of feature drift details)
    csv_rows = []
    for col, details in feature_drift_details.items():
        csv_rows.append({
            "feature": col,
            "p_value": details["p_value"],
            "threshold": details["threshold"],
            "drifted": int(details["drifted"])
        })
    csv_path = output_dir / "drift_summary.csv"
    if csv_rows:
        pd.DataFrame(csv_rows).to_csv(csv_path, index=False)
    else:
        pd.DataFrame(columns=["feature", "p_value", "threshold", "drifted"]).to_csv(csv_path, index=False)

    # 4. Log to MLflow
    with SafeMLflowRun("RetailPulse Data Monitoring", run_name="evidently_monitoring_run"):
        mlflow_metrics = {}
        if drift_summary_metrics.get("drift_count") is not None:
            mlflow_metrics["drift_count"] = float(drift_summary_metrics["drift_count"])
        if drift_summary_metrics.get("drift_share") is not None:
            mlflow_metrics["drift_share"] = float(drift_summary_metrics["drift_share"])
        mlflow_metrics["dataset_drifted"] = 1.0 if dataset_drifted else 0.0
        
        if quality_summary_metrics.get("row_count") is not None:
            mlflow_metrics["dataset_row_count"] = float(quality_summary_metrics["row_count"])
        if quality_summary_metrics.get("missing_values_count") is not None:
            mlflow_metrics["missing_values_count"] = float(quality_summary_metrics["missing_values_count"])
        if quality_summary_metrics.get("missing_values_share") is not None:
            mlflow_metrics["missing_values_share"] = float(quality_summary_metrics["missing_values_share"])
            
        log_metrics(mlflow_metrics)
        
        for col, details in feature_drift_details.items():
            log_metric(f"drift_p_value_{col}", details["p_value"])
            log_metric(f"drift_status_{col}", 1.0 if details["drifted"] else 0.0)
            
        log_artifact(drift_html_path, "monitoring_reports")
        log_artifact(quality_html_path, "monitoring_reports")
        log_artifact(json_path, "monitoring_reports")
        log_artifact(csv_path, "monitoring_reports")
        
    logger.info("Data monitoring completed successfully.")
    return summary_dict


if __name__ == "__main__":
    run_data_monitoring()
