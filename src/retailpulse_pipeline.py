from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from config import FIGURES_DIR, PROCESSED_DATA_PATH, PROJECT_ROOT, RAW_DATA_PATH, REPORTS_DIR
from constants import DEFAULT_RANDOM_STATE
from features import engineer_features
from io_utils import save_figure as persist_figure, write_dataframe, write_text
from preprocessing import clean_transaction_data

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")

DATASET_PATH = RAW_DATA_PATH
PROCESSED_DIR = PROCESSED_DATA_PATH.parent
LEGACY_FALLBACK_DATASET = PROJECT_ROOT.parent.parent / "online_retail_II.xlsx"


def load_raw_data(dataset_path: str | Path | None = None) -> pd.DataFrame:
    """Load the Online Retail II workbook from the project workspace."""
    if dataset_path is not None:
        path = Path(dataset_path)
    elif DATASET_PATH.exists():
        path = DATASET_PATH
    else:
        path = LEGACY_FALLBACK_DATASET
    df = pd.read_excel(path)
    return df.copy()


def clean_and_engineer(df: pd.DataFrame) -> pd.DataFrame:
    """Clean retail transactions and add business-ready features."""
    try:
        from validation import validate_dataset
        validate_dataset(df)
    except Exception as e:
        logger.warning("Great Expectations data validation failed to run: %s", e)

    data = engineer_features(clean_transaction_data(df))
    compatibility_aliases = {
        "Invoice": "InvoiceNo",
        "Customer ID": "CustomerID",
        "Price": "UnitPrice",
        "TotalAmount": "TotalSales",
        "Weekend": "IsWeekend",
    }
    for alias, source in compatibility_aliases.items():
        if source in data.columns:
            data[alias] = data[source]
    return data


