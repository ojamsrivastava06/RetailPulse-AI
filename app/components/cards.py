from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Sequence

import streamlit as st


@dataclass(frozen=True)
class KpiCard:
    label: str
    value: str
    delta: str = ""
    note: str = ""
    status: str = "neutral"
    icon: str = "●"


@dataclass(frozen=True)
class NavigationCard:
    label: str
    description: str
    page_path: str
    icon: str = "📊"
    action_label: str = "Open"


def status_pill(text: str, status: str = "neutral") -> str:
    safe_status = status.lower().strip()
    return f"<span class='rp-pill rp-pill-{safe_status}'>{escape(str(text))}</span>"


def render_section_header(title: str, subtitle: str | None = None, *, tag: str | None = None) -> None:
    parts = [f"<div class='rp-section-header'><div class='rp-section-title'>{escape(title)}</div>"]
    if tag:
        parts.append(f"<div>{status_pill(tag, 'neutral')}</div>")
    if subtitle:
        parts.append(f"<div class='rp-section-subtitle'>{escape(subtitle)}</div>")
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def _card_html(card: KpiCard) -> str:
    icon = escape(str(card.icon)) if card.icon else ""
    status = escape(card.status.lower().strip())
    return f"""
<div class="rp-kpi-card rp-status-{status}">
  <div class="rp-kpi-label">{icon} {escape(card.label)}</div>
  <div class="rp-kpi-value">{escape(card.value)}</div>
  <div class="rp-kpi-delta">{escape(card.delta)}</div>
  <div class="rp-kpi-footnote">{escape(card.note)}</div>
</div>
"""


def render_kpi_cards(cards: Sequence[KpiCard], *, columns: int = 4) -> None:
    if not cards:
        return
    chunk_size = max(columns, 1)
    for index in range(0, len(cards), chunk_size):
        row = cards[index : index + chunk_size]
        cols = st.columns(len(row), gap="medium")
        for column, card in zip(cols, row, strict=False):
            with column:
                st.markdown(_card_html(card), unsafe_allow_html=True)


def render_navigation_cards(cards: Sequence[NavigationCard], *, columns: int = 3) -> None:
    if not cards:
        return
    chunk_size = max(columns, 1)
    for index in range(0, len(cards), chunk_size):
        row = cards[index : index + chunk_size]
        cols = st.columns(len(row), gap="medium")
        for column, card in zip(cols, row, strict=False):
            with column:
                st.markdown(
                    f"""
<div class="rp-nav-card">
  <div class="rp-nav-title">{escape(str(card.icon))} {escape(card.label)}</div>
  <div class="rp-nav-desc">{escape(card.description)}</div>
</div>
""",
                    unsafe_allow_html=True,
                )
                st.page_link(card.page_path, label=card.action_label, icon="➡️")


def render_metric_strip(cards: Sequence[KpiCard]) -> None:
    render_kpi_cards(cards, columns=min(len(cards), 4))
