from __future__ import annotations

from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle


def draw_simple_treemap(ax: plt.Axes, values: Sequence[float], labels: Sequence[str], title: str) -> None:
    clean_values = [max(float(value), 0.0) for value in values]
    total = sum(clean_values)
    if total <= 0:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.set_axis_off()
        ax.set_title(title)
        return

    colors = plt.cm.Blues(np.linspace(0.35, 0.95, len(clean_values)))
    left = 0.0
    for value, label, color in zip(clean_values, labels, colors, strict=False):
        width = value / total
        rect = Rectangle((left, 0), width, 1, facecolor=color, edgecolor="white", linewidth=1.5)
        ax.add_patch(rect)
        ax.text(left + (width / 2), 0.5, f"{label}\n{value:,.0f}", ha="center", va="center", fontsize=8)
        left += width

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()
    ax.set_title(title)


def draw_waterfall(ax: plt.Axes, labels: Sequence[str], values: Sequence[float], title: str) -> None:
    running = 0.0
    bases = []
    colors = []
    for value in values:
        if value >= 0:
            bases.append(running)
            colors.append("#2ca02c")
            running += value
        else:
            bases.append(running + value)
            colors.append("#d62728")
            running += value

    ax.bar(labels, values, bottom=bases, color=colors)
    ax.axhline(0, color="black", linewidth=1)
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=45)


def draw_radar_chart(
    ax: plt.Axes,
    labels: Sequence[str],
    values: Sequence[float],
    title: str,
    *,
    color: str = "#1f77b4",
) -> None:
    if not labels:
        ax.set_axis_off()
        ax.set_title(title)
        return

    clean_values = [max(0.0, float(value)) for value in values]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]
    plot_values = clean_values + clean_values[:1]

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.plot(angles, plot_values, color=color, linewidth=2)
    ax.fill(angles, plot_values, color=color, alpha=0.15)
    ax.set_title(title)
