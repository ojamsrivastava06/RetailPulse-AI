from __future__ import annotations

import pandas as pd

from retailpulse_pipeline import clean_and_engineer


def test_clean_and_engineer_preserves_legacy_alias_columns() -> None:
    raw_df = pd.DataFrame(
        {
            "Invoice": ["A1", "A2"],
            "StockCode": ["S1", "S2"],
            "Description": ["ALPHA LAMP", "BETA FRAME"],
            "Quantity": [2, 3],
            "InvoiceDate": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "Price": [10.0, 12.0],
            "Customer ID": [101, 102],
            "Country": ["United Kingdom", "France"],
        }
    )

    engineered = clean_and_engineer(raw_df)

    expected_aliases = {"Invoice", "Customer ID", "Price", "TotalAmount", "Weekend"}
    expected_modern_columns = {"InvoiceNo", "CustomerID", "UnitPrice", "TotalSales", "IsWeekend", "Revenue"}

    assert expected_aliases.issubset(engineered.columns)
    assert expected_modern_columns.issubset(engineered.columns)
    assert engineered["Invoice"].equals(engineered["InvoiceNo"])
    assert engineered["Customer ID"].equals(engineered["CustomerID"])
    assert engineered["Price"].equals(engineered["UnitPrice"])
