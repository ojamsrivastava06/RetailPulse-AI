from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from config import DATA_DIR, FIGURES_DIR, MODELS_DIR, PROCESSED_OUTPUT_DIR, REPORTS_DIR


def ensure_directories(extra_paths: Iterable[Path] | None = None) -> None:
    project_paths = [
        DATA_DIR,
        DATA_DIR / "raw",
        DATA_DIR / "interim",
        DATA_DIR / "processed",
        DATA_DIR / "external",
        PROCESSED_OUTPUT_DIR,
        FIGURES_DIR,
        REPORTS_DIR,
        MODELS_DIR,
    ]
    if extra_paths is not None:
        project_paths.extend(extra_paths)

    for path in project_paths:
        path.mkdir(parents=True, exist_ok=True)
