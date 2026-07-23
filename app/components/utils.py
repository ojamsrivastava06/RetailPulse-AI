from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

import pandas as pd
import streamlit as st

APP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_ROOT.parent
SRC_ROOT = PROJECT_ROOT / "src"
for import_path in (PROJECT_ROOT, SRC_ROOT):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from src.config import PROJECT_SETTINGS
from src.logger import get_logger
from theme import build_css_variables, normalize_theme_mode

logger = get_logger("retailpulse.streamlit")

THEME_KEY = "rp_theme_mode"
REFRESH_KEY = "rp_last_refresh"

ASSETS_DIR = APP_ROOT / "assets"
ICONS_DIR = APP_ROOT / "icons"
STYLES_DIR = APP_ROOT / "styles"
STYLE_PATH = STYLES_DIR / "style.css"
LOGO_PATH = ASSETS_DIR / "logo.png"

DATA_DIR = PROJECT_SETTINGS.data_dir
PROCESSED_DIR = PROJECT_SETTINGS.processed_output_dir
PROCESSED_DATA_DIR = PROJECT_SETTINGS.processed_data_dir
REPORTS_DIR = PROJECT_SETTINGS.reports_dir
FIGURES_DIR = PROJECT_SETTINGS.figures_dir
MODELS_DIR = PROJECT_SETTINGS.models_dir


@dataclass(frozen=True)
class DatasetSpec:
    key: str
    path: Path
    parse_dates: tuple[str, ...] = ()


@dataclass(frozen=True)
class ArtifactEntry:
    name: str
    path: Path
    modified: datetime
    size_kb: float
    kind: str


@dataclass(frozen=True)
class PageLink:
    label: str
    path: str
    icon: str
    description: str


DATASET_SPECS: tuple[DatasetSpec, ...] = (
    DatasetSpec("sales", PROJECT_SETTINGS.processed_data_dir / "final_processed_dataset.csv", ("InvoiceDate",)),
    DatasetSpec("customer_segments", PROCESSED_DIR / "customer_segments.csv", ("FirstPurchase", "LastPurchase")),
    DatasetSpec("rfm_table", PROCESSED_DIR / "rfm_table.csv", ("FirstPurchase", "LastPurchase")),
    DatasetSpec("customer_retention_metrics", PROCESSED_DIR / "customer_retention_metrics.csv", ("FirstPurchase", "LastPurchase", "SnapshotDate")),
    DatasetSpec("customer_churn_predictions", PROCESSED_DIR / "customer_churn_predictions.csv", ("FirstPurchase", "LastPurchase", "SnapshotDate", "ExpectedNextPurchase")),
    DatasetSpec("customer_health_scores", PROCESSED_DIR / "customer_health_scores.csv"),
    DatasetSpec("customer_probability_scores", PROCESSED_DIR / "customer_probability_scores.csv"),
    DatasetSpec("customer_business_actions", PROCESSED_DIR / "customer_business_actions.csv"),
    DatasetSpec("customer_model_leaderboard", PROCESSED_DIR / "customer_model_leaderboard.csv"),
    DatasetSpec("forecast_results", PROCESSED_DIR / "forecast_results.csv", ("Date",)),
    DatasetSpec("future_predictions", PROCESSED_DIR / "future_predictions.csv", ("Date",)),
    DatasetSpec("forecast_metrics", PROCESSED_DIR / "forecast_metrics.csv"),
    DatasetSpec("forecast_dashboard", PROCESSED_DIR / "forecast_dashboard.csv"),
    DatasetSpec("forecast_comparison", PROCESSED_DIR / "forecast_comparison.csv"),
    DatasetSpec("inventory_dataset", PROCESSED_DIR / "inventory_dataset.csv", ("Date",)),
    DatasetSpec("inventory_metrics", PROCESSED_DIR / "inventory_metrics.csv"),
    DatasetSpec("inventory_risk", PROCESSED_DIR / "inventory_risk.csv"),
    DatasetSpec("inventory_recommendations", PROCESSED_DIR / "inventory_recommendations.csv"),
    DatasetSpec("inventory_dashboard", PROCESSED_DIR / "inventory_dashboard.csv"),
    DatasetSpec("abc_analysis", PROCESSED_DIR / "abc_analysis.csv"),
    DatasetSpec("xyz_analysis", PROCESSED_DIR / "xyz_analysis.csv"),
    DatasetSpec("abc_xyz_matrix", PROCESSED_DIR / "abc_xyz_matrix.csv"),
    DatasetSpec("segment_summary", PROCESSED_DIR / "segment_summary.csv"),
    DatasetSpec("leaderboard", PROCESSED_DIR / "leaderboard.csv"),
    DatasetSpec("business_decisions", PROCESSED_DIR / "business_decisions.csv"),
    DatasetSpec("executive_summary", PROCESSED_DIR / "executive_summary.csv", ("GeneratedAt",)),
    DatasetSpec("business_alerts", PROCESSED_DIR / "business_alerts.csv"),
    DatasetSpec("priority_actions", PROCESSED_DIR / "priority_actions.csv"),
    DatasetSpec("risk_summary", PROCESSED_DIR / "risk_summary.csv"),
    DatasetSpec("scenario_analysis", PROCESSED_DIR / "scenario_analysis.csv"),
    DatasetSpec("recommendation_scores", PROCESSED_DIR / "recommendation_scores.csv"),
)

