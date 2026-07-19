# RetailPulse Report Specification

## Report Design Standards
- Build the report for 16:9 presentation, executive review, and analyst drilldown.
- Keep every page tied to one business question.
- Use the same KPI language across all pages so metrics stay consistent.
- Use bookmarks, drillthrough, and field parameters only where they improve decision speed.

## 1. Executive Dashboard
- Purpose: provide a one-screen leadership view of revenue, profit, customer risk, inventory risk, and forecast quality.
- KPIs: `Total Revenue`, `Gross Profit`, `Profit Margin`, `Churn Rate`, `Inventory Risk Score`, `Forecast Accuracy %`, `Inventory Savings`.
- Charts: KPI strip, revenue trend line, country map, profit waterfall, risk exception table.
- Filters: `Date`, `Country`, `ProductCategory`, `Customer Segment`, `Warehouse`.
- Drillthrough: sales, customer, product, inventory, and churn detail pages.
- Bookmarks: `Executive Summary`, `Risk Focus`, `Opportunity Focus`.
- Tooltips: compact KPI trend card with delta, variance, and status.
- Business insights: show whether growth, service, and retention are moving in the same direction.

## 2. Sales Analytics
- Purpose: analyze revenue growth, basket quality, product mix, and order cadence.
- KPIs: `Total Revenue`, `Total Orders`, `Average Order Value`, `Gross Profit`, `Revenue Growth %`, `Running Total`.
- Charts: line chart, area chart, ribbon chart, waterfall, top products bar, sales matrix.
- Filters: `Date`, `Country`, `ProductCategory`, `Product`, `Customer Segment`.
- Drillthrough: product detail, customer detail, and country detail pages.
- Bookmarks: `Monthly View`, `Quarterly View`, `Rolling 90 Days`.
- Tooltips: mini trend by product or country, plus contribution percent.
- Business insights: identify growth pockets, margin erosion, and order concentration.

## 3. Customer Intelligence
- Purpose: understand customer value, segment mix, and loyalty concentration.
- KPIs: `Total Customers`, `Average CLV`, `Revenue per Customer`, `VIP Customers`, `High Risk Customers`, `Average Health Score`.
- Charts: recency-frequency scatter, segment treemap, customer matrix, top customer bar, cohort table.
- Filters: `Customer Segment`, `Customer Tier`, `Country`, `ProductCategory`, recency band.
- Drillthrough: customer profile page and retention action page.
- Bookmarks: `Champions`, `At Risk`, `New vs Loyal`.
- Tooltips: customer scorecard with CLV, health, risk, and recommended action.
- Business insights: identify where loyalty is concentrated and where churn is starting to rise.

## 4. Demand Forecasting
- Purpose: compare model quality and plan future demand by product, geography, and horizon.
- KPIs: `Forecast Revenue`, `Forecast Demand`, `Forecast Accuracy %`, `MAPE`, `Forecast Error`, best model name.
- Charts: actual vs forecast line, prediction interval area, model comparison bar, residual histogram, small multiples by product or country.
- Filters: `Model`, `HorizonDays`, `Product`, `Country`, `ProductCategory`.
- Drillthrough: forecast series detail and model comparison detail.
- Bookmarks: `Current Horizon`, `Long Horizon`, `Model Comparison`.
- Tooltips: forecast value, confidence band, and error summary.
- Business insights: identify which series are stable enough for planning and which need manual review.

## 5. Inventory Intelligence
- Purpose: manage stock coverage, replenishment, cost, and risk.
- KPIs: `Inventory Cost`, `Inventory Savings`, `Safety Stock`, `Stock Coverage`, `EOQ`, `Inventory Risk Score`, `Inventory Health Score`.
- Charts: risk heatmap, safety stock vs reorder point scatter, cost waterfall, warehouse bar, exception table.
- Filters: `Warehouse`, `Country`, `ProductCategory`, `Inventory Risk Level`, `HorizonDays`.
- Drillthrough: inventory series detail and warehouse detail pages.
- Bookmarks: `Reorder Today`, `High Risk`, `Overstock`.
- Tooltips: reorder rationale, stockout exposure, and recommended quantity.
- Business insights: show where to replenish first and where stock should be reduced.

