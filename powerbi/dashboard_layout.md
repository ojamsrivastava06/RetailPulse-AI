# RetailPulse Dashboard Layout

## Global Canvas Rules
- Use a 16:9 canvas with an 8 px spacing grid.
- Keep a consistent header band, KPI row, core body, and bottom exception rail.
- Place filters in a left rail or top bar, not across the middle of the page.
- Keep executive pages visually lighter than analyst pages.

## Recommended Layout Patterns
| Page | Layout Pattern | Primary Placement | Notes |
| --- | --- | --- | --- |
| `Executive Dashboard` | KPI strip, trend center, risk rail | KPI cards top, trend and map middle, exceptions bottom | Use as the landing page |
| `Sales Analytics` | Trend-first layout | Trend and mix charts centered, product ranking on the right | Keep slicers compact |
| `Customer Intelligence` | Cluster and segment layout | Scatter or cohort view center, segment summary right, details bottom | Emphasize value and loyalty |
| `Demand Forecasting` | Model comparison layout | Actual vs forecast top, model ranking right, error analysis bottom | Keep confidence intervals visible |
| `Inventory Intelligence` | Operations control layout | Risk heatmap center, cost bridge left, action table bottom | Show reorder urgency first |
| `Customer Churn` | Retention action layout | Risk matrix top, funnel center, customer action list bottom | Prioritize save-now lists |
| `Product Analytics` | Assortment analysis layout | Product ranking center, share treemap right, stock flags bottom | Separate winners from dead stock |
| `Geographic Analytics` | Map-led layout | Map left, country ranking right, market summary bottom | Use fewer visuals to keep clarity |
| `Financial Analytics` | Bridge and variance layout | Waterfall top, margin trend center, cost drivers bottom | Finance should see where value moved |
| `KPI Cockpit` | Single-metric layout | Dynamic KPI card top, comparison chart center, target rail bottom | Designed for rapid metric switching |
| `AI Insights` | Driver-explanation layout | Key influencers top, decomposition tree center, explanation table bottom | Keep the story explainable |
| `Executive Summary` | Board-pack layout | High-level cards top, brief trend center, action list bottom | Minimal controls, maximum readability |

## Page-Specific Guidance
- `Executive Dashboard`: use one strong revenue trend, one geographic summary, and one risk table.
- `Sales Analytics`: keep product and country rankings visible without forcing too much scrolling.
- `Customer Intelligence`: reserve the largest visual for the clustering or cohort pattern.
- `Demand Forecasting`: show model quality, not just the forecast line.
- `Inventory Intelligence`: keep the action table prominent so users can reorder immediately.
- `Customer Churn`: give the customer action list a fixed place and make it easy to drill through.
- `Product Analytics`: balance product ranking with stock risk.
- `Geographic Analytics`: let map visuals breathe; avoid placing too many tiny labels nearby.
- `Financial Analytics`: prioritize the waterfall and margin driver table.
- `KPI Cockpit`: dedicate most of the page to the selected KPI and its target.
- `AI Insights`: use the explanation table as the closing element, not the opening element.
- `Executive Summary`: keep the page sparse enough to be board-friendly.
