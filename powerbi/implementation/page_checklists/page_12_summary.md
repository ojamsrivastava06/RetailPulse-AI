# Page 12 Executive Summary

## Purpose

Provide a board-ready summary of what happened, what changed, and what should happen next.

## Canvas And Grid

- Canvas: 16:9 widescreen, 1600 x 900 px design base.
- Grid: 8 px spacing system.
- Margins: 24 px outer margin.
- Header band: 96 px.

## Layout

- High-level cards at the top.
- Compact trend and bridge visuals in the middle.
- Action summary table and notes at the bottom.

## Visual Map

| ID | Type | Position | Main Fields |
| --- | --- | --- | --- |
| `ES-01` | KPI cards | `x24 y112 w1552 h92` | `Total Revenue`, `Gross Profit`, `Churn Rate`, `Inventory Risk Score`, `Forecast Accuracy %`, `Inventory Savings` |
| `ES-02` | Line chart | `x24 y224 w760 h250` | `DimDate[Date]`, `Total Revenue`, `Gross Profit` |
| `ES-03` | Waterfall | `x808 y224 w768 h250` | `Variance`, `Inventory Savings`, `Profit Margin` |
| `ES-04` | Table | `x24 y500 w1040 h292` | `Metric`, `Status`, `Change`, `RecommendedAction` |
| `ES-05` | Notes panel | `x1088 y500 w488 h292` | `Board Pack`, `Ops Pack`, `Finance Pack` notes |

## Titles And Labels

- Title: `Executive Summary`.
- Subtitle: board-level view with the minimum number of controls.
- Keep labels sparse and highly readable.

## Icons And Buttons

- Use a summary or board icon in the title band.
- Add navigation buttons for `Board Pack`, `Ops Pack`, and `Finance Pack`.

## Filters And Slicers

- Keep filters minimal and bookmark-driven.
- Use preset views rather than a full slicer rail.

## Bookmarks

- `Board Pack`
- `Ops Pack`
- `Finance Pack`

## Tooltips And Drillthrough

- Tooltip: concise status narrative for each KPI.
- Drillthrough: optional links to the detailed pages.

## Dynamic Titles

- Reflect the current board pack or operating pack in the title.

## Conditional Formatting

- Use very restrained color so the page feels board-ready.
- Reserve strong red only for urgent exceptions.

## Interaction Notes

- This page should feel lighter than the analytical pages.
- Keep the action summary table as the main decision aid.

## Export Notes

- Ensure the page reads well on a printed board pack.
