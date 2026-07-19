# Visual Inventory

## Usage

This file maps each visual ID to the intended fields, behavior, and export treatment. Page positions live in the page checklist files.

## Page 01 Executive Dashboard

| ID | Visual Type | Data Fields | Axis / Legend | Tooltip / Filters | Conditional Formatting | Sorting | Interactions / Cross-H / Cross-F / Export |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ED-01` | KPI cards | `Total Revenue`, `Gross Profit`, `Profit Margin`, `Churn Rate`, `Inventory Risk Score`, `Forecast Accuracy %`, `Inventory Savings` | None | Tooltip shows delta, variance, and status; filters inherit `Date`, `Country`, `ProductCategory`, `Customer Segment`, `Warehouse` | Use green/amber/red status colors by variance and risk | Business priority order | No cross-highlight; drillthrough from the current filter context; export yes |
| `ED-02` | Line chart | `DimDate[Date]`, `Total Revenue`, `Running Total`, `Monthly Revenue` | Axis: `Date`; legend optional for scenario if needed | Tooltip shows revenue, growth, and rolling total; filters inherit page slicers | Accent line color with subdued gridlines | Chronological | Cross-highlight on; cross-filter to map and table; export yes |
| `ED-03` | Map | `Country`, `Country Revenue`, `Churn Rate`, `Inventory Risk Score` | Axis: `Country`; legend: risk color scale | Tooltip shows forecast accuracy and inventory savings; filters inherit geography slicers | Use bubble/choropleth intensity by risk | Revenue descending or risk severity | Cross-highlight on; cross-filter to exception table; export yes |
| `ED-04` | Waterfall | `Gross Profit`, `Inventory Cost`, `Inventory Savings`, `Variance` | Axis: bridge categories; legend none | Tooltip shows profit margin and cost context; filters inherit page slicers | Use green for gains and red for losses | Contribution order | Cross-filter on; cross-highlight limited; export yes |
| `ED-05` | Table | `RiskCategory`, `InventoryRiskLevel`, `Forecast Accuracy %`, `RecommendedAction`, `ActionReasoning` | Rows by risk group; legend none | Tooltip shows action detail; filters inherit all page slicers | Red/amber/green on severity and recommendation priority | Sort by risk then variance | Cross-filter on; cross-highlight from table only; export yes |

## Page 02 Sales Analytics

| ID | Visual Type | Data Fields | Axis / Legend | Tooltip / Filters | Conditional Formatting | Sorting | Interactions / Cross-H / Cross-F / Export |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `SA-01` | KPI cards | `Total Revenue`, `Total Orders`, `Average Order Value`, `Gross Profit`, `Revenue Growth %`, `Running Total` | None | Tooltip shows month-over-month and year-over-year deltas; filters inherit sales slicers | Use revenue and margin colors consistently | Revenue-first order | No cross-highlight; export yes |
| `SA-02` | Line chart | `DimDate[Date]`, `Total Revenue`, `Monthly Revenue`, `Quarterly Revenue` | Axis: `Date`; legend optional for period toggle | Tooltip shows growth rates and contribution; filters inherit `Date`, `Country`, `ProductCategory`, `Product` | Strong accent line and muted reference grid | Chronological | Cross-highlight on; cross-filter to product bar and matrix; export yes |
| `SA-03` | Bar chart | `Product`, `Top Product Revenue`, `Category Revenue`, `Profit Margin` | Axis: `Product`; legend none | Tooltip shows average order value and country context; filters inherit sales slicers | Highlight top 5 products and low-margin items | Revenue descending | Cross-highlight on; cross-filter to matrix; export yes |
| `SA-04` | Ribbon chart | `ProductCategory`, `Total Revenue`, `Year` | Axis: `Year`; legend: `ProductCategory` | Tooltip shows share and movement; filters inherit `Date` and `Category` | Use restrained categorical palette | Sort by year then revenue share | Cross-highlight on; cross-filter to line chart; export yes |
| `SA-05` | Matrix | `Country`, `ProductCategory`, `Total Revenue`, `Profit Margin`, `Average Order Value` | Rows: `Country`; columns: `ProductCategory` | Tooltip shows revenue growth and basket quality; filters inherit all sales slicers | Heatmap style on margin and AOV | Sort by revenue or margin | Cross-filter on; cross-highlight from ranking visuals; export yes |

## Page 03 Customer Intelligence

| ID | Visual Type | Data Fields | Axis / Legend | Tooltip / Filters | Conditional Formatting | Sorting | Interactions / Cross-H / Cross-F / Export |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `CI-01` | KPI cards | `Total Customers`, `Average CLV`, `Revenue per Customer`, `VIP Customers`, `High Risk Customers`, `Average Health Score` | None | Tooltip shows risk band and recommended action; filters inherit customer slicers | Use VIP, watch, and critical color states | Value-first order | No cross-highlight; export yes |
| `CI-02` | Scatter plot | `Recency`, `Frequency`, `Monetary`, `Segment` | X: `Recency`, Y: `Frequency`, Size: `Monetary`, Legend: `Segment` | Tooltip shows CLV, health score, and risk category; filters inherit `Customer Segment`, `Country`, `ProductCategory` | Bubble color by segment or risk | Recency ascending if sorted by quadrant | Cross-highlight on; cross-filter to treemap and matrix; export yes |
| `CI-03` | Treemap | `Segment`, `CustomerTier`, `Total Revenue`, `Total Customers` | Group by `Segment` and `CustomerTier` | Tooltip shows health score and churn rate; filters inherit customer slicers | Use segment colors with explicit labels | Revenue descending | Cross-highlight on; cross-filter to ranking table; export yes |
| `CI-04` | Bar chart | `CustomerID`, `PredictedCLV`, `CustomerHealthScore` | Axis: `CustomerID`; legend none | Tooltip shows risk category and action summary; filters inherit segment and country slicers | Highlight VIP and at-risk customers | Predicted CLV descending | Cross-highlight on; cross-filter to matrix; export yes |
| `CI-05` | Matrix | `Segment`, `Country`, `Average CLV`, `Churn Rate`, `Retention Rate` | Rows: `Segment`; columns: `Country` or metric labels | Tooltip shows contribution and risk; filters inherit page slicers | Use color scale for CLV and retention | Sort by CLV or churn | Cross-filter on; cross-highlight from scatter and treemap; export yes |

## Page 04 Demand Forecasting

| ID | Visual Type | Data Fields | Axis / Legend | Tooltip / Filters | Conditional Formatting | Sorting | Interactions / Cross-H / Cross-F / Export |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `DF-01` | KPI cards | `Forecast Revenue`, `Forecast Demand`, `Forecast Accuracy %`, `MAPE`, `Forecast Error`, `Best Model Count` | None | Tooltip shows model and horizon context; filters inherit forecasting slicers | Use accuracy threshold colors | Accuracy-first order | No cross-highlight; export yes |
| `DF-02` | Line chart | `Date`, `Actual`, `Forecast`, `Lower95`, `Upper95` | Axis: `Date`; legend: actual vs forecast series | Tooltip shows residual, confidence band, and forecast level; filters inherit `Model`, `HorizonDays`, `Product`, `Country` | Shaded prediction interval and accent forecast line | Chronological | Cross-highlight on; cross-filter to model ranking and residual view; export yes |
| `DF-03` | Bar chart | `Model`, `Forecast Accuracy %`, `MAPE`, `Forecast Error` | Axis: `Model`; legend none | Tooltip shows fold and configuration context; filters inherit page slicers | Highlight best model and threshold misses | Accuracy descending | Cross-highlight on; cross-filter to line and matrix; export yes |
| `DF-04` | Residual chart | `Residual`, `ResidualStd`, `Model` | Axis: residual bins or standardized residuals; legend optional by model | Tooltip shows bias and error spread; filters inherit page slicers | Use diverging colors for positive and negative residuals | Bin or value order | Cross-highlight limited; cross-filter to model ranking; export yes |
| `DF-05` | Matrix | `Product`, `Country`, `HorizonDays`, `Forecast Demand`, `Forecast Revenue` | Rows: `Product`; columns: `HorizonDays` or `Country` | Tooltip shows accuracy and model context; filters inherit all forecasting slicers | Use heatmap on demand or revenue | Sort by horizon or demand | Cross-filter on; cross-highlight from line and model bar; export yes |

## Page 05 Inventory Intelligence

| ID | Visual Type | Data Fields | Axis / Legend | Tooltip / Filters | Conditional Formatting | Sorting | Interactions / Cross-H / Cross-F / Export |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `II-01` | KPI cards | `Inventory Cost`, `Inventory Savings`, `Safety Stock`, `Stock Coverage`, `EOQ`, `Inventory Risk Score` | None | Tooltip shows replenishment rationale and risk; filters inherit `Warehouse`, `Country`, `ProductCategory`, `HorizonDays` | Use risk colors and savings emphasis | Cost and risk priority order | No cross-highlight; export yes |
| `II-02` | Heatmap | `Warehouse`, `ProductCategory`, `Inventory Risk Level`, `StockCoverageDays` | Rows: `Warehouse`; columns: `ProductCategory`; legend: risk heat | Tooltip shows reorder point and coverage; filters inherit inventory slicers | Use strong fill scale for risk severity | Risk then coverage | Cross-highlight on; cross-filter to scatter and table; export yes |
| `II-03` | Scatter plot | `Safety Stock`, `ReorderPoint`, `ReorderQuantity`, `Inventory Risk Score` | X: `Safety Stock`; Y: `ReorderPoint`; Size: `ReorderQuantity`; Legend: `InventoryRiskLevel` | Tooltip shows suggested quantity, stockout risk, and inventory savings; filters inherit page slicers | Bubble color by risk level | Sort by risk or quantity | Cross-highlight on; cross-filter to heatmap and table; export yes |
| `II-04` | Waterfall | `TotalInventoryCost`, `InventorySavings`, `ExpectedProfitImprovement`, `PotentialRevenueLoss` | Axis: cost bridge categories; legend none | Tooltip shows service level and coverage context; filters inherit page slicers | Green for savings, red for losses | Contribution order | Cross-highlight limited; cross-filter to exception table; export yes |
| `II-05` | Ranking / exception table panel | `Warehouse`, `InventoryRiskLevel`, `Recommendation`, `SuggestedQuantity`, `SeriesKey` | Axis: `Warehouse` or `SeriesKey`; legend none | Tooltip shows `BusinessExplanation` and `TriggerMetric`; filters inherit `Warehouse`, `Country`, `ProductCategory` | Priority and risk severity formatting | Sort by priority then risk level | Cross-filter on; cross-highlight from heatmap and scatter; export yes |

## Page 06 Customer Churn

| ID | Visual Type | Data Fields | Axis / Legend | Tooltip / Filters | Conditional Formatting | Sorting | Interactions / Cross-H / Cross-F / Export |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `CH-01` | KPI cards | `Churn Rate`, `Retention Rate`, `High Risk Customers`, `Average Health Score`, `Customer Lifetime Value`, `VIP Customers` | None | Tooltip shows risk band and action counts; filters inherit churn slicers | Use severity colors for churn and retention | Risk-first order | No cross-highlight; export yes |
| `CH-02` | Funnel | `HealthBand`, `Total Customers`, `Churn Probability`, `Retention Probability` | Axis: health stage; legend none | Tooltip shows churn rate and LTV; filters inherit `RiskCategory`, `HealthBand`, `CustomerSegment`, `Country` | Use red-to-green progression | Stage order from healthy to critical | Cross-highlight on; cross-filter to matrix and line chart; export yes |
| `CH-03` | Matrix | `RiskCategory`, `HealthBand`, `CustomerSegment`, `ChurnProbability` | Rows: risk/health; columns: segment | Tooltip shows recommended action and expected LTV; filters inherit page slicers | Red/amber/green heatmap | Risk severity order | Cross-filter on; cross-highlight from funnel and line chart; export yes |
| `CH-04` | Line chart | `SnapshotDate`, `Retention Rate`, `Churn Rate` | Axis: `SnapshotDate`; legend: rate series | Tooltip shows high-risk customer count; filters inherit time and segment slicers | Use retention and churn contrast colors | Chronological | Cross-highlight on; cross-filter to table and matrix; export yes |
| `CH-05` | Key influencers / action rail | `RiskCategory`, `HealthBand`, `CustomerSegment`, `CustomerHealthScore`, `ExpectedLifetimeValue` | Analyze: churn or retention; explain by driver fields | Tooltip shows top drivers and action cues; filters inherit page slicers | Highlight strongest positive and negative drivers | Driver strength order | Cross-highlight on; cross-filter to action table; export yes |
| `CH-06` | Action table | `CustomerID`, `RecommendedAction`, `ActionReasoning`, `ExpectedLifetimeValue`, `ProbabilityConfidence` | Rows: customer; legend none | Tooltip shows health status and next purchase probability; filters inherit page slicers | Priority and risk-based formatting | Priority then LTV | Cross-filter on; cross-highlight from all visual states; export yes |

## Page 07 Product Analytics

| ID | Visual Type | Data Fields | Axis / Legend | Tooltip / Filters | Conditional Formatting | Sorting | Interactions / Cross-H / Cross-F / Export |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `PA-01` | KPI cards | `Category Revenue`, `Top Product Revenue`, `Inventory Risk Score`, `Forecast Demand`, `Inventory Savings` | None | Tooltip shows category and assortment context; filters inherit product slicers | Use product and risk colors | Revenue-first order | No cross-highlight; export yes |
| `PA-02` | Bar chart | `Product`, `Total Revenue`, `Profit Margin` | Axis: `Product`; legend none | Tooltip shows stockout exposure and forecast demand; filters inherit `ProductCategory`, `ABCClass`, `XYZClass`, `Country` | Highlight winners, slow movers, and margin erosion | Revenue descending | Cross-highlight on; cross-filter to treemap and scatter; export yes |
| `PA-03` | Treemap | `ProductCategory`, `Category Revenue`, `ABCClass`, `Total Products` | Group by `ProductCategory`; legend by class | Tooltip shows share of revenue and class mix; filters inherit page slicers | Use class colors consistently | Revenue descending | Cross-highlight on; cross-filter to ranking bar; export yes |
| `PA-04` | Pareto / ribbon panel | `Product`, `Cumulative Revenue`, `Revenue Share`, `Year` | Axis: `Product` or `Year`; legend: revenue share or category | Tooltip shows contribution and movement; filters inherit product slicers | Use cumulative curve accent and muted share colors | Pareto order or year order | Cross-highlight on; cross-filter to scatter and bar; export yes |
| `PA-05` | Scatter plot | `Inventory Risk Score`, `Forecast Demand`, `ABCClass`, `XYZClass` | X: risk score; Y: forecast demand; Size: revenue or stock value; Legend: class | Tooltip shows seasonal flag and dead stock candidate state; filters inherit page slicers | Bubble color by class or seasonal flag | Sort by risk or forecast demand | Cross-highlight on; cross-filter to bar and treemap; export yes |

## Page 08 Geographic Analytics

| ID | Visual Type | Data Fields | Axis / Legend | Tooltip / Filters | Conditional Formatting | Sorting | Interactions / Cross-H / Cross-F / Export |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GA-01` | KPI cards | `Country Revenue`, `Total Orders`, `Churn Rate`, `Inventory Cost`, `Forecast Demand`, `Inventory Savings` | None | Tooltip shows market concentration and service context; filters inherit geography slicers | Use region-level risk colors | Revenue-first order | No cross-highlight; export yes |
| `GA-02` | Map / filled map toggle | `Country`, `Country Revenue`, `Churn Rate`, `Inventory Risk Score` | Axis: `Country`; legend: intensity or bubble size | Tooltip shows forecast accuracy and stock coverage; filters inherit `Country`, `Warehouse`, `ProductCategory` | Use map intensity and bubble size carefully | Revenue or risk severity | Cross-highlight on; cross-filter to ranking bar and matrix; export yes |
| `GA-03` | Bar chart | `Country`, `Country Revenue`, `Profit Margin` | Axis: `Country`; legend none | Tooltip shows total orders and retention rate; filters inherit page slicers | Highlight top markets and margin pressure | Revenue descending | Cross-highlight on; cross-filter to map and matrix; export yes |
| `GA-04` | Matrix | `Country`, `Warehouse`, `ProductCategory`, `Total Revenue`, `Inventory Cost` | Rows: `Country`; columns: `Warehouse` or `ProductCategory` | Tooltip shows churn and stock coverage; filters inherit page slicers | Heatmap on revenue and cost | Sort by revenue or cost | Cross-filter on; cross-highlight from map and ranking bar; export yes |
| `GA-05` | Bubble chart | `Country Revenue`, `Churn Rate`, `Inventory Risk Score`, `Forecast Accuracy %` | X: revenue; Y: churn; Size: inventory risk; Legend: region | Tooltip shows service coverage and forecast priority; filters inherit page slicers | Use strong region colors | Sort by revenue or risk | Cross-highlight on; cross-filter to bar and matrix; export yes |

