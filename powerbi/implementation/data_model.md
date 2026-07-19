# Semantic Model

## Modeling Approach

Use a conformed star schema with one active date role per fact table, single-direction relationships from dimensions to facts, and hidden technical keys.

## Table Summary

| Table | Type | Grain | Primary Key | Source |
| --- | --- | --- | --- | --- |
| `DimDate` | Dimension | One row per date | `DateKey` | Derived calendar table |
| `DimCustomer` | Dimension | One row per customer | `CustomerKey` | Sales and customer snapshot outputs |
| `DimProduct` | Dimension | One row per product | `ProductKey` | Sales, forecast, and inventory outputs |
| `DimCountry` | Dimension | One row per country | `CountryKey` | Distinct country values |
| `DimCategory` | Dimension | One row per category | `CategoryKey` | Distinct product categories |
| `DimWarehouse` | Dimension | One row per warehouse | `WarehouseKey` | Inventory warehouse assignments |
| `FactSales` | Fact | One row per invoice line | `SalesLineKey` | `final_processed_dataset.csv` |
| `FactForecast` | Fact | One row per series/date/model point | `ForecastRowKey` | Forecast evaluation and future predictions |
| `FactInventory` | Fact | One row per series/date/horizon/warehouse point | `InventoryRowKey` | Inventory planning outputs |
| `FactCustomer` | Fact | One row per customer snapshot | `CustomerSnapshotKey` | RFM and customer segment outputs |
| `FactChurn` | Fact | One row per customer snapshot | `ChurnSnapshotKey` | Churn and retention outputs |
| `KPI Targets` | Disconnected | One row per KPI target | `KPI Name` | Manual table |
| `KPI Selector` | Disconnected | One row per selectable KPI | `KPI Label` | Manual table or field parameter |

## Dimension Tables

### `DimDate`

- Columns: `DateKey`, `Date`, `Year`, `Quarter`, `MonthNumber`, `MonthName`, `WeekNumber`, `DayNumber`, `DayName`, `IsWeekend`, `IsMonthStart`, `IsMonthEnd`, `IsHoliday`, `Season`.
- Key: `DateKey` as integer `YYYYMMDD`.
- Relationships: 1:* to all fact tables on the relevant date key.
- Cardinality: one date row to many fact rows.
- Cross filter: single direction.
- Hidden fields: `DateKey` and any helper sort columns.
- Sort columns: `MonthName` by `MonthNumber`, `DayName` by `DayNumber`, `Quarter` by `QuarterNumber`.
- Hierarchies: `Year > Quarter > Month > Date`.

### `DimCustomer`

- Columns: `CustomerKey`, `CustomerID`, `CustomerTier`, `Segment`, `Cluster`, `HistoricalCLV`, `PredictedCLV`, `CustomerHealthScore`, `RiskCategory`, `HealthBand`, `PreferredCountry`, `PreferredCategory`, `PreferredProduct`.
- Key: `CustomerKey` derived from cleaned `CustomerID`.
- Relationships: 1:* to `FactSales`, `FactCustomer`, and `FactChurn`.
- Cardinality: one customer to many transaction and snapshot rows.
- Cross filter: single direction.
- Hidden fields: surrogate key and raw business identifiers.
- Sort columns: `CustomerTier` by business priority, `RiskCategory` by risk rank, `HealthBand` by health rank.
- Hierarchies: `Country > CustomerTier > Segment`.

### `DimProduct`

- Columns: `ProductKey`, `StockCode`, `Description`, `ProductCategory`, `ABCClass`, `XYZClass`, `ABCXYZMatrix`, `FastMovingItem`, `SlowMovingItem`, `DeadStockCandidate`, `SeasonalProduct`, `CriticalProduct`, `HighValueItem`, `LowValueItem`.
- Key: `ProductKey` from the cleaned product master.
- Relationships: 1:* to `FactSales`, `FactForecast`, `FactInventory`, `FactCustomer`, and `FactChurn` where product affinity is required.
- Cardinality: one product to many fact rows.
- Cross filter: single direction.
- Hidden fields: `StockCode` and product surrogate key.
- Sort columns: `ProductCategory` by business priority, `ABCClass` by A/B/C rank, `XYZClass` by X/Y/Z rank.
- Hierarchies: `Category > Product`.

