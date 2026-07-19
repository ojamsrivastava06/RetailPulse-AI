from __future__ import annotations

import pandas as pd


def frame_to_markdown_like(df: pd.DataFrame, rows: int = 10) -> str:
    if df.empty:
        return "No rows available."
    return "```\n" + df.head(rows).to_string(index=False) + "\n```"