## Page 09 Financial Analytics

| ID | Visual Type | Data Fields | Axis / Legend | Tooltip / Filters | Conditional Formatting | Sorting | Interactions / Cross-H / Cross-F / Export |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `FA-01` | KPI cards | `Total Revenue`, `Gross Profit`, `Profit Margin`, `Inventory Cost`, `Inventory Savings`, `Revenue per Customer` | None | Tooltip shows margin bridge and cost context; filters inherit finance slicers | Green for favorable margin and savings | Revenue-first order | No cross-highlight; export yes |
| `FA-02` | Waterfall | `Gross Profit`, `Inventory Cost`, `Inventory Savings`, `Variance` | Axis: bridge categories; legend none | Tooltip shows cost drivers and margin pressure; filters inherit `Date`, `Country`, `ProductCategory`, `Customer Segment` | Use green for gains and red for costs | Contribution order | Cross-highlight on; cross-filter to matrix and scatter; export yes |
| `FA-03` | Line chart | `DimDate[Date]`, `Profit Margin`, `Gross Profit` | Axis: `Date`; legend optional by metric | Tooltip shows period-over-period change; filters inherit page slicers | Accent line color with subtle baseline | Chronological | Cross-highlight on; cross-filter to waterfall and matrix; export yes |
| `FA-04` | Matrix / cost driver bar panel | `ProductCategory`, `Gross Profit`, `Profit Margin`, `Inventory Cost` | Rows: `ProductCategory`; legend optional if a bar variant is toggled | Tooltip shows cost driver explanations; filters inherit page slicers | Heatmap on margin and cost | Sort by profit or cost | Cross-highlight on; cross-filter to scatter; export yes |
| `FA-05` | Scatter plot | `Total Revenue`, `Gross Profit`, `Inventory Cost`, `Country` | X: revenue; Y: gross profit; Size: inventory cost; Legend: country | Tooltip shows margin, category, and country context; filters inherit page slicers | Bubble color by country or cost band | Sort by revenue or profit | Cross-highlight on; cross-filter to waterfall and matrix; export yes |

