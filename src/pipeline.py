from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import FINAL_PROCESSED_DATA_PATH, PROCESSED_DATA_PATH, RAW_DATA_PATH, REPORTS_DIR
from preprocessing import clean_transaction_data
from features import engineer_features
from quality_report import build_data_quality_report
from io_utils import write_dataframe
from logger import get_logger
from utils import ensure_directories

logger = get_logger(__name__)


def run_phase_one() -> tuple[pd.DataFrame, Path]:
    """Run the Phase 1 data engineering pipeline with artifact-safe writes."""
    ensure_directories()
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Raw dataset not found at {RAW_DATA_PATH}")

    logger.info("Loading raw retail data from %s", RAW_DATA_PATH)
    raw_df = pd.read_excel(RAW_DATA_PATH)

    try:
        from validation import validate_dataset
        validate_dataset(raw_df)
    except Exception as e:
        logger.warning("Great Expectations data validation failed to run: %s", e)

    cleaned_df = clean_transaction_data(raw_df)
    feature_df = engineer_features(cleaned_df)
    write_dataframe(feature_df, PROCESSED_DATA_PATH)
    write_dataframe(feature_df, FINAL_PROCESSED_DATA_PATH)
    build_data_quality_report(feature_df, REPORTS_DIR / "data_quality_report.md")
    return feature_df, FINAL_PROCESSED_DATA_PATH
