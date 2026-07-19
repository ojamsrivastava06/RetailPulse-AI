from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import pandas as pd
import streamlit as st

from components.utils import ArtifactEntry, file_bytes, read_text, time_ago


def render_dataframe(frame: pd.DataFrame, *, height: int = 360, use_container_width: bool = True) -> None:
    if frame.empty:
        st.info("No records available.")
        return
    st.dataframe(frame, use_container_width=use_container_width, height=height, hide_index=True)


def render_preview_table(frame: pd.DataFrame, *, rows: int = 10, height: int = 320) -> None:
    render_dataframe(frame.head(rows), height=height)


def render_markdown_preview(path: Path, *, rows: int = 12) -> None:
    content = read_text(path)
    if not content:
        st.info("No preview available.")
        return
    snippet = "\n".join(content.splitlines()[:rows])
    st.code(snippet, language="markdown")


def render_artifact_card(entry: ArtifactEntry, *, download_label: str = "Download") -> None:
    with st.container(border=True):
        st.markdown(f"**{entry.name}**")
        st.caption(f"{entry.kind.upper()} | {entry.size_kb:,.1f} KB | updated {time_ago(entry.modified)}")
        payload = file_bytes(entry.path)
        mime = "application/octet-stream"
        if entry.kind == "csv":
            mime = "text/csv"
        elif entry.kind == "md":
            mime = "text/markdown"
        elif entry.kind == "html":
            mime = "text/html"
        elif entry.kind in {"png", "jpg", "jpeg", "webp"}:
            mime = f"image/{entry.kind if entry.kind != 'jpg' else 'jpeg'}"
        st.download_button(download_label, data=payload, file_name=entry.name, mime=mime, use_container_width=True)


def render_artifact_grid(entries: Sequence[ArtifactEntry], *, columns: int = 3, download_label: str = "Download") -> None:
    if not entries:
        st.info("No artifacts found.")
        return
    chunk_size = max(columns, 1)
    for index in range(0, len(entries), chunk_size):
        row = entries[index : index + chunk_size]
        cols = st.columns(len(row), gap="medium")
        for column, entry in zip(cols, row, strict=False):
            with column:
                render_artifact_card(entry, download_label=download_label)