### `DimCountry`

- Columns: `CountryKey`, `CountryName`, `RegionGroup`, `WarehouseGroup`.
- Key: `CountryKey` derived from normalized country text.
- Relationships: 1:* to all country-enabled facts.
- Cardinality: one country to many fact rows.
- Cross filter: single direction.
- Hidden fields: `CountryKey`.
- Sort columns: `RegionGroup` by reporting order if needed.
- Hierarchies: `RegionGroup > CountryName`.

### `DimCategory`

- Columns: `CategoryKey`, `CategoryName`, `CategoryGroup`, `DemandProfile`.
- Key: `CategoryKey` derived from `ProductCategory`.
- Relationships: 1:* to all category-enabled facts.
- Cardinality: one category to many fact rows.
- Cross filter: single direction.
- Hidden fields: `CategoryKey`.
- Sort columns: `CategoryName` by business priority.
- Hierarchies: `CategoryGroup > CategoryName`.

### `DimWarehouse`

- Columns: `WarehouseKey`, `WarehouseCode`, `WarehouseType`, `ServiceRegion`, `AssignmentRule`.
- Key: `WarehouseKey` from the warehouse code.
- Relationships: 1:* to `FactInventory` only.
- Cardinality: one warehouse to many inventory rows.
- Cross filter: single direction.
- Hidden fields: `WarehouseKey`.
- Sort columns: `WarehouseType` by operational priority.
- Hierarchies: `ServiceRegion > WarehouseCode`.

## Fact Tables

### `FactSales`

- Columns: `SalesLineKey`, `DateKey`, `CustomerKey`, `ProductKey`, `CountryKey`, `CategoryKey`, `InvoiceNo`, `InvoiceDate`, `StockCode`, `Description`, `Quantity`, `UnitPrice`, `Revenue`, `Profit`, `TotalSales`, `InvoiceRevenue`, `BasketSize`, `AverageBasketValue`, `AverageOrderValue`, `CustomerTenure`, `CustomerFrequency`, `DaysSinceLastPurchase`, `MonthlyRevenue`, `MonthlyOrderCount`, `CountryRevenue`, `ProductFrequency`.
- Grain: invoice line.
- Keys: surrogate row key plus conformed dimension keys.
- Relationships: many-to-one to every conformed dimension except warehouse.
- Cardinality: many fact rows to one dimension row.
- Cross filter: single direction from dimensions to fact.
- Hidden fields: raw lookup keys, technical date keys, and duplicated legacy columns if they are not needed on visuals.
- Sort columns: `InvoiceDate` ascending, `ProductCategory` by business rank, `Country` by market order.
- Hierarchies: `InvoiceDate` can reuse the date hierarchy.

### `FactForecast`

- Columns: `ForecastRowKey`, `DateKey`, `ProductKey`, `CountryKey`, `CategoryKey`, `Date`, `SeriesKey`, `Product`, `Country`, `ProductCategory`, `Model`, `Configuration`, `Fold`, `HorizonDays`, `ForecastLevel`, `Entity`, `Actual`, `Forecast`, `Residual`, `ResidualStd`, `Lower95`, `Upper95`, `ForecastDemand`, `ForecastRevenue`.
- Grain: one forecast series and date per model/configuration.
- Keys: row key plus conformed dimension keys.
- Relationships: many-to-one to date, product, country, and category.
- Cardinality: many forecast rows to one dimension row.
- Cross filter: single direction.
- Hidden fields: `SeriesKey`, `Configuration`, and raw diagnostics if not needed on report pages.
- Sort columns: `Date`, `HorizonDays`, `Model`.
- Hierarchies: `Model > Configuration > SeriesKey` for drilldown if needed.

### `FactInventory`

