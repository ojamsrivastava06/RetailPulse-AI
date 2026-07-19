# Power Query Implementation

## Loading Principle

Keep the Power Query layer deterministic and conservative: clean the CSVs, set types, standardize keys, and merge subject-area outputs only when they belong to the same business grain.

## Sales Staging

### `data/processed/final_processed_dataset.csv`

- Import: load as the canonical sales staging query and enable load.
- Cleaning: trim text fields, normalize country and product category labels, remove exact duplicate invoice lines, and keep only valid positive sales rows already approved by the upstream pipeline.
- Data types: `InvoiceNo` text, `StockCode` text, `Description` text, `Quantity` whole number, `InvoiceDate` datetime, `UnitPrice` decimal, `CustomerID` whole number or text, `Country` text, `IsWeekend` logical, `IsMonthStart` logical, `IsMonthEnd` logical.
- Relationships: feeds `FactSales` and provides the seed for `DimCustomer`, `DimProduct`, `DimCountry`, and `DimCategory`.
- Column mapping: `InvoiceDate` -> `DateKey` derivation; `StockCode` and `Description` -> product mapping; `CustomerID` -> customer mapping; `Country` -> country mapping; `ProductCategory` -> category mapping.
- Transformations: derive `SalesLineKey`, `InvoiceDateKey`, `CustomerKey`, `ProductKey`, `CountryKey`, and `CategoryKey`.
- Merge operations: merge with reference queries for product, customer, and date attributes only after the base query is cleaned.
- Append operations: do not append `retailpulse_processed.csv`.
- Calculated columns: keep Power Query additions limited to stable keys and sort helpers.

### `data/processed/retailpulse_processed.csv`

- Import: do not load.
- Cleaning: treat as a legacy mirror of `final_processed_dataset.csv`.
- Data types, relationships, merges, append operations, calculated columns: none.

## Customer Intelligence

### `processed/rfm_table.csv`

- Import: load and use as the customer value baseline.
- Cleaning: standardize `CustomerID`, cast date fields, and remove duplicate customer rows.
- Data types: `CustomerID` whole number, `Recency` whole number, `Frequency` whole number, `Monetary` decimal, `Orders` whole number, `Revenue` decimal, `LastPurchase` datetime, `FirstPurchase` datetime.
- Relationships: keys into `DimCustomer` and supports `FactCustomer`.
- Column mapping: RFM scores, tier, CLV, and ranking attributes map to `DimCustomer` and `FactCustomer`.
- Transformations: create a clean `CustomerKey` and a normalized tier label.
- Merge operations: merge with `customer_segments.csv` on `CustomerID`.
- Append operations: can append to `customer_segments.csv` only after aligning the customer grain.
- Calculated columns: customer segment and risk labels are better modeled as dimension attributes.

### `processed/customer_segments.csv`

- Import: load and use as the segment enrichment table.
- Cleaning: standardize `CustomerID`, trim `Segment`, and coerce PCA and t-SNE fields to decimal.
- Data types: `CustomerID` whole number, clustering diagnostics decimal or whole number, `Segment` text.
- Relationships: merge into `DimCustomer` and `FactCustomer`.
- Column mapping: `Cluster`, `Segment`, `ClusterSize`, and `CustomerTier` enrich the customer dimension.
- Transformations: keep the existing segmentation labels as-is and hide diagnostic columns if not needed in visuals.
- Merge operations: merge into `rfm_table.csv` on `CustomerID`.
- Append operations: do not append to facts; this is a customer enrichment source.
- Calculated columns: `Customer Segment` can be promoted from `Segment` for report use.

### `processed/segment_summary.csv`

- Import: load as a hidden aggregation and QA table.
- Cleaning: normalize `Segment` text and numeric totals.
- Data types: `Customers`, `Revenue`, `Orders`, `Profit`, and ratio columns as decimal or whole number.
- Relationships: none required.
- Column mapping: segment-level rollup for validation.
- Transformations: sort by revenue and retain only one row per segment.
- Merge operations: none.
- Append operations: none.
- Calculated columns: none.

