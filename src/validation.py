from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import pandas as pd
import great_expectations as ge

logger = logging.getLogger("retailpulse.validation")


def make_serializable(val: Any) -> Any:
    import numpy as np
    if isinstance(val, dict):
        return {k: make_serializable(v) for k, v in val.items()}
    elif isinstance(val, (list, tuple)):
        return [make_serializable(v) for v in val]
    elif isinstance(val, (np.integer, np.int64)):
        return int(val)
    elif isinstance(val, (np.floating, np.float64)):
        return float(val)
    elif isinstance(val, np.ndarray):
        return make_serializable(val.tolist())
    elif isinstance(val, (pd.Timestamp, Path)):
        return str(val)
    return val


def generate_html_report(results: dict[str, Any], summary_df: pd.DataFrame, df: pd.DataFrame) -> str:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    total_checks = len(summary_df)
    passed_checks = int(summary_df["Success"].sum())
    failed_checks = total_checks - passed_checks
    success_percent = (passed_checks / total_checks * 100) if total_checks > 0 else 0.0
    warning_or_danger_class = "danger" if failed_checks > 0 else "success"

    table_rows = []
    for _, row in summary_df.iterrows():
        status_class = "passed" if row["Success"] else "failed"
        status_text = "PASSED" if row["Success"] else "FAILED"
        table_rows.append(f"""
        <tr>
            <td><code>{row["Expectation"]}</code></td>
            <td><code>{row["Column"]}</code></td>
            <td><small>{row["Parameters"]}</small></td>
            <td><span class="status {status_class}">{status_text}</span></td>
            <td><code>{row["ObservedValue"]}</code></td>
        </tr>
        """)

    table_rows_html = "\n".join(table_rows)

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>RetailPulse - Data Validation Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header {{ border-bottom: 2px solid #0056b3; padding-bottom: 15px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0; color: #0056b3; }}
        .summary-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .card {{ padding: 20px; border-radius: 6px; color: #fff; text-align: center; font-weight: bold; }}
        .card.success {{ background-color: #28a745; }}
        .card.warning {{ background-color: #ffc107; color: #333; }}
        .card.danger {{ background-color: #dc3545; }}
        .card.info {{ background-color: #17a2b8; }}
        .metric-value {{ font-size: 2em; margin-bottom: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; border: 1px solid #ddd; text-align: left; }}
        th {{ background-color: #0056b3; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .status {{ font-weight: bold; padding: 4px 8px; border-radius: 4px; text-transform: uppercase; font-size: 0.85em; }}
        .status.passed {{ background-color: #d4edda; color: #155724; }}
        .status.failed {{ background-color: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>RetailPulse Data Validation Report</h1>
            <p>Generated at: {timestamp}</p>
        </div>
        
        <div class="summary-cards">
            <div class="card info">
                <div class="metric-value">{total_checks}</div>
                <div>Total Expectations</div>
            </div>
            <div class="card success">
                <div class="metric-value">{passed_checks}</div>
                <div>Passed Expectations</div>
            </div>
            <div class="card {warning_or_danger_class}">
                <div class="metric-value">{failed_checks}</div>
                <div>Failed Expectations</div>
            </div>
            <div class="card info">
                <div class="metric-value">{success_percent:.1f}%</div>
                <div>Success Rate</div>
            </div>
        </div>
        
        <h2>Validation Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Expectation Type</th>
                    <th>Column</th>
                    <th>Parameters</th>
                    <th>Status</th>
                    <th>Observed Value</th>
                </tr>
            </thead>
            <tbody>
                {table_rows_html}
            </tbody>
        </table>
    </div>
</body>
</html>
"""


def save_reports(results: dict[str, Any], df: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save JSON
    json_path = output_dir / "validation_report.json"
    serializable_results = make_serializable(results)
    json_path.write_text(json.dumps(serializable_results, indent=2), encoding="utf-8")

    # 2. Compile summary rows
    summary_rows = []
    for res in results.get("results", []):
        config = res.get("expectation_config", {})
        kwargs = config.get("kwargs", {})
        success = res.get("success", False)
        observed = res.get("result", {}).get("observed_value", "N/A")
        summary_rows.append({
            "Expectation": config.get("expectation_type", "Unknown"),
            "Column": kwargs.get("column", "N/A"),
            "Parameters": json.dumps(kwargs),
            "Success": success,
            "ObservedValue": str(observed),
        })

    # Add duplicate rows expectation manually
    duplicate_count = results["statistics"].get("duplicate_rows_count", 0)
    summary_rows.append({
        "Expectation": "expect_no_duplicate_rows",
        "Column": "All Columns",
        "Parameters": "{}",
        "Success": duplicate_count == 0,
        "ObservedValue": str(duplicate_count),
    })

    summary_df = pd.DataFrame(summary_rows)

    # 3. Save Summary CSV
    summary_path = output_dir / "validation_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    # 4. Save HTML
    html_path = output_dir / "validation_report.html"
    html_content = generate_html_report(results, summary_df, df)
    html_path.write_text(html_content, encoding="utf-8")


def validate_dataset(df: pd.DataFrame, output_dir: Path | None = None) -> dict[str, Any]:
    """Validate retail transaction data using Great Expectations."""
    logger.info("Starting data validation check using Great Expectations")
    if output_dir is None:
        output_dir = Path("reports/data_validation")

    try:
        # Wrap the raw dataframe in Great Expectations dataset
        gdf = ge.from_pandas(df)

        # 1. Column existence checks
        gdf.expect_column_to_exist("Invoice")
        gdf.expect_column_to_exist("Customer ID")
        gdf.expect_column_to_exist("Price")
        gdf.expect_column_to_exist("Quantity")
        gdf.expect_column_to_exist("InvoiceDate")
        gdf.expect_column_to_exist("Country")

        # 2. Data type checks
        # Price must be float/numeric, Quantity must be int/numeric
        gdf.expect_column_values_to_be_of_type("Quantity", "int")
        gdf.expect_column_values_to_be_of_type("Price", "float")

        # 3. Missing values & null percentage
        gdf.expect_column_values_to_not_be_null("Invoice", mostly=0.99)
        gdf.expect_column_values_to_not_be_null("Customer ID", mostly=0.75)
        gdf.expect_column_values_to_not_be_null("Price", mostly=0.99)

        # 4. Numeric range checks (Checking for negative quantities / prices)
        # Note: online retail data might contain cancellation invoices (Quantity < 0),
        # but we specify that regular rows should mostly be > 0.
        gdf.expect_column_values_to_be_between("Quantity", min_value=0, mostly=0.85)
        gdf.expect_column_values_to_be_between("Price", min_value=0.0, mostly=0.99)

        # 5. Invalid Customer IDs (check if they are within acceptable ranges)
        gdf.expect_column_values_to_be_between("Customer ID", min_value=0, mostly=0.75)

        # 6. Date format check
        if pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]):
            # If already parsed as datetime, it is inherently in a valid format.
            # We can check its type to ensure type integrity.
            gdf.expect_column_values_to_be_in_type_list("InvoiceDate", ["datetime64[ns]", "datetime64", "Timestamp", "datetime"])
        else:
            gdf.expect_column_values_to_match_strftime_format("InvoiceDate", "%Y-%m-%d %H:%M:%S", mostly=0.95)

        # Run validation
        results_obj = gdf.validate()
        if hasattr(results_obj, "to_json_dict"):
            results = results_obj.to_json_dict()
        else:
            results = dict(results_obj)

        # 7. Check for duplicates manually and attach to results statistics
        duplicate_count = int(df.duplicated().sum())
        if "statistics" not in results:
            results["statistics"] = {}
        results["statistics"]["duplicate_rows_count"] = duplicate_count

        # Save reports
        save_reports(results, df, output_dir)
        logger.info(f"Data validation report successfully saved under: {output_dir}")

        # Check if validation overall failed
        # If any major checks (e.g. column existence) failed, we log it but don't crash
        if not results.get("success", False):
            logger.warning("Data validation failed to meet all specified expectations")

        return results

    except Exception as e:
        logger.error(f"Error executing Great Expectations validation: {e}")
        # Return a fallback validation dictionary instead of crashing
        return {
            "success": False,
            "statistics": {"duplicate_rows_count": 0},
            "results": [],
            "error": str(e),
        }
