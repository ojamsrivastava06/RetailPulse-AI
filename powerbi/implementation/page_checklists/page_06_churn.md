# Page 06 Customer Churn

## Purpose

Identify churn risk, retention opportunities, and customer-level actions.

## Canvas And Grid

- Canvas: 16:9 widescreen, 1600 x 900 px design base.
- Grid: 8 px spacing system.
- Margins: 24 px outer margin.
- Header band: 96 px.

## Layout

- KPI strip at the top.
- Retention funnel and churn risk matrix in the center.
- Cohort trend, influencer insight, and action table in the lower half.

## Visual Map

| ID | Type | Position | Main Fields |
| --- | --- | --- | --- |
| `CH-01` | KPI cards | `x24 y112 w1552 h92` | `Churn Rate`, `Retention Rate`, `High Risk Customers`, `Average Health Score`, `Customer Lifetime Value`, `VIP Customers` |
| `CH-02` | Funnel | `x24 y224 w760 h250` | `RetentionProbability`, `ChurnProbability`, `HealthBand` |
| `CH-03` | Matrix | `x808 y224 w768 h250` | `RiskCategory`, `HealthBand`, `CustomerSegment`, `ChurnProbability` |
| `CH-04` | Line chart | `x24 y500 w760 h292` | `SnapshotDate`, `Retention Rate`, `Churn Rate` |
| `CH-05` | Key influencers | `x24 y500 w760 h292` | `RiskCategory`, `HealthBand`, `CustomerSegment`, `CustomerHealthScore`, `ExpectedLifetimeValue` |
| `CH-06` | Table | `x808 y500 w768 h292` | `CustomerID`, `RecommendedAction`, `ActionReasoning`, `ExpectedLifetimeValue` |

## Titles And Labels

- Title: `Customer Churn`.
- Subtitle: retention urgency, save-now actions, and customer health.
- Keep the funnel labels business-friendly.

## Icons And Buttons

- Use a retention or shield icon in the title band.
- Add navigation buttons to customer, AI insights, and summary pages.

## Filters And Slicers

- Slicers: `RiskCategory`, `HealthBand`, `CustomerSegment`, `Country`, `ProductCategory`, `RecommendedAction`.
- Keep the risk and health slicers synchronized across customer pages.

## Bookmarks

- `Critical`
- `VIP`
- `Save Now`

## Tooltips And Drillthrough

- Tooltip: risk reason, expected LTV, and action summary.
- Drillthrough: customer profile and action detail pages.

## Dynamic Titles

- Show the selected risk category and health band in the title.

## Conditional Formatting

- Use strong red for critical risk and green for VIP retention states.
- Highlight action urgency in the table and matrix.

## Interaction Notes

- Keep the retention funnel simple and readable.
- The action table should be the last stop before drillthrough.

## Export Notes

- The page should remain useful even without tooltip interaction.