### `processed/customer_retention_metrics.csv`

- Import: load as the churn and retention staging table.
- Cleaning: standardize `CustomerID`, fix date parsing, and keep a single snapshot row per customer and snapshot date.
- Data types: identity fields as whole number or text, date fields as date/datetime, ratios as decimal, flags as logical.
- Relationships: feeds `FactChurn` and can populate `FactCustomer` if retention metrics are needed there.
- Column mapping: rolling windows, momentum, diversity, and tenure fields map directly into the churn fact.
- Transformations: generate a stable snapshot grain on `CustomerID` plus `SnapshotDate`.
- Merge operations: merge with `customer_churn_predictions.csv`, `customer_health_scores.csv`, `customer_probability_scores.csv`, and `customer_business_actions.csv`.
- Append operations: append with `customer_churn_predictions.csv` only after the columns are aligned.
- Calculated columns: `Health Status` is better created in the semantic model.

### `processed/customer_churn_predictions.csv`

- Import: load and use as the predictive churn staging table.
- Cleaning: standardize identifiers and convert all score columns to decimal.
- Data types: `CustomerID` whole number, dates as date or datetime, probabilities and scores as decimal, labels and actions as text.
- Relationships: feeds `FactChurn`.
- Column mapping: churn probabilities, retention probabilities, risk categories, and recommendation text map to the churn fact.
- Transformations: keep the heuristic and model scores side by side for auditability.
- Merge operations: merge with `customer_retention_metrics.csv` on `CustomerID` and `SnapshotDate`.
- Append operations: append into the same churn fact after standardizing the columns.
- Calculated columns: `Probability Bucket` and `Health Status` can be retained as source fields.

### `processed/customer_health_scores.csv`

- Import: load as a lightweight enrichment table.
- Cleaning: standardize `CustomerID` and validate score ranges.
- Data types: `CustomerID` whole number, scores decimal, `HealthBand` text, `RiskCategory` text.
- Relationships: merge into `FactChurn` and optionally `DimCustomer`.
- Column mapping: health band and activity/engagement scores.
- Transformations: no complex reshaping needed.
- Merge operations: merge with the churn fact on `CustomerID`.
- Append operations: none.
- Calculated columns: none.

### `processed/customer_probability_scores.csv`

- Import: load as a lightweight enrichment table.
- Cleaning: standardize `CustomerID` and validate probabilities.
- Data types: `CustomerID` whole number, probabilities decimal, prediction labels text, `RiskScore` decimal.
- Relationships: merge into `FactChurn`.
- Column mapping: predicted churn, retention probability, next purchase probability, and risk score.
- Transformations: preserve both score and label outputs.
- Merge operations: merge with `customer_churn_predictions.csv`.
- Append operations: none.
- Calculated columns: none.

### `processed/customer_business_actions.csv`

- Import: load as a customer action lookup table.
- Cleaning: standardize `CustomerID`, trim action text, and keep one recommendation row per customer.
- Data types: `CustomerID` whole number, scores decimal, `RecommendedAction` and `ActionReasoning` text.
- Relationships: merge into `FactChurn` and surface selected fields in `DimCustomer`.
- Column mapping: action, reason, and band outputs.
- Transformations: preserve the recommended action as the business-facing label.
- Merge operations: merge with the churn predictions table on `CustomerID`.
- Append operations: none.
- Calculated columns: none.

### `processed/customer_model_leaderboard.csv`

- Import: load as a hidden governance table for model quality review.
- Cleaning: keep model rows unique and cast metrics to decimal.
- Data types: accuracy metrics decimal, counts whole number, status and reasons text.
- Relationships: none.
- Column mapping: model evaluation metadata only.
- Transformations: none beyond type casting.
- Merge operations: none.
- Append operations: none.
- Calculated columns: none.

## Forecasting

### `processed/forecast_results.csv`

