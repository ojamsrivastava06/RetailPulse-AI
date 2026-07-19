# Page 10 KPI Cockpit

## Purpose

Provide a configurable operations cockpit for one metric at a time.

## Canvas And Grid

- Canvas: 16:9 widescreen, 1600 x 900 px design base.
- Grid: 8 px spacing system.
- Margins: 24 px outer margin.
- Header band: 96 px.

## Layout

- Large dynamic KPI at the top.
- Comparison and trend visuals in the middle.
- Target and breakdown table at the bottom.

## Visual Map

| ID | Type | Position | Main Fields |
| --- | --- | --- | --- |
| `KC-01` | KPI card | `x24 y112 w760 h140` | `Dynamic KPI`, `Variance`, `Target Achievement %` |
| `KC-02` | Gauge | `x808 y112 w768 h140` | `Dynamic KPI`, `Target Value` |
| `KC-03` | Bar chart | `x24 y276 w760 h220` | `KPI Selector`, `Dynamic KPI`, `Target Value` |
| `KC-04` | Sparkline panel | `x808 y276 w768 h220` | `DimDate[Date]`, `Dynamic KPI` |
| `KC-05` | Table | `x24 y520 w1552 h272` | `KPI Name`, `TargetValue`, `Variance`, `Target Achievement %` |

## Titles And Labels

- Title: `KPI Cockpit`.
- Subtitle: the active KPI, target period, and scenario.
- Keep the cockpit terminology short and executive-friendly.

## Icons And Buttons

- Use a gauge or target icon in the title band.
- Add navigation buttons for the KPI source pages.

## Filters And Slicers

- Slicers: `KPI Selector`, `Target Period`, `Scenario`, `Date`.
- Keep the selector to a curated list of business metrics.

## Bookmarks

- `Revenue Mode`
- `Customer Mode`
- `Inventory Mode`

## Tooltips And Drillthrough

- Tooltip: KPI definition, target logic, and latest drivers.
- Drillthrough: the selected KPI source page.

## Dynamic Titles

- Show the selected KPI name and target period in the page title.

## Conditional Formatting

- Use a clear green-amber-red scale for target achievement and variance.
- Highlight underperforming metrics with a strong warning color.

## Interaction Notes

- This page should change metric context without changing the underlying model.
- Keep the selector visible at all times.

## Export Notes

- The large KPI card must remain the dominant visual in export.