- Columns: `InventoryRowKey`, `DateKey`, `ProductKey`, `CountryKey`, `CategoryKey`, `WarehouseKey`, `Date`, `SeriesKey`, `Product`, `Country`, `ProductCategory`, `Warehouse`, `SupplierLane`, `HorizonDays`, `CurrentStock`, `EstimatedStock`, `ForecastDemand`, `ForecastRevenue`, `SafetyStock`, `ReorderPoint`, `ReorderQuantity`, `EconomicOrderQuantity`, `InventoryTurnover`, `DaysOfInventory`, `ServiceLevel`, `StockCoverageDays`, `DemandVariability`, `LeadTimeVariability`, `WarehouseAllocationScore`, `InventoryRiskScore`, `InventoryHealthScore`, `StockoutCost`, `TotalInventoryCost`, `OptimizedInventoryCost`, `InventorySavings`, `PotentialRevenueLoss`, `ExpectedProfitImprovement`, `InventoryRiskLevel`, `InventoryHealthScore`, `ReorderToday`, `HighRiskFlag`, `PredictedHighRiskProbability`, `PredictedHighRiskFlag`.
- Grain: series, date, horizon, and warehouse combination.
- Keys: row key plus conformed dimension keys.
- Relationships: many-to-one to date, product, country, category, and warehouse.
- Cardinality: many inventory rows to one dimension row.
- Cross filter: single direction.
- Hidden fields: technical risk scores and helper flags that are not used directly on visuals.
- Sort columns: `HorizonDays`, `Warehouse`, `InventoryRiskLevel`.
- Hierarchies: `Warehouse > ProductCategory > Product`.

### `FactCustomer`

- Columns: `CustomerSnapshotKey`, `DateKey`, `CustomerKey`, `CountryKey`, `CategoryKey`, `CustomerID`, `Recency`, `Frequency`, `Monetary`, `Orders`, `Revenue`, `LastPurchase`, `FirstPurchase`, `R_score`, `F_score`, `M_score`, `RFM_Score`, `CustomerRank`, `CustomerTier`, `HistoricalCLV`, `CustomerRevenue`, `CustomerProfit`, `CustomerMargin`, `LifetimeDays`, `PurchaseIntervalDays`, `AverageCLV`, `PredictedCLV`, `Cluster`, `Segment`, `PCA1`, `PCA2`, `TSNE1`, `TSNE2`, `ClusterSize`.
- Grain: customer snapshot.
- Keys: row key plus customer, date, country, and category keys.
- Relationships: many-to-one to date, customer, country, and category.
- Cardinality: many snapshot rows to one customer.
- Cross filter: single direction.
- Hidden fields: PCA and t-SNE diagnostics, snapshot helper fields, and raw business identifiers if duplicated elsewhere.
- Sort columns: `CustomerTier`, `Segment`, `CustomerRank`.
- Hierarchies: `CustomerTier > Segment > CustomerID`.

### `FactChurn`

- Columns: `ChurnSnapshotKey`, `DateKey`, `CustomerKey`, `CountryKey`, `CategoryKey`, `CustomerID`, `FirstPurchase`, `LastPurchase`, `SnapshotDate`, `InvoiceCount`, `TransactionCount`, `TotalRevenue`, `TotalQuantity`, `AverageOrderValue`, `AverageBasketSize`, `MedianBasketSize`, `CustomerTenure`, `RetentionAge`, `DaysSinceLastPurchase`, `PurchaseGap`, `MonthlySpend`, `QuarterlySpend`, `AnnualSpend`, `CustomerVelocity`, `PurchaseMomentum`, `CustomerGrowthRate`, `CategoryDiversity`, `ProductDiversity`, `CountryDiversity`, `RollingRevenue_30`, `RollingRevenue_60`, `RollingRevenue_90`, `RollingRevenue_180`, `ChurnProbability`, `RetentionProbability`, `NextPurchaseProbability`, `ExpectedLifetimeValue`, `CustomerHealthScore`, `RiskScore`, `RiskCategory`, `HealthBand`, `CustomerSegment`, `RecommendedAction`, `ActionReasoning`, `ProbabilityConfidence`, `PredictedChurn`, `PredictedChurnLabel`, `ProbabilityBucket`.
- Grain: one snapshot row per customer and snapshot date.
- Keys: row key plus customer, date, country, and category keys.
- Relationships: many-to-one to date, customer, country, and category.
- Cardinality: many churn rows to one customer.
- Cross filter: single direction.
- Hidden fields: rolling windows, heuristic scores, probability diagnostics, and internal recommendation text where not needed on visuals.
- Sort columns: `RiskCategory` by severity, `HealthBand` by health rank, `ProbabilityBucket` by probability rank.
- Hierarchies: `RiskCategory > HealthBand > CustomerSegment`.

