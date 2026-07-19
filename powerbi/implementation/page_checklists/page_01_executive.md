# Page 01 Executive Dashboard

## Purpose

Provide a single-screen leadership view of revenue, profit, customer risk, inventory risk, and forecast quality.

## Canvas And Grid

- Canvas: 16:9 widescreen, 1600 x 900 px design base.
- Grid: 8 px spacing system.
- Margins: 24 px outer margin on all sides.
- Header band: 96 px across the full width.

## Layout

- Top band: title, subtitle, page icon, and navigator buttons.
- KPI strip: seven headline cards in one row.
- Main body: revenue trend and market map side by side.
- Lower band: profit bridge and risk exception table.

## Visual Map

| ID | Type | Position | Main Fields |
| --- | --- | --- | --- |
| `ED-01` | KPI cards | `x24 y112 w1552 h104` | `Total Revenue`, `Gross Profit`, `Profit Margin`, `Churn Rate`, `Inventory Risk Score`, `Forecast Accuracy %`, `Inventory Savings` |
| `ED-02` | Line chart | `x24 y240 w940 h250` | `DimDate[Date]`, `Total Revenue`, `Running Total` |
| `ED-03` | Map | `x988 y240 w588 h250` | `Country`, `Country Revenue`, `Churn Rate`, `Inventory Risk Score` |
| `ED-04` | Waterfall | `x24 y516 w940 h288` | `Gross Profit`, `Inventory Cost`, `Inventory Savings`, `Variance` |
| `ED-05` | Table | `x988 y516 w588 h288` | `RiskCategory`, `InventoryRiskLevel`, `Forecast Accuracy %`, `RecommendedAction` |

## Titles And Labels

- Title: `Executive Dashboard`.
- Subtitle: selected date range, selected country, and active scenario.
- KPI labels: short business names only.
- Use a single accent color per page and reserve red for critical exceptions.

## Icons And Buttons

- Use a dashboard icon in the title band.
- Add page navigator buttons for `Sales`, `Customers`, `Forecast`, `Inventory`, `Churn`, `Summary`.
- Add a home button that returns to this page.

## Filters And Slicers

- Primary slicers: `Date`, `Country`, `ProductCategory`, `Customer Segment`, `Warehouse`.
- Keep slicers in a compact top strip or a hidden filter pane.
- Use single-select for scenario states.

## Bookmarks

- `Executive Summary`
- `Risk Focus`
- `Opportunity Focus`

## Tooltips And Drillthrough

- Tooltip: compact KPI trend card with delta, status, and variance.
- Drillthrough targets: sales detail, customer detail, product detail, inventory detail, and churn detail.

## Dynamic Titles

- Drive the page subtitle from the selected date, country, and category context.
- Update the KPI strip title only when the active scenario changes.

## Conditional Formatting

- Use green for favorable variance, amber for watch, and red for critical risk.
- Format the exception table by risk severity and forecast error.

## Interaction Notes

- Keep cross-highlighting on for exploratory elements, but avoid noisy cross-filtering on the KPI strip.
- Do not allow the map to obscure the trend story.

## Export Notes

- The page must fit on one exported PDF page without scrolling.
- The exception table should remain readable in presentation mode.
