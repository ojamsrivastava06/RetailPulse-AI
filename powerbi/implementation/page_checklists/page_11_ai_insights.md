# Page 11 AI Insights

## Purpose

Expose model drivers, anomalies, and recommendation logic.

## Canvas And Grid

- Canvas: 16:9 widescreen, 1600 x 900 px design base.
- Grid: 8 px spacing system.
- Margins: 24 px outer margin.
- Header band: 96 px.

## Layout

- Driver visuals at the top.
- Root-cause visual in the center.
- Explanations and anomalies in the lower band.

## Visual Map

| ID | Type | Position | Main Fields |
| --- | --- | --- | --- |
| `AI-01` | KPI cards | `x24 y112 w1552 h92` | `High Risk Customers`, `High Risk Inventory Series`, `Forecast Accuracy %`, `Recommended Action Count` |
| `AI-02` | Key influencers | `x24 y224 w760 h250` | `RiskCategory`, `CustomerHealthScore`, `InventoryRiskScore`, `ChurnProbability` |
| `AI-03` | Decomposition tree | `x808 y224 w768 h250` | `Total Revenue`, `Gross Profit`, `Churn Rate`, `Inventory Savings` |
| `AI-04` | Anomaly line | `x24 y500 w760 h292` | `DimDate[Date]`, `Total Revenue`, `Churn Rate`, `Inventory Risk Score` |
| `AI-05` | Driver scatter | `x24 y500 w760 h292` | `ChurnProbability`, `ExpectedLifetimeValue`, `CustomerHealthScore`, `RiskCategory` |
| `AI-06` | Explanation table | `x808 y500 w768 h292` | `Entity`, `Metric`, `Reason`, `RecommendedAction` |

## Titles And Labels

- Title: `AI Insights`.
- Subtitle: drivers, anomalies, and recommended actions.
- Keep the explanatory text short and actionable.

## Icons And Buttons

- Use an insights or spark icon in the title band.
- Add navigation buttons to churn, inventory, and summary pages.

## Filters And Slicers

- Slicers: `Entity`, `Metric`, `Date`, `Scenario`.
- Keep diagnostic slicers page-specific.

## Bookmarks

- `Churn Drivers`
- `Inventory Drivers`
- `Revenue Drivers`

## Tooltips And Drillthrough

- Tooltip: explanation snippet, driver summary, and action cue.
- Drillthrough: driver detail and entity-level detail pages.

## Dynamic Titles

- Show the current entity and metric focus in the title.

## Conditional Formatting

- Highlight the most important drivers and anomalies with strong contrast.
- Keep explanatory text readable on a light or dark theme.

## Interaction Notes

- The explanation table should close the narrative, not open it.
- Do not let the driver visuals become too technical for executives.

## Export Notes

- The page must still make sense if the user exports without interacting.