## Relationship Matrix

| From | To | Cardinality | Cross Filter | Active | Notes |
| --- | --- | --- | --- | --- | --- |
| `DimDate[DateKey]` | `FactSales[DateKey]` | 1:* | Single | Yes | Sales trend analysis |
| `DimDate[DateKey]` | `FactForecast[DateKey]` | 1:* | Single | Yes | Forecast trend analysis |
| `DimDate[DateKey]` | `FactInventory[DateKey]` | 1:* | Single | Yes | Inventory trend analysis |
| `DimDate[DateKey]` | `FactCustomer[DateKey]` | 1:* | Single | Yes | Customer snapshot analysis |
| `DimDate[DateKey]` | `FactChurn[DateKey]` | 1:* | Single | Yes | Churn snapshot analysis |
| `DimCustomer[CustomerKey]` | `FactSales[CustomerKey]` | 1:* | Single | Yes | Customer-level sales |
| `DimCustomer[CustomerKey]` | `FactCustomer[CustomerKey]` | 1:* | Single | Yes | Customer intelligence |
| `DimCustomer[CustomerKey]` | `FactChurn[CustomerKey]` | 1:* | Single | Yes | Churn and retention |
| `DimProduct[ProductKey]` | `FactSales[ProductKey]` | 1:* | Single | Yes | Product analysis |
| `DimProduct[ProductKey]` | `FactForecast[ProductKey]` | 1:* | Single | Yes | Demand forecasting |
| `DimProduct[ProductKey]` | `FactInventory[ProductKey]` | 1:* | Single | Yes | Inventory planning |
| `DimProduct[ProductKey]` | `FactCustomer[ProductKey]` | 1:* | Single | Optional | Product affinity analysis |
| `DimProduct[ProductKey]` | `FactChurn[ProductKey]` | 1:* | Single | Optional | Product affinity analysis |
| `DimCountry[CountryKey]` | `FactSales[CountryKey]` | 1:* | Single | Yes | Geographic sales |
| `DimCountry[CountryKey]` | `FactForecast[CountryKey]` | 1:* | Single | Yes | Geographic forecasting |
| `DimCountry[CountryKey]` | `FactInventory[CountryKey]` | 1:* | Single | Yes | Geographic inventory |
| `DimCountry[CountryKey]` | `FactCustomer[CountryKey]` | 1:* | Single | Yes | Geographic customer mix |
| `DimCountry[CountryKey]` | `FactChurn[CountryKey]` | 1:* | Single | Yes | Geographic churn |
| `DimCategory[CategoryKey]` | `FactSales[CategoryKey]` | 1:* | Single | Yes | Category analysis |
| `DimCategory[CategoryKey]` | `FactForecast[CategoryKey]` | 1:* | Single | Yes | Category forecasting |
| `DimCategory[CategoryKey]` | `FactInventory[CategoryKey]` | 1:* | Single | Yes | Category inventory |
| `DimCategory[CategoryKey]` | `FactCustomer[CategoryKey]` | 1:* | Single | Optional | Category affinity |
| `DimCategory[CategoryKey]` | `FactChurn[CategoryKey]` | 1:* | Single | Optional | Category affinity |
| `DimWarehouse[WarehouseKey]` | `FactInventory[WarehouseKey]` | 1:* | Single | Yes | Warehouse planning |

## Hidden Fields

- Hide all surrogate keys in every dimension.
- Hide raw business identifiers when they are duplicated in conformed dimensions and facts.
- Hide helper sort columns, QA-only metrics, and model governance tables.
- Hide `retailpulse_processed.csv` and all `*.bak_*` files.

## Sort and Hierarchy Rules

- Sort `MonthName` by `MonthNumber`.
- Sort `Quarter` by quarter number.
- Sort `CustomerTier`, `RiskCategory`, `HealthBand`, `ABCClass`, and `XYZClass` by explicit numeric helper columns if needed.
- Build date, customer, product, and geography hierarchies in the dimension tables, not in the fact tables.

## Model Notes

- Keep `FactCustomer` and `FactChurn` as snapshot facts.
- Keep `DimProduct` as the conformed product master for sales, forecast, and inventory.
- Use disconnected support tables for targets, KPI selection, and model governance.
