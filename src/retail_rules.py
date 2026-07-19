from __future__ import annotations

import pandas as pd

from constants import DEFAULT_PRODUCT_CATEGORY, HOLIDAY_MONTH_DAY_PAIRS, PRODUCT_CATEGORY_KEYWORDS


def classify_product(description: str) -> str:
    text = str(description).lower()
    for category, keywords in PRODUCT_CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return DEFAULT_PRODUCT_CATEGORY


def build_holiday_flag(series: pd.Series) -> pd.Series:
    flags: list[int] = []
    for timestamp in pd.to_datetime(series):
        try:
            flags.append(int((int(timestamp.month), int(timestamp.day)) in HOLIDAY_MONTH_DAY_PAIRS))
        except Exception:
            flags.append(0)
    return pd.Series(flags, index=series.index, dtype=int)


def normalize_retail_frame(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    rename_map = {
        "Customer ID": "CustomerID",
        "Invoice": "InvoiceNo",
        "Price": "UnitPrice",
        "TotalAmount": "Revenue",
        "TotalSales": "Revenue",
    }
    applicable = {source: target for source, target in rename_map.items() if source in data.columns and target not in data.columns}
    if applicable:
        data = data.rename(columns=applicable)

    required_columns = {"InvoiceDate", "Description", "Country", "Quantity"}
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        raise KeyError(f"Input data is missing required columns: {sorted(missing_columns)}")

    if "InvoiceNo" not in data.columns:
        data["InvoiceNo"] = data.index.astype(str)
    if "CustomerID" not in data.columns:
        data["CustomerID"] = -1
    if "ProductCategory" not in data.columns:
        data["ProductCategory"] = data["Description"].apply(classify_product)
    if "Revenue" not in data.columns:
        if "UnitPrice" not in data.columns:
            raise KeyError("Revenue is missing and cannot be derived because UnitPrice is unavailable")
        data["Revenue"] = pd.to_numeric(data["Quantity"], errors="coerce").fillna(0) * pd.to_numeric(
            data["UnitPrice"], errors="coerce"
        ).fillna(0)

    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")
    data["Quantity"] = pd.to_numeric(data["Quantity"], errors="coerce").fillna(0)
    data["Revenue"] = pd.to_numeric(data["Revenue"], errors="coerce").fillna(0)
    data["Description"] = data["Description"].fillna("Unknown").astype(str)
    data["Country"] = data["Country"].fillna("Unknown").astype(str)
    data["ProductCategory"] = data["ProductCategory"].fillna(DEFAULT_PRODUCT_CATEGORY).astype(str)
    data["CustomerID"] = pd.to_numeric(data["CustomerID"], errors="coerce").fillna(-1).astype(int)

    data = data.dropna(subset=["InvoiceDate"]).copy()
    data = data[data["Quantity"] >= 0].copy()
    return data.reset_index(drop=True)
