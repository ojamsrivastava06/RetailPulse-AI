# Page 07 Product Analytics

## Purpose

Understand product winners, slow movers, category contribution, and stock risk.

## Canvas And Grid

- Canvas: 16:9 widescreen, 1600 x 900 px design base.
- Grid: 8 px spacing system.
- Margins: 24 px outer margin.
- Header band: 96 px.

## Layout

- KPI strip at the top.
- Product ranking and category share in the center.
- Pareto curve and risk scatter lower on the page.

## Visual Map

| ID | Type | Position | Main Fields |
| --- | --- | --- | --- |
| `PA-01` | KPI cards | `x24 y112 w1552 h92` | `Category Revenue`, `Top Product Revenue`, `Inventory Risk Score`, `Forecast Demand`, `Inventory Savings` |
| `PA-02` | Bar chart | `x24 y224 w760 h250` | `Product`, `Total Revenue`, `Profit Margin` |
| `PA-03` | Treemap | `x808 y224 w768 h250` | `ProductCategory`, `Category Revenue`, `ABCClass` |
| `PA-04` | Line or area chart | `x24 y500 w760 h292` | `Product`, `Cumulative Revenue`, `Revenue Share` |
| `PA-05` | Scatter plot | `x808 y500 w768 h292` | `Inventory Risk Score`, `Forecast Demand`, `ProductCategory`, `ABCClass` |

## Titles And Labels

- Title: `Product Analytics`.
- Subtitle: winners, slow movers, and assortment mix.
- Keep product labels concise or rely on drillthrough.

## Icons And Buttons

- Use a product or cube icon in the title band.
- Add navigation buttons to inventory and geography pages.

## Filters And Slicers

- Slicers: `Product`, `ProductCategory`, `ABCClass`, `XYZClass`, `SeasonalProduct`, `Country`.
- Keep product and assortment slicers tightly scoped.

## Bookmarks

- `High Value`
- `Slow Moving`
- `Seasonal`

## Tooltips And Drillthrough

- Tooltip: product mix, stockout exposure, and forecast demand.
- Drillthrough: product detail and series detail pages.

## Dynamic Titles

- Reflect the active category and product selection in the title.

## Conditional Formatting

- Use ABC and XYZ class colors consistently.
- Highlight slow movers and dead stock candidates.

## Interaction Notes

- Keep the Pareto curve visible as the main assortment story.
- Let the scatter plot identify risk candidates without overpowering the ranking.

## Export Notes

- Long product names should truncate cleanly in table and bar labels.
