from __future__ import annotations

import pandas as pd


def clean_transaction_data(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize raw Online Retail II transactions for downstream analytics."""
    data = df.copy()

    rename_map = {
        "Invoice": "InvoiceNo",
        "Customer ID": "CustomerID",
        "Price": "UnitPrice",
        "TotalAmount": "TotalSales",
    }
    data = data.rename(columns=rename_map)

    required_columns = {"InvoiceNo", "Quantity", "UnitPrice", "InvoiceDate", "CustomerID", "Country"}
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        raise KeyError(f"Input data is missing required columns: {sorted(missing_columns)}")

    data = data.drop_duplicates()
    data = data.dropna(subset=["InvoiceNo", "Quantity", "UnitPrice", "InvoiceDate", "CustomerID", "Country"])
    data["InvoiceNo"] = data["InvoiceNo"].astype(str).str.strip()
    data = data[~data["InvoiceNo"].str.startswith("C", na=False)]
    data = data[data["Quantity"] > 0]
    data = data[(data["UnitPrice"] > 0) & (data["UnitPrice"].notna())]

    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")
    data = data.dropna(subset=["InvoiceDate"])

    data["CustomerID"] = pd.to_numeric(data["CustomerID"], errors="coerce")
    data = data.dropna(subset=["CustomerID"])
    data["Country"] = data["Country"].fillna("Unknown").astype(str)
    data["Description"] = data["Description"].fillna("Unknown").astype(str)
    data["TotalSales"] = data["Quantity"] * data["UnitPrice"]
    data = data.reset_index(drop=True)
    return data
