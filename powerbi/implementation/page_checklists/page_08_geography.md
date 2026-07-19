# Page 08 Geographic Analytics

## Purpose

Review demand, revenue, churn, and inventory by market.

## Canvas And Grid

- Canvas: 16:9 widescreen, 1600 x 900 px design base.
- Grid: 8 px spacing system.
- Margins: 24 px outer margin.
- Header band: 96 px.

## Layout

- Map on the left.
- Country ranking on the right.
- Market summary and risk comparison in the lower section.

## Visual Map

| ID | Type | Position | Main Fields |
| --- | --- | --- | --- |
| `GA-01` | KPI cards | `x24 y112 w1552 h92` | `Country Revenue`, `Total Orders`, `Churn Rate`, `Inventory Cost`, `Forecast Demand`, `Inventory Savings` |
| `GA-02` | Map | `x24 y224 w760 h250` | `Country`, `Country Revenue`, `Churn Rate`, `Inventory Risk Score` |
| `GA-03` | Bar chart | `x808 y224 w768 h250` | `Country`, `Country Revenue`, `Profit Margin` |
| `GA-04` | Matrix | `x24 y500 w760 h292` | `Country`, `Warehouse`, `ProductCategory`, `Total Revenue`, `Inventory Cost` |
| `GA-05` | Bubble chart | `x808 y500 w768 h292` | `Country Revenue`, `Churn Rate`, `Inventory Risk Score`, `Forecast Accuracy %` |

## Titles And Labels

- Title: `Geographic Analytics`.
- Subtitle: regional concentration, market risk, and service coverage.
- Keep country labels readable on the map and ranking chart.

## Icons And Buttons

- Use a map pin or globe icon in the title band.
- Add navigation buttons to sales, churn, and inventory pages.

## Filters And Slicers

- Slicers: `Country`, `Warehouse`, `ProductCategory`, `Customer Segment`.
- Keep region-level filters synchronized across geography pages.

## Bookmarks

- `Domestic`
- `Europe`
- `International`

## Tooltips And Drillthrough

- Tooltip: country profile with revenue, risk, and stock coverage.
- Drillthrough: country detail page.

## Dynamic Titles

- Reflect the active country or region selection in the title.

## Conditional Formatting

- Use map intensity carefully so small countries do not disappear.
- Apply risk colors consistently to the ranking and matrix.

## Interaction Notes

- Keep the map as the entry point, not the only insight.
- The country ranking should explain the map visually.

## Export Notes

- Verify that labels and map fills remain readable after export.