PAGE_LINKS: tuple[PageLink, ...] = (
    PageLink("Home", "Home.py", "🏠", "Platform overview"),
    PageLink("Executive Dashboard", "pages/01_Executive_Dashboard.py", "📈", "Leadership KPIs"),
    PageLink("Sales Analytics", "pages/02_Sales_Analytics.py", "💹", "Revenue and mix"),
    PageLink("Customer Intelligence", "pages/03_Customer_Intelligence.py", "👥", "RFM and CLV"),
    PageLink("Demand Forecasting", "pages/04_Demand_Forecasting.py", "🔮", "Modelled demand"),
    PageLink("Inventory Optimization", "pages/05_Inventory_Optimization.py", "📦", "Stock and replenishment"),
    PageLink("Customer Churn", "pages/06_Customer_Churn.py", "🛡️", "Retention actions"),
    PageLink("Settings", "pages/09_Settings.py", "⚙️", "Theme and refresh"),
)



def current_theme_mode(default: str = "dark") -> str:
    return normalize_theme_mode(st.session_state.get(THEME_KEY, default))


def set_theme_mode(mode: str) -> None:
    st.session_state[THEME_KEY] = normalize_theme_mode(mode)


def bootstrap_page(page_title: str, page_icon: str = "📊", *, layout: str = "wide") -> str:
    st.set_page_config(
        page_title=f"RetailPulse | {page_title}",
        page_icon=page_icon,
        layout=layout,
        initial_sidebar_state="expanded",
    )
    st.session_state.setdefault(THEME_KEY, "dark")
    st.session_state.setdefault(REFRESH_KEY, datetime.utcnow().isoformat())
    theme_mode = current_theme_mode()
    apply_theme(theme_mode)
    return theme_mode


def apply_theme(mode: str | None = None) -> str:
    theme_mode = normalize_theme_mode(mode or st.session_state.get(THEME_KEY, "dark"))
    css_text = STYLE_PATH.read_text(encoding="utf-8") if STYLE_PATH.exists() else ""
    st.markdown(f"<style>{build_css_variables(theme_mode)}\n{css_text}</style>", unsafe_allow_html=True)
    return theme_mode


@st.cache_data(show_spinner=False)
def load_csv(path_str: str, parse_dates: tuple[str, ...] = ()) -> pd.DataFrame:
    path = Path(path_str)
    if not path.exists():
        logger.warning("Missing CSV: %s", path)
        return pd.DataFrame()
    try:
        return pd.read_csv(path, parse_dates=list(parse_dates) or None, low_memory=False)
    except Exception:
        logger.exception("Failed to read %s", path)
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_dataset(key: str) -> pd.DataFrame:
    spec = next((item for item in DATASET_SPECS if item.key == key), None)
    if spec is None:
        raise KeyError(f"Unknown dataset key: {key}")
    return load_csv(str(spec.path), spec.parse_dates)


@st.cache_data(show_spinner=False)
def load_data_bundle() -> dict[str, pd.DataFrame]:
    return {spec.key: load_dataset(spec.key) for spec in DATASET_SPECS}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def file_bytes(path: Path) -> bytes:
    if not path.exists():
        return b""
    return path.read_bytes()


def list_artifacts(directory: Path, suffixes: Sequence[str], *, exclude_backup: bool = True) -> list[ArtifactEntry]:
    if not directory.exists():
        return []
    allowed_suffixes = {suffix.lower() for suffix in suffixes}
    entries: list[ArtifactEntry] = []
    for path in directory.iterdir():
        if not path.is_file():
            continue
        if exclude_backup and ".bak_" in path.name:
            continue
        if path.suffix.lower() not in allowed_suffixes:
            continue
        stat = path.stat()
        entries.append(
            ArtifactEntry(
                name=path.name,
                path=path,
                modified=datetime.fromtimestamp(stat.st_mtime),
                size_kb=round(stat.st_size / 1024, 1),
                kind=path.suffix.lower().lstrip("."),
            )
        )
    return sorted(entries, key=lambda item: item.modified, reverse=True)