def save_processed_data(df: pd.DataFrame, output_path: str | Path | None = None) -> Path:
    """Save the cleaned dataframe in CSV format for downstream use."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = Path(output_path) if output_path is not None else PROCESSED_DATA_PATH
    return write_dataframe(df, path)


def load_processed_data(path: str | Path | None = None) -> pd.DataFrame:
    path = Path(path) if path is not None else PROCESSED_DIR / "retailpulse_processed.csv"
    return pd.read_csv(path, parse_dates=["InvoiceDate"])


def save_figure(fig, filename: str, output_dir: str | Path | None = None) -> Path:
    output_dir = Path(output_dir) if output_dir is not None else FIGURES_DIR
    return persist_figure(fig, output_dir / filename)


def generate_eda_outputs(df: pd.DataFrame, output_dir: str | Path | None = None) -> list[Path]:
    output_dir = Path(output_dir) if output_dir is not None else FIGURES_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    paths: list[Path] = []
    sample_size = min(len(df), 10000)
    sample_frame = df.sample(sample_size, random_state=DEFAULT_RANDOM_STATE) if sample_size else df

    daily_sales = (
        df.set_index("InvoiceDate")
        .resample("D")["Revenue"]
        .sum()
        .rename("Daily Revenue")
    )
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.lineplot(x=daily_sales.index, y=daily_sales.values, ax=ax, color="#4C78A8")
    ax.set_title("Daily Sales Trend")
    ax.set_xlabel("Date")
    ax.set_ylabel("Revenue")
    paths.append(save_figure(fig, "01_daily_sales.png", output_dir))

    monthly_sales = df.groupby([df["InvoiceDate"].dt.to_period("M")]).agg(TotalRevenue=("Revenue", "sum"), Orders=("Invoice", "nunique"))
    monthly_sales.index = monthly_sales.index.to_timestamp()
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.lineplot(x=monthly_sales.index, y=monthly_sales["TotalRevenue"], ax=ax, color="#F58518")
    ax.set_title("Monthly Sales")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue")
    paths.append(save_figure(fig, "02_monthly_sales.png", output_dir))

    fig, ax = plt.subplots(figsize=(12, 5))
    sns.lineplot(x=monthly_sales.index, y=monthly_sales["Orders"], ax=ax, color="#54A24B")
    ax.set_title("Monthly Order Volume")
    ax.set_xlabel("Month")
    ax.set_ylabel("Orders")
    paths.append(save_figure(fig, "03_order_volume.png", output_dir))

    top_products = (
        df.groupby("Description")
        .agg(Revenue=("Revenue", "sum"), Quantity=("Quantity", "sum"))
        .sort_values("Revenue", ascending=False)
        .head(10)
    )
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.barplot(x=top_products.index, y=top_products["Revenue"], palette="viridis", ax=ax)
    ax.set_title("Top Products by Revenue")
    ax.set_xlabel("Product")
    ax.set_ylabel("Revenue")
    ax.tick_params(axis="x", rotation=45)
    paths.append(save_figure(fig, "04_top_products.png", output_dir))

    worst_products = (
        df.groupby("Description")
        .agg(Revenue=("Revenue", "sum"), Quantity=("Quantity", "sum"))
        .sort_values("Revenue", ascending=True)
        .head(10)
    )
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.barplot(x=worst_products.index, y=worst_products["Revenue"], palette="rocket", ax=ax)
    ax.set_title("Worst Products by Revenue")
    ax.set_xlabel("Product")
    ax.set_ylabel("Revenue")
    ax.tick_params(axis="x", rotation=45)
    paths.append(save_figure(fig, "05_worst_products.png", output_dir))

    country_sales = df.groupby("Country")["Revenue"].sum().sort_values(ascending=False).head(12)
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.barplot(x=country_sales.index, y=country_sales.values, palette="mako", ax=ax)
    ax.set_title("Revenue by Country")
    ax.set_xlabel("Country")
    ax.set_ylabel("Revenue")
    ax.tick_params(axis="x", rotation=45)
    paths.append(save_figure(fig, "06_country_sales.png", output_dir))

    customer_distribution = df.groupby("Customer ID").size().reset_index(name="Orders")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(customer_distribution["Orders"], bins=30, kde=True, ax=ax, color="#4C78A8")
    ax.set_title("Customer Order Frequency Distribution")
    ax.set_xlabel("Orders per Customer")
    ax.set_ylabel("Customers")
    paths.append(save_figure(fig, "07_customer_distribution.png", output_dir))

    basket_sizes = df.groupby("Invoice").size()
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(basket_sizes, bins=30, kde=True, ax=ax, color="#F58518")
    ax.set_title("Basket Size Distribution")
    ax.set_xlabel("Items per Basket")
    ax.set_ylabel("Transactions")
    paths.append(save_figure(fig, "08_basket_size.png", output_dir))

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(df["Quantity"], bins=40, kde=True, ax=ax, color="#54A24B")
    ax.set_title("Quantity Distribution")
    ax.set_xlabel("Quantity")
    ax.set_ylabel("Transactions")
    paths.append(save_figure(fig, "09_quantity_distribution.png", output_dir))

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(df["Price"], bins=40, kde=True, ax=ax, color="#B279A2")
    ax.set_title("Price Distribution")
    ax.set_xlabel("Price")
    ax.set_ylabel("Transactions")
    paths.append(save_figure(fig, "10_price_distribution.png", output_dir))

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(df["Revenue"], bins=40, kde=True, ax=ax, color="#72B7B2")
    ax.set_title("Revenue Distribution")
    ax.set_xlabel("Revenue")
    ax.set_ylabel("Transactions")
    paths.append(save_figure(fig, "11_revenue_distribution.png", output_dir))

    pivot = df.pivot_table(index="Month", columns="Country", values="Revenue", aggfunc="sum").fillna(0)
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.heatmap(pivot.head(12), cmap="Blues", annot=False, ax=ax)
    ax.set_title("Monthly Revenue Heatmap by Country")
    ax.set_xlabel("Country")
    ax.set_ylabel("Month")
    paths.append(save_figure(fig, "12_country_month_heatmap.png", output_dir))

    numeric = df[["Quantity", "Price", "Revenue", "Profit", "Year", "Month", "Quarter", "Hour", "Weekend", "AverageBasketValue", "CLV"]]
    corr = numeric.corr()
    fig, ax = plt.subplots(figsize=(12, 9))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
    ax.set_title("Correlation Matrix")
    paths.append(save_figure(fig, "13_correlation_matrix.png", output_dir))

    pareto = (
        df.groupby("Description")["Revenue"]
        .sum()
        .sort_values(ascending=False)
        .cumsum()
        / df["Revenue"].sum() * 100
    )
    fig, ax = plt.subplots(figsize=(10, 5))
    pareto.head(20).plot(kind="line", ax=ax, color="#4C78A8")
    ax.set_title("Pareto Analysis - Revenue Contribution")
    ax.set_xlabel("Products")
    ax.set_ylabel("Cumulative Revenue %")
    paths.append(save_figure(fig, "14_pareto_analysis.png", output_dir))

    abc = df.groupby("Description")["Revenue"].sum().sort_values(ascending=False)
    abc_cumsum = abc.cumsum() / abc.sum()
    abc_labels = pd.Series(np.where(abc_cumsum <= 0.8, "A", np.where(abc_cumsum <= 0.95, "B", "C")), index=abc.index)
    fig, ax = plt.subplots(figsize=(10, 5))
    abc_labels.value_counts().reindex(["A", "B", "C"]).plot(kind="bar", ax=ax, color=["#4C78A8", "#F58518", "#54A24B"])
    ax.set_title("ABC Analysis")
    ax.set_xlabel("Category")
    ax.set_ylabel("Products")
    paths.append(save_figure(fig, "15_abc_analysis.png", output_dir))

    product_category_sales = df.groupby("ProductCategory")["Revenue"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x=product_category_sales.index, y=product_category_sales.values, palette="viridis", ax=ax)
    ax.set_title("Category Analysis by Product Type")
    ax.set_xlabel("Category")
    ax.set_ylabel("Revenue")
    paths.append(save_figure(fig, "16_category_analysis.png", output_dir))

    seasonal = df.groupby(["Month", "Year"])["Revenue"].sum().reset_index()
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.lineplot(data=seasonal, x="Month", y="Revenue", hue="Year", ax=ax)
    ax.set_title("Seasonal Trend")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue")
    paths.append(save_figure(fig, "17_seasonal_trend.png", output_dir))

    hourly_sales = df.groupby("Hour")["Revenue"].sum()
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x=hourly_sales.index, y=hourly_sales.values, palette="rocket", ax=ax)
    ax.set_title("Hourly Sales")
    ax.set_xlabel("Hour")
    ax.set_ylabel("Revenue")
    paths.append(save_figure(fig, "18_hourly_sales.png", output_dir))

    weekly_sales = df.groupby("Week")["Revenue"].sum()
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.lineplot(x=weekly_sales.index, y=weekly_sales.values, color="#4C78A8", ax=ax)
    ax.set_title("Weekly Sales")
    ax.set_xlabel("Week")
    ax.set_ylabel("Revenue")
    paths.append(save_figure(fig, "19_weekly_sales.png", output_dir))

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=df, x="Country", y="Revenue", ax=ax)
    ax.set_title("Revenue Boxplot by Country")
    ax.set_xlabel("Country")
    ax.set_ylabel("Revenue")
    ax.tick_params(axis="x", rotation=45)
    paths.append(save_figure(fig, "20_revenue_boxplot.png", output_dir))

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=df, x="Weekend", y="Revenue", ax=ax)
    ax.set_title("Weekend vs Weekday Revenue")
    ax.set_xlabel("Day Type")
    ax.set_ylabel("Revenue")
    paths.append(save_figure(fig, "21_weekend_boxplot.png", output_dir))

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.scatterplot(data=sample_frame, x="Quantity", y="Revenue", hue="Weekend", ax=ax)
    ax.set_title("Revenue vs Quantity")
    ax.set_xlabel("Quantity")
    ax.set_ylabel("Revenue")
    paths.append(save_figure(fig, "22_scatter_quantity_revenue.png", output_dir))

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.scatterplot(data=sample_frame, x="Price", y="Revenue", hue="Year", ax=ax)
    ax.set_title("Revenue vs Price")
    ax.set_xlabel("Price")
    ax.set_ylabel("Revenue")
    paths.append(save_figure(fig, "23_scatter_price_revenue.png", output_dir))

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.violinplot(data=df, x="Weekend", y="Revenue", ax=ax)
    ax.set_title("Revenue Violin Plot by Weekend")
    ax.set_xlabel("Weekend")
    ax.set_ylabel("Revenue")
    paths.append(save_figure(fig, "24_revenue_violin.png", output_dir))

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.violinplot(data=df, x="Month", y="Revenue", ax=ax)
    ax.set_title("Revenue Violin Plot by Month")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue")
    paths.append(save_figure(fig, "25_revenue_month_violin.png", output_dir))

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    summary = {
        "rows": len(df),
        "customers": df["Customer ID"].nunique(),
        "products": df["Description"].nunique(),
        "countries": df["Country"].nunique(),
        "revenue": round(float(df["Revenue"].sum()), 2),
        "profit": round(float(df["Profit"].sum()), 2),
        "average_order_value": round(float(df.groupby("Invoice")["Revenue"].sum().mean()), 2),
    }
    business_insights = ["RetailPulse Business Insights", "=========================="]
    business_insights.extend(f"{key}: {value}" for key, value in summary.items())
    write_text("\n".join(business_insights) + "\n", REPORTS_DIR / "business_insights.txt")

    return paths


def build_project_pipeline(dataset_path: str | Path | None = None) -> tuple[pd.DataFrame, Path]:
    raw_df = load_raw_data(dataset_path)
    cleaned_df = clean_and_engineer(raw_df)
    output_path = save_processed_data(cleaned_df)
    generate_eda_outputs(cleaned_df)
    return cleaned_df, output_path
