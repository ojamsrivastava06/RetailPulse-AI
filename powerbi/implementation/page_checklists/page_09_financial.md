# Page 09 Financial Analytics

## Purpose

Connect revenue, profit, inventory cost, and customer value into a finance lens.

## Canvas And Grid

- Canvas: 16:9 widescreen, 1600 x 900 px design base.
- Grid: 8 px spacing system.
- Margins: 24 px outer margin.
- Header band: 96 px.

## Layout

- Waterfall and margin narrative at the top.
- Margin trend in the center.
- Cost drivers and value scatter in the lower half.

## Visual Map

| ID | Type | Position | Main Fields |
| --- | --- | --- | --- |
| `FA-01` | KPI cards | `x24 y112 w1552 h92` | `Total Revenue`, `Gross Profit`, `Profit Margin`, `Inventory Cost`, `Inventory Savings`, `Revenue per Customer` |
| `FA-02` | Waterfall | `x24 y224 w760 h250` | `Gross Profit`, `Inventory Cost`, `Inventory Savings`, `Variance` |
| `FA-03` | Line chart | `x808 y224 w768 h250` | `DimDate[Date]`, `Profit Margin`, `Gross Profit` |
| `FA-04` | Matrix / cost driver bar panel | `x24 y500 w760 h292` | `ProductCategory`, `Gross Profit`, `Profit Margin`, `Inventory Cost` |
| `FA-05` | Scatter plot | `x808 y500 w768 h292` | `Total Revenue`, `Gross Profit`, `Inventory Cost`, `Country` |

## Titles And Labels

- Title: `Financial Analytics`.
- Subtitle: cost bridge, margin pressure, and value creation.
- Keep finance labels precise and consistent.

## Icons And Buttons

- Use a finance or chart icon in the title band.
- Add navigation buttons to inventory, sales, and summary pages.

## Filters And Slicers

- Slicers: `Date`, `Country`, `ProductCategory`, `Customer Segment`, `Model`.
- Keep the finance lens aligned with the active business context.

## Bookmarks

- `Margin Pressure`
- `Growth Invest`
- `Cost Reduction`

## Tooltips And Drillthrough

- Tooltip: cost bridge and margin explanation.
- Drillthrough: product, customer, and inventory cost pages.

## Dynamic Titles

- Reflect the current period and margin story in the title.

## Conditional Formatting

- Use red for margin compression and green for positive cost control.
- Highlight the largest cost drivers in the matrix.

## Interaction Notes

- Keep the waterfall at the front of the financial story.
- Let the scatter plot show where profit and cost diverge.

## Export Notes

- Finance leaders should be able to read this page without hovering.