## Page 10 KPI Cockpit

| ID | Visual Type | Data Fields | Axis / Legend | Tooltip / Filters | Conditional Formatting | Sorting | Interactions / Cross-H / Cross-F / Export |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `KC-01` | KPI card | `Dynamic KPI`, `Variance`, `Target Achievement %` | None | Tooltip shows KPI definition, target logic, and drivers; filters inherit `KPI Selector`, `Target Period`, `Scenario`, `Date` | Green/amber/red by variance and achievement | Target status order | No cross-highlight; export yes |
| `KC-02` | Gauge | `Dynamic KPI`, `Target Value` | Axis: gauge scale; legend none | Tooltip shows target and variance; filters inherit cockpit slicers | Use a clear threshold band | Gauge range order | Cross-highlight limited; cross-filter to bar and table; export yes |
| `KC-03` | Bar chart | `KPI Selector`, `Dynamic KPI`, `Target Value` | Axis: `KPI Selector`; legend none | Tooltip shows actual vs target by KPI; filters inherit cockpit slicers | Target line and achievement colors | Selected KPI order | Cross-highlight on; cross-filter to sparkline and table; export yes |
| `KC-04` | Sparkline panel | `DimDate[Date]`, `Dynamic KPI` | Axis: `Date`; legend none | Tooltip shows recent trend and delta; filters inherit cockpit slicers | Highlight trend direction and turning points | Chronological | Cross-highlight on; cross-filter to gauge and table; export yes |
| `KC-05` | Table | `KPI Name`, `TargetValue`, `Variance`, `Target Achievement %`, `TargetPeriod` | Rows: KPI name; legend none | Tooltip shows selected scenario and definition; filters inherit cockpit slicers | Red/amber/green by achievement | Variance order | Cross-filter on; cross-highlight from KPI card and bar; export yes |

