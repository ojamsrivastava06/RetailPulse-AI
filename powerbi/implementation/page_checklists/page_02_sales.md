# Page 02 Sales Analytics

## Purpose

Analyze revenue growth, basket quality, product mix, and order cadence.

## Canvas And Grid

- Canvas: 16:9 widescreen, 1600 x 900 px design base.
- Grid: 8 px spacing system.
- Margins: 24 px outer margin.
- Header band: 96 px.

## Layout

- KPI strip across the top.
- Revenue trend and mix visuals in the center.
- Ranking and detail matrix in the lower half.

## Visual Map

| ID | Type | Position | Main Fields |
| --- | --- | --- | --- |
| `SA-01` | KPI cards | `x24 y112 w1552 h92` | `Total Revenue`, `Total Orders`, `Average Order Value`, `Gross Profit`, `Revenue Growth %`, `Running Total` |
| `SA-02` | Line chart | `x24 y224 w1040 h250` | `DimDate[Date]`, `Total Revenue`, `Monthly Revenue`, `Quarterly Revenue` |
| `SA-03` | Bar chart | `x1088 y224 w488 h250` | `Product`, `Top Product Revenue`, `Category Revenue` |
| `SA-04` | Ribbon chart | `x24 y500 w760 h292` | `ProductCategory`, `Total Revenue`, `Year` |
| `SA-05` | Matrix | `x808 y500 w768 h292` | `Country`, `ProductCategory`, `Total Revenue`, `Profit Margin`, `Average Order Value` |

## Titles And Labels

- Title: `Sales Analytics`.
- Subtitle: growth, mix, and basket performance for the active filters.
- Use concise axis labels and avoid cluttering the product ranking.

## Icons And Buttons

- Use a trend icon and a cart or revenue icon in the title band.
- Add navigator buttons for adjacent pages and a back button to summary.

## Filters And Slicers

- Slicers: `Date`, `Country`, `ProductCategory`, `Product`, `Customer Segment`.
- Keep the page focused on sales context only.

## Bookmarks

- `Monthly View`
- `Quarterly View`
- `Rolling 90 Days`

## Tooltips And Drillthrough

- Tooltip: mini trend and contribution percent.
- Drillthrough: product detail, customer detail, and country detail.

## Dynamic Titles

- Show the current date range and active product or country context.

## Conditional Formatting

- Highlight top products, margin erosion, and AOV movement.
- Use diverging colors only on the matrix and ranking table.

## Interaction Notes

- Keep cross-highlighting on for the trend and mix visuals.
- Prevent the matrix from overpowering the trend line.

## Export Notes

- Ensure the line chart, ribbon chart, and matrix remain legible in PDF export.
