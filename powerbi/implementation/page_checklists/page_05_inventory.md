# Page 05 Inventory Intelligence

## Purpose

Manage stock coverage, replenishment, inventory cost, and risk.

## Canvas And Grid

- Canvas: 16:9 widescreen, 1600 x 900 px design base.
- Grid: 8 px spacing system.
- Margins: 24 px outer margin.
- Header band: 96 px.

## Layout

- KPI strip at the top.
- Risk heatmap and replenishment scatter in the center.
- Cost bridge, warehouse ranking, and exception table share the lower band as a split panel.

## Visual Map

| ID | Type | Position | Main Fields |
| --- | --- | --- | --- |
| `II-01` | KPI cards | `x24 y112 w1552 h92` | `Inventory Cost`, `Inventory Savings`, `Safety Stock`, `Stock Coverage`, `EOQ`, `Inventory Risk Score` |
| `II-02` | Heatmap | `x24 y224 w760 h250` | `Warehouse`, `ProductCategory`, `Inventory Risk Level`, `StockCoverageDays` |
| `II-03` | Scatter plot | `x808 y224 w768 h250` | `Safety Stock`, `ReorderPoint`, `ReorderQuantity`, `Inventory Risk Score` |
| `II-04` | Waterfall | `x24 y500 w760 h292` | `TotalInventoryCost`, `InventorySavings`, `ExpectedProfitImprovement` |
| `II-05` | Ranking / exception panel | `x808 y500 w768 h292` | `SeriesKey`, `Warehouse`, `InventoryRiskLevel`, `Recommendation`, `SuggestedQuantity` |

## Titles And Labels

- Title: `Inventory Intelligence`.
- Subtitle: replenishment, service level, and cost-to-serve context.
- Keep the KPI labels short and operational.

## Icons And Buttons

- Use an inventory or box icon in the title band.
- Add navigation buttons to product, finance, and summary pages.

## Filters And Slicers

- Slicers: `Warehouse`, `Country`, `ProductCategory`, `Inventory Risk Level`, `HorizonDays`.
- Keep warehouse filtering prominent for inventory users.

## Bookmarks

- `Reorder Today`
- `High Risk`
- `Overstock`

## Tooltips And Drillthrough

- Tooltip: reorder rationale, stockout exposure, and recommended quantity.
- Drillthrough: inventory series detail and warehouse detail pages.

## Dynamic Titles

- Reflect the selected warehouse, category, and horizon in the title.

## Conditional Formatting

- Color the heatmap by risk severity.
- Highlight exceptions and reorder actions in red or amber.

## Interaction Notes

- Keep the exception table prominent because it drives the operational decision.
- Let the scatter plot drive the cost and risk story.

## Export Notes

- The heatmap and exception table must remain legible in export.
