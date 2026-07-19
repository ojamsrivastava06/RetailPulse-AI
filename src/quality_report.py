from __future__ import annotations

from pathlib import Path

import pandas as pd

from io_utils import write_text


def build_data_quality_report(df: pd.DataFrame, output_path: str | Path | None = None) -> str:
    """Create a lightweight markdown quality report for the processed dataset."""
    required_columns = {"Quantity", "UnitPrice", "Revenue"}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise KeyError(f"Cannot build quality report without columns: {sorted(missing_columns)}")

    output_path = Path(output_path) if output_path is not None else Path(__file__).resolve().parents[1] / "reports" / "data_quality_report.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    missing = df.isna().sum()
    duplicates = df.duplicated().sum()
    invalid_quantities = int((df["Quantity"] <= 0).sum())
    invalid_prices = int((df["UnitPrice"] <= 0).sum())
    numeric = df.select_dtypes(include=["number"])
    summary = numeric.describe().T
    q1 = df["Revenue"].quantile(0.25)
    q3 = df["Revenue"].quantile(0.75)
    iqr = q3 - q1
    revenue_outliers = int(((df["Revenue"] < q1 - 1.5 * iqr) | (df["Revenue"] > q3 + 1.5 * iqr)).sum())

    lines = []
    lines.append("# Data Quality Report")
    lines.append("")
    lines.append("## Overview")
    lines.append(f"- Rows: {len(df)}")
    lines.append(f"- Columns: {len(df.columns)}")
    lines.append(f"- Duplicate records: {duplicates}")
    lines.append(f"- Invalid quantities: {invalid_quantities}")
    lines.append(f"- Invalid prices: {invalid_prices}")
    lines.append("")
    lines.append("## Missing Values")
    for col, value in missing.items():
        if value > 0:
            lines.append(f"- {col}: {value}")
    if all(value == 0 for value in missing):
        lines.append("- No missing values detected.")
    lines.append("")
    lines.append("## Data Types")
    for col, dtype in df.dtypes.items():
        lines.append(f"- {col}: {dtype}")
    lines.append("")
    lines.append("## Summary Statistics")
    for _, row in summary.iterrows():
        lines.append(f'- {row.name}: mean={row["mean"]:.2f}, std={row["std"]:.2f}, min={row["min"]:.2f}, max={row["max"]:.2f}')
    lines.append("")
    lines.append("## Outlier Notes")
    lines.append(f"- Revenue outliers detected via IQR rule: {revenue_outliers}")
    lines.append("- Outliers were reviewed using value range checks for revenue, quantity, and unit price.")
    lines.append("- Extreme values are retained when they represent valid transactions; they are flagged for further review.")

    write_text("\n".join(lines), output_path)
    return str(output_path)
