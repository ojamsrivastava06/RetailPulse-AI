from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import plotly.graph_objects as go

ThemeMode = Literal["dark", "light"]


@dataclass(frozen=True)
class ThemePalette:
    background: str
    surface: str
    surface_alt: str
    text: str
    muted: str
    primary: str
    secondary: str
    accent: str
    success: str
    warning: str
    danger: str
    border: str
    sidebar_bg: str
    overlay: str


FONT_FAMILY = '"Segoe UI", "Aptos", Tahoma, sans-serif'

LIGHT_PALETTE = ThemePalette(
    background="#F6F7F4",
    surface="#FFFFFF",
    surface_alt="#F3F5F1",
    text="#0F172A",
    muted="#475569",
    primary="#2457A6",
    secondary="#0F766E",
    accent="#8A5A13",
    success="#15803D",
    warning="#D97706",
    danger="#DC2626",
    border="#D9E2EC",
    sidebar_bg="#EEF3F9",
    overlay="rgba(29, 78, 216, 0.08)",
)

DARK_PALETTE = ThemePalette(
    background="#111315",
    surface="#1A1D1F",
    surface_alt="#222628",
    text="#F3F1EA",
    muted="#BAB4A7",
    primary="#5B8DEF",
    secondary="#2DD4BF",
    accent="#F2B84B",
    success="#35C46D",
    warning="#F2A33A",
    danger="#F06A5F",
    border="#33383B",
    sidebar_bg="#171A1C",
    overlay="rgba(91, 141, 239, 0.14)",
)


def normalize_theme_mode(value: str | None) -> ThemeMode:
    if value and value.lower().startswith("l"):
        return "light"
    return "dark"


def get_palette(mode: ThemeMode) -> ThemePalette:
    return LIGHT_PALETTE if mode == "light" else DARK_PALETTE


def build_css_variables(mode: ThemeMode) -> str:
    palette = get_palette(mode)
    return f"""
:root {{
  --rp-bg: {palette.background};
  --rp-surface: {palette.surface};
  --rp-surface-alt: {palette.surface_alt};
  --rp-text: {palette.text};
  --rp-muted: {palette.muted};
  --rp-primary: {palette.primary};
  --rp-secondary: {palette.secondary};
  --rp-accent: {palette.accent};
  --rp-success: {palette.success};
  --rp-warning: {palette.warning};
  --rp-danger: {palette.danger};
  --rp-border: {palette.border};
  --rp-sidebar-bg: {palette.sidebar_bg};
  --rp-overlay: {palette.overlay};
  --rp-font: {FONT_FAMILY};
  --rp-radius: 8px;
  --rp-radius-sm: 8px;
  --rp-radius-xs: 6px;
  --rp-shadow: 0 12px 28px rgba(15, 23, 42, 0.12);
}}
"""


def build_plotly_template(mode: ThemeMode) -> go.layout.Template:
    palette = get_palette(mode)
    return go.layout.Template(
        layout=go.Layout(
            font=dict(family=FONT_FAMILY, color=palette.text, size=13),
            paper_bgcolor=palette.background,
            plot_bgcolor=palette.surface,
            colorway=[
                palette.primary,
                palette.secondary,
                palette.accent,
                palette.success,
                palette.warning,
                palette.danger,
            ],
            margin=dict(l=20, r=20, t=55, b=24),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                bgcolor="rgba(0,0,0,0)",
            ),
            xaxis=dict(
                gridcolor="rgba(148, 163, 184, 0.15)",
                zeroline=False,
                linecolor=palette.border,
                tickfont=dict(color=palette.muted),
            ),
            yaxis=dict(
                gridcolor="rgba(148, 163, 184, 0.15)",
                zeroline=False,
                linecolor=palette.border,
                tickfont=dict(color=palette.muted),
            ),
        )
    )
