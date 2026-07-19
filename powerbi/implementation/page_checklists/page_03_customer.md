# Page 03 Customer Intelligence

## Purpose

Show customer value, segment mix, loyalty concentration, and early churn pressure.

## Canvas And Grid

- Canvas: 16:9 widescreen, 1600 x 900 px design base.
- Grid: 8 px spacing system.
- Margins: 24 px outer margin.
- Header band: 96 px.

## Layout

- KPI strip at the top.
- Core behavioral visual in the center.
- Segment and customer detail visuals across the lower half.

## Visual Map

| ID | Type | Position | Main Fields |
| --- | --- | --- | --- |
| `CI-01` | KPI cards | `x24 y112 w1552 h92` | `Total Customers`, `Average CLV`, `Revenue per Customer`, `VIP Customers`, `High Risk Customers`, `Average Health Score` |
| `CI-02` | Scatter plot | `x24 y224 w760 h250` | `Recency`, `Frequency`, `Monetary`, `Segment` |
| `CI-03` | Treemap | `x808 y224 w768 h250` | `Segment`, `CustomerTier`, `Revenue`, `Customer Count` |
| `CI-04` | Bar chart | `x24 y500 w760 h292` | `CustomerID`, `PredictedCLV`, `CustomerHealthScore` |
| `CI-05` | Matrix | `x808 y500 w768 h292` | `Segment`, `Country`, `Average CLV`, `Churn Rate`, `Retention Rate` |

## Titles And Labels

- Title: `Customer Intelligence`.
- Subtitle: segment mix, value concentration, and retention pressure.
- Keep labels short and business-facing.

## Icons And Buttons

- Use a customer or profile icon in the title band.
- Add navigation buttons for `Churn`, `Sales`, and `Summary`.

## Filters And Slicers

- Slicers: `Customer Segment`, `Country`, `ProductCategory`, recency band.
- Keep customer and retention slicers synchronized across customer-related pages.

## Bookmarks

- `Champions`
- `At Risk`
- `New vs Loyal`

## Tooltips And Drillthrough

- Tooltip: customer scorecard with CLV, health, risk, and recommended action.
- Drillthrough: customer profile and retention action pages.

## Dynamic Titles

- Show the active segment, country, and health band in the title or subtitle.

## Conditional Formatting

- Use strong contrast for VIP and high-risk states.
- Apply traffic-light formatting to segment contribution and retention metrics.

## Interaction Notes

- Keep cross-highlighting on for the scatter plot and treemap.
- Let the customer ranking table filter the detail matrix.

## Export Notes

- Keep the scatter plot labels readable in presentation mode.
- The page should remain understandable without hover interaction.