## Page 11 AI Insights

| ID | Visual Type | Data Fields | Axis / Legend | Tooltip / Filters | Conditional Formatting | Sorting | Interactions / Cross-H / Cross-F / Export |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `AI-01` | KPI cards | `High Risk Customers`, `High Risk Inventory Series`, `Forecast Accuracy %`, `Recommended Action Count` | None | Tooltip shows model confidence and anomaly count; filters inherit `Entity`, `Metric`, `Date`, `Scenario` | Use alert colors for risk and anomalies | Risk-first order | No cross-highlight; export yes |
| `AI-02` | Key influencers | Analyze `Churn Rate` or `Inventory Risk Score`; explain by `RiskCategory`, `CustomerHealthScore`, `InventoryRiskScore`, `CustomerSegment`, `RevenueTrend` | No axis; legend built into the visual | Tooltip shows top positive and negative drivers; filters inherit page slicers | Use the built-in influence strength scale | Driver strength order | Cross-highlight on; cross-filter to the explanation table; export yes |
| `AI-03` | Decomposition tree | `Total Revenue`, `Gross Profit`, `Churn Rate`, `Inventory Savings` | Split by `Country`, `ProductCategory`, `Customer Segment`, `Warehouse`, `Model` | Tooltip shows the selected branch and contribution; filters inherit page slicers | Highlight the active branch path | Contribution order | Cross-highlight on; cross-filter to anomaly and explanation views; export yes |
| `AI-04` | Anomaly line | `DimDate[Date]`, `Total Revenue`, `Churn Rate`, `Inventory Risk Score` | Axis: `Date`; legend: metric series | Tooltip shows anomaly detection details; filters inherit page slicers | Flag anomalous points clearly | Chronological | Cross-highlight on; cross-filter to driver scatter and table; export yes |
| `AI-05` | Driver scatter | `ChurnProbability`, `ExpectedLifetimeValue`, `CustomerHealthScore`, `RiskCategory` | X: churn probability; Y: expected lifetime value; Size: health score; Legend: risk category | Tooltip shows recommended action and confidence; filters inherit page slicers | Bubble color by risk category | Sort by probability or LTV | Cross-highlight on; cross-filter to explanation table; export yes |
| `AI-06` | Explanation table | `Entity`, `Metric`, `Reason`, `RecommendedAction`, `ProbabilityConfidence` | Rows: entity or case; legend none | Tooltip shows a short recommendation summary; filters inherit page slicers | Use severity colors and callout icons | Sort by action priority | Cross-filter on; cross-highlight from all AI visuals; export yes |