- Import: load as the historical forecast evaluation table.
- Cleaning: standardize `SeriesKey`, `Product`, `Country`, and `ProductCategory`, and cast dates to date.
- Data types: date as date, fold and horizon columns whole number, metric columns decimal, model and configuration text.
- Relationships: feeds `FactForecast`.
- Column mapping: `Actual`, `Forecast`, `Residual`, `ResidualStd`, `Lower95`, and `Upper95`.
- Transformations: keep actual and forecast rows aligned for backtest analysis.
- Merge operations: merge with `future_predictions.csv` only after the forecast grain is normalized.
- Append operations: can append with `future_predictions.csv` after adding nulls for actual-only fields.
- Calculated columns: `Forecast Bucket` is best created in the semantic model.

### `processed/future_predictions.csv`

- Import: load as the future forecast planning table.
- Cleaning: standardize the same keys as `forecast_results.csv` and ensure horizon values are whole number.
- Data types: `Date` date, `ForecastDemand` and `ForecastRevenue` decimal, confidence band columns decimal, `HorizonDays` whole number.
- Relationships: feeds `FactForecast`.
- Column mapping: future demand and revenue projections.
- Transformations: add a source-stage flag such as `ForecastLevel` or `ForecastStage` before append.
- Merge operations: merge with `forecast_results.csv` on `SeriesKey`, `Date`, `Model`, and `Configuration` if a unified table is required.
- Append operations: append into `FactForecast` after standardizing the schema.
- Calculated columns: none.

### `processed/forecast_metrics.csv`

- Import: load as a hidden model scoring table.
- Cleaning: keep one row per series, model, and configuration.
- Data types: metric columns decimal, `status` and `reason` text.
- Relationships: none required in the report model.
- Column mapping: MAE, RMSE, MAPE, sMAPE, R2, and MASE.
- Transformations: sort by model quality for QA.
- Merge operations: none.
- Append operations: none.
- Calculated columns: none.

### `processed/forecast_dashboard.csv`

- Import: load as a small executive helper table if the forecast cockpit needs a pre-aggregated source.
- Cleaning: validate that horizon, entity, and metric values are unique at the intended grain.
- Data types: `HorizonDays` whole number, metrics decimal, labels text.
- Relationships: disconnected helper table or aggregate table only.
- Column mapping: dashboard-level forecast demand, revenue, and priority.
- Transformations: no grain changes unless the page is simplified for performance.
- Merge operations: none.
- Append operations: none.
- Calculated columns: none.

### `processed/forecast_comparison.csv`

- Import: load as a hidden governance table.
- Cleaning: validate one row per model and series.
- Data types: counts whole number, errors and fit metrics decimal.
- Relationships: none.
- Column mapping: model comparison only.
- Transformations: sort by `mape` and `rmse`.
- Merge operations: none.
- Append operations: none.
- Calculated columns: none.

## Inventory

### `processed/inventory_dataset.csv`

- Import: load as the canonical inventory planning fact.
- Cleaning: standardize `SeriesKey`, `Warehouse`, `SupplierLane`, and risk labels; convert Boolean-like strings to logical values.
- Data types: `Date` date, `HorizonDays` whole number, costs and quantities decimal, classification flags logical, risk labels text.
- Relationships: feeds `FactInventory` and supports `DimWarehouse`, `DimProduct`, `DimCountry`, `DimCategory`, and `DimDate`.
- Column mapping: stock, replenishment, risk, and optimization metrics.
- Transformations: derive `Inventory Status`, `HighRiskFlag`, and a stable `InventoryRowKey` if needed.
- Merge operations: merge with `inventory_metrics.csv`, `inventory_risk.csv`, `inventory_recommendations.csv`, `abc_analysis.csv`, and `xyz_analysis.csv`.
- Append operations: do not append unrelated inventory summary tables until the columns are aligned.
- Calculated columns: `Inventory Status` and `Health Status` can be modeled later in DAX if preferred.

### `processed/inventory_metrics.csv`

- Import: load as a supporting analysis table.
- Cleaning: standardize the same product and horizon keys as `inventory_dataset.csv`.
- Data types: metrics decimal, flags logical, classifications text.
- Relationships: merge into `FactInventory` or use as an aggregate source.
- Column mapping: summary metrics and ABC/XYZ classification outputs.
- Transformations: keep the row grain at `SeriesKey` plus `HorizonDays`.
- Merge operations: merge with `inventory_dataset.csv`.
- Append operations: none.
- Calculated columns: none.