def list_reports() -> list[ArtifactEntry]:
    md_reports = list_artifacts(REPORTS_DIR, (".md",))
    html_reports = list_artifacts(REPORTS_DIR / "evidently", (".html",))
    return md_reports + html_reports


def list_figures() -> list[ArtifactEntry]:
    return list_artifacts(FIGURES_DIR, (".png", ".jpg", ".jpeg", ".webp"))


def list_models() -> list[ArtifactEntry]:
    return list_artifacts(MODELS_DIR, (".pkl", ".joblib"))


def format_currency(value: Any, *, digits: int = 0) -> str:
    if pd.isna(value):
        return "n/a"
    return f"${float(value):,.{digits}f}" if digits else f"${float(value):,.0f}"


def format_percent(value: Any, *, digits: int = 1) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{float(value) * 100:.{digits}f}%"


def format_number(value: Any, *, digits: int = 0) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{float(value):,.{digits}f}" if digits else f"{int(round(float(value))):,}"


def format_compact(value: Any) -> str:
    if pd.isna(value):
        return "n/a"
    number = float(value)
    magnitude = abs(number)
    if magnitude >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f}B"
    if magnitude >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    if magnitude >= 1_000:
        return f"{number / 1_000:.1f}K"
    if number.is_integer():
        return f"{int(number):,}"
    return f"{number:.1f}"


def format_date_range(start: pd.Timestamp | None, end: pd.Timestamp | None) -> str:
    if start is None or end is None or pd.isna(start) or pd.isna(end):
        return "No date range available"
    return f"{pd.to_datetime(start).date():%d %b %Y} to {pd.to_datetime(end).date():%d %b %Y}"


def safe_divide(numerator: float | int, denominator: float | int, *, default: float = 0.0) -> float:
    try:
        return float(numerator) / float(denominator) if float(denominator) else default
    except Exception:
        return default


def format_change(current: float | int | None, previous: float | int | None, *, digits: int = 1, percent: bool = False) -> str:
    if current is None or previous is None or pd.isna(current) or pd.isna(previous):
        return "No prior comparison"
    current_value = float(current)
    previous_value = float(previous)
    if previous_value == 0:
        return "No prior comparison"
    delta = current_value - previous_value
    if percent:
        return f"{(delta / previous_value) * 100:+.{digits}f}% vs prior period"
    return f"{delta:+,.{digits}f} vs prior period"


def time_ago(value: datetime | pd.Timestamp | None) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    try:
        timestamp = pd.to_datetime(value, utc=True)
    except (TypeError, ValueError):
        return "n/a"
    if pd.isna(timestamp):
        return "n/a"
    delta = datetime.now(timestamp.tzinfo) - timestamp.to_pydatetime()
    days = max(delta.days, 0)
    hours = max(delta.seconds // 3600, 0)
    if days > 0:
        return f"{days}d ago"
    if hours > 0:
        return f"{hours}h ago"
    return "just now"


def filter_forecast_comparison(forecast_comparison: pd.DataFrame, selections: dict[str, Any] | None = None) -> pd.DataFrame:
    if forecast_comparison.empty:
        return forecast_comparison
    filtered = forecast_comparison.copy()
    if selections:
        selected_countries = selections.get("Country", [])
        selected_categories = selections.get("ProductCategory", [])
        selected_products = selections.get("Product", [])
        selected_models = selections.get("Model", [])
        if selected_models and "model_name" in filtered.columns:
            filtered = filtered[filtered["model_name"].astype(str).isin(selected_models)]
        if (selected_countries or selected_categories or selected_products) and "series_key" in filtered.columns:
            def matches(val):
                if not isinstance(val, str) or val == "ALL":
                    return True
                parts = [p.strip() for p in val.split("|")]
                if len(parts) < 3:
                    return True
                prod, country, cat = parts[0], parts[1], parts[2]
                if selected_countries and country not in selected_countries:
                    return False
                if selected_categories and cat not in selected_categories:
                    return False
                if selected_products and prod not in selected_products:
                    return False
                return True
            filtered = filtered[filtered["series_key"].apply(matches)]
    if filtered.empty:
        return forecast_comparison
    return filtered


def calculate_forecast_accuracy(forecast_comparison: pd.DataFrame, selections: dict[str, Any] | None = None) -> float:
    filtered = filter_forecast_comparison(forecast_comparison, selections)
    if filtered.empty or "mape" not in filtered.columns:
        return 0.0
    min_mape = filtered["mape"].min()
    return max(0.0, 1.0 - float(min_mape) / 100.0)

