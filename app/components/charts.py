from __future__ import annotations

from typing import Sequence

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from theme import build_plotly_template, get_palette, normalize_theme_mode


def _apply_style(fig: go.Figure, mode: str, *, title: str | None = None, height: int = 420) -> go.Figure:
    theme_mode = normalize_theme_mode(mode)
    palette = get_palette(theme_mode)
    fig.update_layout(
        template=build_plotly_template(theme_mode),
        height=height,
        margin=dict(l=12, r=12, t=56, b=28),
        paper_bgcolor=palette.background,
        plot_bgcolor=palette.surface,
        title=dict(text=title or "", x=0.02, xanchor="left"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(showline=False)
    fig.update_yaxes(showline=False)
    return fig


def render_plotly(fig: go.Figure, *, use_container_width: bool = True, key: str | None = None) -> None:
    st.plotly_chart(
        fig,
        use_container_width=use_container_width,
        key=key,
        config={"displaylogo": False, "responsive": True},
    )


def line_chart(
    frame: pd.DataFrame,
    x: str,
    y: str,
    *,
    color: str | None = None,
    title: str = "",
    mode: str = "dark",
    height: int = 420,
    markers: bool = False,
    fill: str | None = None,
) -> go.Figure:
    fig = px.line(frame, x=x, y=y, color=color, markers=markers, color_discrete_sequence=None)
    if fill and fig.data:
        for trace in fig.data:
            trace.update(fill=fill)
    return _apply_style(fig, mode, title=title, height=height)


def area_chart(
    frame: pd.DataFrame,
    x: str,
    y: str,
    *,
    color: str | None = None,
    title: str = "",
    mode: str = "dark",
    height: int = 420,
) -> go.Figure:
    fig = px.area(frame, x=x, y=y, color=color)
    return _apply_style(fig, mode, title=title, height=height)


def bar_chart(
    frame: pd.DataFrame,
    x: str,
    y: str,
    *,
    color: str | None = None,
    orientation: str = "v",
    title: str = "",
    mode: str = "dark",
    height: int = 420,
    text: str | None = None,
) -> go.Figure:
    fig = px.bar(frame, x=x, y=y, color=color, orientation=orientation, text=text)
    if orientation == "h":
        fig.update_yaxes(autorange="reversed")
    return _apply_style(fig, mode, title=title, height=height)


def scatter_chart(
    frame: pd.DataFrame,
    x: str,
    y: str,
    *,
    size: str | None = None,
    color: str | None = None,
    hover_data: Sequence[str] | None = None,
    title: str = "",
    mode: str = "dark",
    height: int = 420,
) -> go.Figure:
    fig = px.scatter(frame, x=x, y=y, size=size, color=color, hover_data=hover_data)
    return _apply_style(fig, mode, title=title, height=height)


def treemap_chart(
    frame: pd.DataFrame,
    path: Sequence[str],
    values: str,
    *,
    color: str | None = None,
    title: str = "",
    mode: str = "dark",
    height: int = 420,
) -> go.Figure:
    fig = px.treemap(frame, path=path, values=values, color=color)
    return _apply_style(fig, mode, title=title, height=height)


def heatmap_chart(
    matrix: pd.DataFrame,
    *,
    title: str = "",
    mode: str = "dark",
    height: int = 420,
) -> go.Figure:
    fig = px.imshow(matrix, aspect="auto", color_continuous_scale="Blues")
    return _apply_style(fig, mode, title=title, height=height)


def waterfall_chart(
    labels: Sequence[str],
    values: Sequence[float],
    *,
    title: str = "",
    mode: str = "dark",
    height: int = 420,
) -> go.Figure:
    fig = go.Figure(go.Waterfall(x=list(labels), y=list(values)))
    return _apply_style(fig, mode, title=title, height=height)


def funnel_chart(
    labels: Sequence[str],
    values: Sequence[float],
    *,
    title: str = "",
    mode: str = "dark",
    height: int = 420,
) -> go.Figure:
    fig = go.Figure(go.Funnel(y=list(labels), x=list(values), textinfo="value+percent initial"))
    return _apply_style(fig, mode, title=title, height=height)


def donut_chart(
    frame: pd.DataFrame,
    names: str,
    values: str,
    *,
    title: str = "",
    mode: str = "dark",
    height: int = 420,
) -> go.Figure:
    fig = px.pie(frame, names=names, values=values, hole=0.55)
    return _apply_style(fig, mode, title=title, height=height)