### `processed/inventory_risk.csv`

- Import: load as a hidden risk summary table.
- Cleaning: verify all risk scores are numeric and bounded.
- Data types: risk scores decimal, high-risk day counts whole number, labels text.
- Relationships: merge into `FactInventory`.
- Column mapping: risk profile and revenue at risk.
- Transformations: no additional shaping required.
- Merge operations: merge on `SeriesKey`, `Product`, `Country`, `ProductCategory`, and `HorizonDays`.
- Append operations: none.
- Calculated columns: none.

### `processed/inventory_recommendations.csv`

- Import: load as the action table for replenishment.
- Cleaning: standardize keys and normalize free-text recommendations.
- Data types: `SuggestedQuantity` decimal or whole number, labels text.
- Relationships: merge into `FactInventory` and expose selected fields on inventory pages.
- Column mapping: recommendation, priority, trigger metric, and suggested quantity.
- Transformations: keep one recommendation row per series and horizon.
- Merge operations: merge with `inventory_dataset.csv` or `inventory_metrics.csv`.
- Append operations: none.
- Calculated columns: none.

### `processed/inventory_dashboard.csv`

- Import: load as a pre-aggregated inventory helper table.
- Cleaning: validate the dashboard view grain and unique combinations.
- Data types: metrics decimal, dimensions text, counts whole number.
- Relationships: disconnected helper table or aggregate source only.
- Column mapping: dashboard-level inventory risk and savings metrics.
- Transformations: no grain changes unless the cockpit requires them.
- Merge operations: none.
- Append operations: none.
- Calculated columns: none.

### `processed/abc_analysis.csv`

- Import: load as a product classification helper.
- Cleaning: standardize product and country text, ensure revenue shares are numeric.
- Data types: revenue and share fields decimal, classifications text, flags logical.
- Relationships: merge into `DimProduct` or `FactInventory`.
- Column mapping: ABC class, revenue share, and high-value flags.
- Transformations: keep one row per `SeriesKey`.
- Merge operations: merge with `xyz_analysis.csv` and `abc_xyz_matrix.csv`.
- Append operations: none.
- Calculated columns: none.

### `processed/xyz_analysis.csv`

- Import: load as a demand variability helper.
- Cleaning: standardize product and country text, ensure variability fields are numeric.
- Data types: variability metrics decimal, classes text, flags logical.
- Relationships: merge into `DimProduct` or `FactInventory`.
- Column mapping: XYZ class and demand variability.
- Transformations: keep one row per `SeriesKey`.
- Merge operations: merge with `abc_analysis.csv`.
- Append operations: none.
- Calculated columns: none.

### `processed/abc_xyz_matrix.csv`

- Import: load as a small summary lookup table.
- Cleaning: keep the ABC and XYZ class labels unique and cast metrics to decimal.
- Data types: counts whole number, revenue decimal, class labels text.
- Relationships: none required, but it can support a hidden product classification summary.
- Column mapping: matrix rollup only.
- Transformations: no reshaping required.
- Merge operations: none.
- Append operations: none.
- Calculated columns: none.

## Disconnected Controls

### `KPI Targets`

- Import: create as a manual table in Power BI.
- Cleaning: keep one row per KPI and target period.
- Data types: KPI name text, target value decimal, target period text.
- Relationships: disconnected.
- Column mapping: target configuration for variance measures.
- Transformations: none.
- Merge operations: none.
- Append operations: none.
- Calculated columns: optional `Target Status` if useful.

### `KPI Selector`

- Import: create as a field parameter or disconnected table.
- Cleaning: keep only business-facing KPI labels.
- Data types: text labels plus a hidden field reference.
- Relationships: disconnected.
- Column mapping: drives `Dynamic KPI`.
- Transformations: none.
- Merge operations: none.
- Append operations: none.
- Calculated columns: none.
