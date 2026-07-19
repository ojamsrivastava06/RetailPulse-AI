from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from constants import RAW_DATA_FILENAMES


@dataclass(frozen=True)
class ProjectSettings:
    project_root: Path
    data_dir: Path
    raw_data_dir: Path
    interim_data_dir: Path
    processed_data_dir: Path
    processed_output_dir: Path
    external_data_dir: Path
    reports_dir: Path
    figures_dir: Path
    models_dir: Path
    notebooks_dir: Path
    docs_dir: Path
    app_dir: Path
    service_dir: Path
    tests_dir: Path
    raw_data_candidates: tuple[Path, ...]

    @property
    def raw_data_path(self) -> Path:
        return next((path for path in self.raw_data_candidates if path.exists()), self.raw_data_candidates[0])


def build_settings(project_root: Path | None = None) -> ProjectSettings:
    root = (project_root or Path(__file__).resolve().parents[1]).resolve()
    data_dir = root / "data"
    reports_dir = root / "reports"

    return ProjectSettings(
        project_root=root,
        data_dir=data_dir,
        raw_data_dir=data_dir / "raw",
        interim_data_dir=data_dir / "interim",
        processed_data_dir=data_dir / "processed",
        processed_output_dir=root / "processed",
        external_data_dir=data_dir / "external",
        reports_dir=reports_dir,
        figures_dir=reports_dir / "figures",
        models_dir=root / "models",
        notebooks_dir=root / "notebooks",
        docs_dir=root / "docs",
        app_dir=root / "app",
        service_dir=root / "service",
        tests_dir=root / "tests",
        raw_data_candidates=tuple(data_dir / "raw" / filename for filename in RAW_DATA_FILENAMES),
    )


PROJECT_SETTINGS = build_settings()
