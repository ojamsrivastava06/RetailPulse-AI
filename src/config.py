from __future__ import annotations

from settings import PROJECT_SETTINGS

PROJECT_ROOT = PROJECT_SETTINGS.project_root
DATA_DIR = PROJECT_SETTINGS.data_dir
RAW_DATA_CANDIDATES = list(PROJECT_SETTINGS.raw_data_candidates)
RAW_DATA_PATH = PROJECT_SETTINGS.raw_data_path
PROCESSED_DATA_PATH = PROJECT_SETTINGS.processed_data_dir / "retailpulse_processed.csv"
FINAL_PROCESSED_DATA_PATH = PROJECT_SETTINGS.processed_data_dir / "final_processed_dataset.csv"
REPORTS_DIR = PROJECT_SETTINGS.reports_dir
FIGURES_DIR = PROJECT_SETTINGS.figures_dir
MODELS_DIR = PROJECT_SETTINGS.models_dir
PROCESSED_OUTPUT_DIR = PROJECT_SETTINGS.processed_output_dir
DOCS_DIR = PROJECT_SETTINGS.docs_dir
