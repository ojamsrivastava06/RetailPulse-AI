from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from io_utils import write_text


def notebook_lines(content: str) -> list[str]:
    stripped = content.strip("\n")
    if not stripped:
        return []
    return [line if line.endswith("\n") else f"{line}\n" for line in stripped.splitlines(keepends=True)]


def make_notebook_cell(cell_type: str, content: str) -> dict[str, Any]:
    cell: dict[str, Any] = {
        "cell_type": cell_type,
        "metadata": {},
        "source": notebook_lines(content),
    }
    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    return cell


def write_notebook_json(notebook: dict[str, Any], path: Path) -> Path:
    return write_text(json.dumps(notebook, indent=2), path)
