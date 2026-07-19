from __future__ import annotations

import numpy as np
import pandas as pd

from constants import DEFAULT_PROFIT_MARGIN, SEASON_MAP
from retail_rules import classify_product


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add reusable retail features on top of the cleaned transactional frame."""
    data = df.copy()

    if "InvoiceDate" not in data.columns:
        raise KeyError("InvoiceDate is required for feature engineering")

    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")
    data = data.dropna(subset=["InvoiceDate"]).copy()

    data["Year"] = data["InvoiceDate"].dt.year
    data["Month"] = data["InvoiceDate"].dt.month
    data["Week"] = data["InvoiceDate"].dt.isocalendar().week.astype(int)
    data["Quarter"] = data["InvoiceDate"].dt.quarter
    data["Day"] = data["InvoiceDate"].dt.day
    data["Hour"] = data["InvoiceDate"].dt.hour
    data["DayOfWeek"] = data["InvoiceDate"].dt.day_name()
    data["IsWeekend"] = data["InvoiceDate"].dt.dayofweek.isin([5, 6]).astype(int)
    data["IsMonthStart"] = data["InvoiceDate"].dt.is_month_start.astype(int)
    data["IsMonthEnd"] = data["InvoiceDate"].dt.is_month_end.astype(int)
    data["Season"] = data["InvoiceDate"].dt.month.map(SEASON_MAP)

    data["Revenue"] = data["TotalSales"].astype(float)
    data["Profit"] = (data["Revenue"] * DEFAULT_PROFIT_MARGIN).round(2)

    invoice_summary = (
        data.groupby("InvoiceNo", as_index=False)
        .agg(
            InvoiceRevenue=("Revenue", "sum"),
            BasketSize=("InvoiceNo", "size"),
            InvoiceCountry=("Country", "first"),
            InvoiceCustomerID=("CustomerID", "first"),
            FirstInvoiceDate=("InvoiceDate", "first"),
        )
    )
    data = data.merge(invoice_summary, on="InvoiceNo", how="left")
    data["AverageBasketValue"] = (data["InvoiceRevenue"] / data["BasketSize"]).round(2)

    customer_summary = (
        data.groupby("CustomerID", as_index=False)
        .agg(
            TotalRevenue=("Revenue", "sum"),
            TotalOrders=("InvoiceNo", "nunique"),
            AvgOrderValue=("Revenue", "mean"),
            FirstPurchase=("InvoiceDate", "min"),
            LastPurchase=("InvoiceDate", "max"),
            UniqueProducts=("Description", "nunique"),
        )
    )
    customer_summary["CLV"] = customer_summary["TotalRevenue"].round(2)
    customer_summary["CustomerTenure"] = (customer_summary["LastPurchase"] - customer_summary["FirstPurchase"]).dt.days + 1
    customer_summary["CustomerFrequency"] = (customer_summary["TotalOrders"] / customer_summary["CustomerTenure"].replace(0, np.nan)).replace(np.inf, np.nan)
    data = data.merge(customer_summary[["CustomerID", "CLV", "CustomerTenure", "CustomerFrequency"]], on="CustomerID", how="left")

    data["DaysSinceLastPurchase"] = (data["InvoiceDate"].max() - data["InvoiceDate"]).dt.days
    data["MonthlyRevenue"] = data.groupby([data["CustomerID"], data["Year"], data["Month"]])["Revenue"].transform("sum")
    data["MonthlyOrderCount"] = data.groupby([data["CustomerID"], data["Year"], data["Month"]])["InvoiceNo"].transform("nunique")
    data["CountryRevenue"] = data.groupby("Country")["Revenue"].transform("sum")
    data["ProductFrequency"] = data.groupby("Description")["InvoiceNo"].transform("nunique")
    data["AverageOrderValue"] = data.groupby("InvoiceNo")["Revenue"].transform("sum")

    data["ProductCategory"] = data["Description"].apply(classify_product)
    data = validate_engineered_features(data)
    data = data.sort_values("InvoiceDate").reset_index(drop=True)
    return data


def validate_engineered_features(data: pd.DataFrame) -> pd.DataFrame:
    """Coerce engineered numeric features into a stable, model-ready shape."""
    numeric_columns = [
        "Revenue",
        "Profit",
        "AverageBasketValue",
        "CLV",
        "CustomerTenure",
        "CustomerFrequency",
        "MonthlyRevenue",
        "MonthlyOrderCount",
        "CountryRevenue",
        "ProductFrequency",
        "AverageOrderValue",
    ]
    for column in numeric_columns:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")

    data["Profit"] = data["Profit"].clip(lower=0)
    data["AverageBasketValue"] = data["AverageBasketValue"].replace([np.inf, -np.inf], np.nan).fillna(0)
    data["CLV"] = data["CLV"].replace([np.inf, -np.inf], np.nan).fillna(0)
    data["CustomerTenure"] = data["CustomerTenure"].fillna(1).clip(lower=1)
    data["CustomerFrequency"] = data["CustomerFrequency"].replace([np.inf, -np.inf], np.nan).fillna(0)
    data["MonthlyRevenue"] = data["MonthlyRevenue"].replace([np.inf, -np.inf], np.nan).fillna(0)
    data["MonthlyOrderCount"] = data["MonthlyOrderCount"].fillna(0).astype(int)
    data["CountryRevenue"] = data["CountryRevenue"].replace([np.inf, -np.inf], np.nan).fillna(0)
    data["ProductFrequency"] = data["ProductFrequency"].fillna(0).astype(int)
    data["AverageOrderValue"] = data["AverageOrderValue"].replace([np.inf, -np.inf], np.nan).fillna(0)
    return data