## 6. Customer Churn
- Purpose: identify churn risk, retention opportunities, and account-level actions.
- KPIs: `Churn Rate`, `Retention Rate`, `High Risk Customers`, `Average Health Score`, `Customer Lifetime Value`, `Recommended Action Count`.
- Charts: retention funnel, churn funnel, risk matrix, retention cohort line, key influencers.
- Filters: `RiskCategory`, `HealthBand`, `CustomerSegment`, `Country`, `ProductCategory`, `RecommendedAction`.
- Drillthrough: customer profile and action detail pages.
- Bookmarks: `Critical`, `VIP`, `Save Now`.
- Tooltips: risk reason, expected LTV, and action summary.
- Business insights: surface the smallest set of customers that can change the largest retention outcome.

## 7. Product Analytics
- Purpose: understand product winners, slow movers, category contribution, and risk.
- KPIs: `Category Revenue`, `Top Product Revenue`, `Inventory Risk Score`, `Forecast Demand`, dead stock count, margin.
- Charts: treemap, product bar ranking, ribbon chart, Pareto curve, scatter value versus risk.
- Filters: `Product`, `ProductCategory`, `ABCClass`, `XYZClass`, `SeasonalProduct`, `Country`.
- Drillthrough: product detail and series detail pages.
- Bookmarks: `High Value`, `Slow Moving`, `Seasonal`.
- Tooltips: product mix, stockout exposure, and forecast demand.
- Business insights: show which products deserve more inventory, more promotion, or liquidation.

## 8. Geographic Analytics
- Purpose: review demand, revenue, churn, and inventory by market.
- KPIs: `Country Revenue`, `Total Orders`, `Churn Rate`, `Inventory Cost`, `Forecast Demand`, `Inventory Savings`.
- Charts: map, filled map, country bar ranking, geographic matrix, bubble risk comparison.
- Filters: `Country`, `Warehouse`, `ProductCategory`, `Customer Segment`.
- Drillthrough: country detail page.
- Bookmarks: `Domestic`, `Europe`, `International`.
- Tooltips: country profile with revenue, risk, and stock coverage.
- Business insights: reveal market concentration, service gaps, and regional growth potential.

## 9. Financial Analytics
- Purpose: connect revenue, profit, inventory cost, and customer value into a finance lens.
- KPIs: `Total Revenue`, `Gross Profit`, `Profit Margin`, `Inventory Cost`, `Inventory Savings`, `Revenue per Customer`.
- Charts: waterfall, margin trend line, category profit matrix, cost driver bar, revenue versus profit scatter.
- Filters: `Date`, `Country`, `ProductCategory`, `Customer Segment`, `Model`.
- Drillthrough: product, customer, and inventory cost pages.
- Bookmarks: `Margin Pressure`, `Growth Invest`, `Cost Reduction`.
- Tooltips: cost bridge and margin explanation.
- Business insights: show where profit is leaking and where savings can be reinvested.

## 10. KPI Cockpit
- Purpose: provide a configurable operations cockpit for one metric at a time.
- KPIs: selected `Dynamic KPI`, `Variance`, `Target Achievement %`, current value, trend, and status.
- Charts: large KPI card, gauge, comparison bar, sparklines, target table.
- Filters: `KPI Selector`, `Target Period`, `Scenario`, `Date`.
- Drillthrough: the selected KPI source page.
- Bookmarks: `Revenue Mode`, `Customer Mode`, `Inventory Mode`.
- Tooltips: KPI definition, target logic, and latest change drivers.
- Business insights: create one reusable board for executives who want to switch context quickly.

## 11. AI Insights
- Purpose: expose model drivers, anomalies, and recommendation logic.
- KPIs: top driver strength, recommendation count, anomaly count, model confidence, portfolio risk.
- Charts: key influencers, decomposition tree, anomaly line, driver scatter, explanation table.
- Filters: `Entity`, `Metric`, `Date`, `Scenario`.
- Drillthrough: driver detail and entity-level detail pages.
- Bookmarks: `Churn Drivers`, `Inventory Drivers`, `Revenue Drivers`.
- Tooltips: explanation snippet, SHAP-style summary, and recommended action.
- Business insights: explain why the metric changed, not just that it changed.

## 12. Executive Summary
- Purpose: provide a board-ready summary of what happened, what changed, and what should happen next.
- KPIs: `Total Revenue`, `Gross Profit`, `Churn Rate`, `Inventory Risk Score`, `Forecast Accuracy %`, `Inventory Savings`.
- Charts: summary cards, single line trend, compact waterfall, action summary table.
- Filters: minimal and preset by bookmark.
- Drillthrough: optional links to the detailed pages.
- Bookmarks: `Board Pack`, `Ops Pack`, `Finance Pack`.
- Tooltips: concise status narrative for each KPI.
- Business insights: support a final decision conversation with a very small number of actions.