## Page 12 Executive Summary

| ID | Visual Type | Data Fields | Axis / Legend | Tooltip / Filters | Conditional Formatting | Sorting | Interactions / Cross-H / Cross-F / Export |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ES-01` | KPI cards | `Total Revenue`, `Gross Profit`, `Churn Rate`, `Inventory Risk Score`, `Forecast Accuracy %`, `Inventory Savings` | None | Tooltip shows concise board-level narrative; filters are bookmark-driven | Very restrained color use | Executive priority order | No cross-highlight; export yes |
| `ES-02` | Line chart | `DimDate[Date]`, `Total Revenue`, `Gross Profit` | Axis: `Date`; legend optional | Tooltip shows period change and trend context; filters inherit board pack settings | Accent line only, minimal gridlines | Chronological | Cross-highlight limited; cross-filter to waterfall and table; export yes |
| `ES-03` | Waterfall | `Variance`, `Inventory Savings`, `Profit Margin` | Axis: summary bridge categories; legend none | Tooltip shows the change narrative; filters inherit board pack settings | Green for positive, red for negative | Contribution order | Cross-highlight on; cross-filter to action table; export yes |
| `ES-04` | Table | `Metric`, `Status`, `Change`, `RecommendedAction` | Rows: metric; legend none | Tooltip shows one-line explanation; filters inherit board pack settings | Use simple traffic-light states | Sort by urgency | Cross-filter on; cross-highlight from cards and waterfall; export yes |
| `ES-05` | Notes panel | `Board Pack`, `Ops Pack`, `Finance Pack` notes | None | Tooltip optional; filters minimal | Neutral styling with subdued emphasis | N/A | Static reference panel; export yes |
