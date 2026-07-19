from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import shutil
from typing import Any

import joblib
import matplotlib.pyplot as plt
import pandas as pd


def slugify(value: str) -> str:
    filtered = "".join(character.lower() if character.isalnum() else "_" for character in value)
    while "__" in filtered:
        filtered = filtered.replace("__", "_")
    return filtered.strip("_") or "artifact"


def backup_existing_file(path: Path) -> None:
    if not path.exists():
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    backup_path = path.with_name(f"{path.stem}.bak_{timestamp}{path.suffix}")
    shutil.copy2(path, backup_path)


def write_dataframe(df: pd.DataFrame, path: Path, *, index: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_existing_file(path)
    df.to_csv(path, index=index)
    return path


def write_text(content: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_existing_file(path)
    path.write_text(content, encoding="utf-8")
    return path


def write_joblib(payload: Any, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_existing_file(path)
    joblib.dump(payload, path)
    return path


def save_figure(fig: plt.Figure, path: Path, *, dpi: int = 300) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_existing_file(path)
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return path
