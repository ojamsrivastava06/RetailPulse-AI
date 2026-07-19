# RetailPulse Enterprise Power BI Data Model

## Scope
This semantic model is designed to sit on top of the existing RetailPulse outputs without recreating or rewriting the source datasets.

### Source Artifacts
- `data/processed/final_processed_dataset.csv`
- `processed/customer_segments.csv`
- `processed/customer_metrics.csv`
- `processed/customer_probability_scores.csv`
- `processed/customer_health_scores.csv`
- `processed/customer_retention_metrics.csv`
- `processed/customer_business_actions.csv`
- `processed/customer_churn_predictions.csv`
- `processed/forecast_results.csv`
- `processed/forecast_metrics.csv`
- `processed/forecast_dashboard.csv`
- `processed/future_predictions.csv`
- `processed/inventory_dataset.csv`
- `processed/inventory_metrics.csv`
- `processed/inventory_risk.csv`
- `processed/inventory_dashboard.csv`
- `processed/inventory_recommendations.csv`
- `processed/abc_analysis.csv`
- `processed/xyz_analysis.csv`
- `processed/abc_xyz_matrix.csv`

## Modeling Principles
- Use a star schema with single-direction relationships from dimensions to facts.
- Keep the data model in Import mode for the current file-based implementation.
- Create surrogate keys in Power Query for `DimDate`, `DimCustomer`, `DimProduct`, `DimCountry`, `DimCategory`, and `DimWarehouse`.
- Treat `FactCustomer` and `FactChurn` as snapshot-style facts, not fully additive transaction tables.
- Use a product mapping query to reconcile sales-line `StockCode` records with description-based forecast and inventory series.
- Extend `DimDate` to cover the latest forecast horizon so future dates remain reportable.

## Semantic Model Inventory
| Table | Type | Grain | Primary Key | Primary Source |
| --- | --- | --- | --- | --- |
| `DimDate` | Dimension | One row per date | `DateKey` | Derived calendar table |
| `DimCustomer` | Dimension | One row per customer | `CustomerKey` | Customer snapshot outputs |
| `DimProduct` | Dimension | One row per product | `ProductKey` | Sales, forecast, and inventory outputs |
| `DimCountry` | Dimension | One row per country | `CountryKey` | Distinct country values |
| `DimCategory` | Dimension | One row per product category | `CategoryKey` | Distinct product categories |
| `DimWarehouse` | Dimension | One row per warehouse | `WarehouseKey` | Inventory warehouse allocation |
| `FactSales` | Fact | One row per invoice line | `SalesLineKey` | `final_processed_dataset.csv` |
| `FactForecast` | Fact | One row per forecast point | `ForecastRowKey` | Forecast evaluation and future forecast outputs |
| `FactInventory` | Fact | One row per series/date/horizon | `InventoryRowKey` | `inventory_dataset.csv` |
| `FactCustomer` | Fact | One row per customer snapshot | `CustomerSnapshotKey` | `customer_segments.csv` and `customer_metrics.csv` |
| `FactChurn` | Fact | One row per customer snapshot | `ChurnSnapshotKey` | `customer_churn_predictions.csv` and related churn snapshots |

## Relationship Matrix
| From | To | Cardinality | Cross Filter | Active | Notes |
| --- | --- | --- | --- | --- | --- |
| `DimDate[DateKey]` | `FactSales[InvoiceDateKey]` | 1:* | Single | Yes | Transaction date analysis |
| `DimDate[DateKey]` | `FactForecast[DateKey]` | 1:* | Single | Yes | Forecast trend and horizon analysis |
| `DimDate[DateKey]` | `FactInventory[DateKey]` | 1:* | Single | Yes | Inventory planning over time |
| `DimDate[DateKey]` | `FactCustomer[SnapshotDateKey]` | 1:* | Single | Yes | Customer snapshot analysis |
| `DimDate[DateKey]` | `FactChurn[SnapshotDateKey]` | 1:* | Single | Yes | Churn snapshot analysis |
| `DimCustomer[CustomerKey]` | `FactSales[CustomerKey]` | 1:* | Single | Yes | Customer-level sales analysis |
| `DimCustomer[CustomerKey]` | `FactCustomer[CustomerKey]` | 1:* | Single | Yes | Customer intelligence summary |
| `DimCustomer[CustomerKey]` | `FactChurn[CustomerKey]` | 1:* | Single | Yes | Churn and retention analysis |
| `DimProduct[ProductKey]` | `FactSales[ProductKey]` | 1:* | Single | Yes | SKU and product mix analysis |
| `DimProduct[ProductKey]` | `FactForecast[ProductKey]` | 1:* | Single | Yes | Forecast by product |
| `DimProduct[ProductKey]` | `FactInventory[ProductKey]` | 1:* | Single | Yes | Inventory optimization by product |
| `DimCountry[CountryKey]` | `FactSales[CountryKey]` | 1:* | Single | Yes | Geographic sales analysis |
| `DimCountry[CountryKey]` | `FactForecast[CountryKey]` | 1:* | Single | Yes | Geographic forecast analysis |
| `DimCountry[CountryKey]` | `FactInventory[CountryKey]` | 1:* | Single | Yes | Country-level inventory planning |
| `DimCountry[CountryKey]` | `FactCustomer[CountryKey]` | 1:* | Single | Yes | Country-level customer mix |
| `DimCountry[CountryKey]` | `FactChurn[CountryKey]` | 1:* | Single | Yes | Churn by geography |
| `DimCategory[CategoryKey]` | `FactSales[CategoryKey]` | 1:* | Single | Yes | Category analysis |
| `DimCategory[CategoryKey]` | `FactForecast[CategoryKey]` | 1:* | Single | Yes | Forecast by category |
| `DimCategory[CategoryKey]` | `FactInventory[CategoryKey]` | 1:* | Single | Yes | Inventory by category |
| `DimCategory[CategoryKey]` | `FactCustomer[CategoryKey]` | 1:* | Single | Yes | Customer mix by category |
| `DimCategory[CategoryKey]` | `FactChurn[CategoryKey]` | 1:* | Single | Yes | Churn by category affinity |
| `DimWarehouse[WarehouseKey]` | `FactInventory[WarehouseKey]` | 1:* | Single | Yes | Replenishment and service-level planning |

## Data Dictionary

### DimDate
- `DateKey`: integer `YYYYMMDD` surrogate key.
- `Date`: calendar date.
- `Year`, `Quarter`, `MonthNumber`, `MonthName`, `WeekNumber`, `DayNumber`, `DayName`: standard calendar attributes.
- `IsWeekend`, `IsMonthStart`, `IsMonthEnd`, `IsHoliday`, `Season`: reporting attributes reused across sales, forecast, inventory, and churn.

### DimCustomer
- `CustomerKey`: surrogate customer key built from `CustomerID`.
- `CustomerID`: original business identifier from the source data.
- `FirstPurchase`, `LastPurchase`: customer lifecycle bounds.
- `CustomerTier`, `Segment`, `Cluster`: customer intelligence outputs from Phase 2.
- `HistoricalCLV`, `PredictedCLV`, `CustomerHealthScore`, `RiskCategory`, `HealthBand`: value and retention attributes from Phases 2 and 5.
- `PreferredCountry`, `PreferredCategory`, `PreferredProduct`: dominant affinity fields for drillthrough and segmentation.

### DimProduct
- `ProductKey`: surrogate key for the cleaned product master.
- `StockCode`: source SKU or item code.
- `Description`: canonical product name.
- `ProductCategory`: merchandising category derived from the pipeline rules.
- `ABCClass`, `XYZClass`, `ABCXYZMatrix`: inventory classification attributes.
- `FastMovingItem`, `SlowMovingItem`, `DeadStockCandidate`, `SeasonalProduct`, `CriticalProduct`, `HighValueItem`, `LowValueItem`: operational flags for inventory and executive reporting.

### DimCountry
- `CountryKey`: surrogate key for country.
- `CountryName`: business country label.
- `RegionGroup`: recommended grouping such as Domestic, Europe, or International.
- `WarehouseGroup`: assigned fulfillment cluster used by inventory analysis.

### DimCategory
- `CategoryKey`: surrogate key for product category.
- `CategoryName`: category label such as Lighting, Decor, Accessories, Homeware, Stationery, or Other.
- `CategoryGroup`: broader business grouping for rollup analysis.
- `DemandProfile`: optional descriptor used in forecasting and inventory planning.

### DimWarehouse
- `WarehouseKey`: warehouse surrogate key.
- `WarehouseCode`: operational warehouse code such as `WH-UK-01`.
- `WarehouseType`: domestic, regional, or international.
- `ServiceRegion`: country or market group served by the warehouse.
- `AssignmentRule`: text description of the warehouse assignment rule.

### FactSales
- `SalesLineKey`: row-level key for invoice line analysis.
- `DateKey`, `CustomerKey`, `ProductKey`, `CountryKey`, `CategoryKey`: surrogate relationships to the conformed dimensions.
- `InvoiceNo`, `InvoiceDate`, `CustomerID`, `StockCode`, `Description`, `Country`, `ProductCategory`: source transaction descriptors.
- `Quantity`, `UnitPrice`, `Revenue`, `Profit`, `TotalSales`: base monetary and volume metrics.
- `InvoiceRevenue`, `BasketSize`, `AverageBasketValue`, `AverageOrderValue`: invoice-level commercial metrics.
- `CustomerTenure`, `CustomerFrequency`, `DaysSinceLastPurchase`, `MonthlyRevenue`, `MonthlyOrderCount`, `CountryRevenue`, `ProductFrequency`: customer and product context.
- `Year`, `Quarter`, `Month`, `Week`, `Day`, `Hour`, `DayOfWeek`, `IsWeekend`, `Season`: date intelligence columns.

### FactForecast
- `ForecastRowKey`: row-level key for forecast output.
- `DateKey`, `ProductKey`, `CountryKey`, `CategoryKey`: surrogate relationships to the conformed dimensions.
- `Date`, `HorizonDays`, `SeriesKey`, `Product`, `Country`, `ProductCategory`, `Model`, `Configuration`, `ForecastLevel`, `Entity`: forecast context.
- `Actual`, `Forecast`, `Residual`, `ResidualStd`, `Lower95`, `Upper95`: historical forecast evaluation fields.
- `ForecastDemand`, `ForecastRevenue`, `DemandRisk`, `RevenuePriority`: future planning fields.

### FactInventory
- `InventoryRowKey`: row-level key for inventory planning.
- `DateKey`, `ProductKey`, `CountryKey`, `CategoryKey`, `WarehouseKey`: surrogate relationships to the conformed dimensions.
- `Date`, `HorizonDays`, `SeriesKey`, `Product`, `Country`, `ProductCategory`, `Warehouse`, `SupplierLane`: planning context.
- `CurrentStock`, `EstimatedStock`, `ForecastDemand`, `ForecastRevenue`, `Lower95Demand`, `Upper95Demand`: stock and demand state.
- `SafetyStock`, `ReorderPoint`, `ReorderQuantity`, `EconomicOrderQuantity`, `StockValue`, `DaysOfInventory`, `StockCoverageDays`: replenishment and coverage metrics.
- `InventoryTurnover`, `ServiceLevel`, `DemandVariability`, `LeadTimeVariability`, `WarehouseAllocationScore`: operational efficiency metrics.
- `StockoutRiskScore`, `OverstockRiskScore`, `DemandSpikeRiskScore`, `SupplierDelayRiskScore`, `InventoryAgeRiskScore`, `InventoryRiskScore`, `InventoryHealthScore`: risk and health outputs.
- `StockoutCost`, `TotalInventoryCost`, `OptimizedInventoryCost`, `InventorySavings`, `PotentialRevenueLoss`, `ExpectedProfitImprovement`: financial impact measures.
- `FastMovingItem`, `SlowMovingItem`, `DeadStockCandidate`, `SeasonalProduct`, `CriticalProduct`, `HighValueItem`, `LowValueItem`, `ABCClass`, `XYZClass`, `ABCXYZMatrix`: decision flags.

### FactCustomer
- `CustomerSnapshotKey`: snapshot-level customer row key.
- `DateKey`, `CustomerKey`, `CountryKey`, `CategoryKey`: surrogate relationships to the conformed dimensions.
- `CustomerID`, `FirstPurchase`, `LastPurchase`, `SnapshotDate`: customer snapshot metadata.
- `Recency`, `Frequency`, `Monetary`, `Orders`, `Revenue`, `CustomerRank`, `CustomerTier`: RFM and ranking fields.
- `HistoricalCLV`, `CustomerRevenue`, `CustomerProfit`, `CustomerMargin`, `AverageCLV`, `PredictedCLV`: value fields from Phase 2.
- `Cluster`, `Segment`, `ClusterSize`, `PCA1`, `PCA2`, `TSNE1`, `TSNE2`: segmentation outputs.
- `DominantCountry`, `DominantCategory`, `DominantProduct`: affinity fields for drillthrough and visuals.

### FactChurn
- `ChurnSnapshotKey`: snapshot-level churn row key.
- `DateKey`, `CustomerKey`, `CountryKey`, `CategoryKey`: surrogate relationships to the conformed dimensions.
- `CustomerID`, `FirstPurchase`, `LastPurchase`, `SnapshotDate`: customer timing context.
- `InvoiceCount`, `TransactionCount`, `TotalRevenue`, `TotalQuantity`, `AverageOrderValue`, `AverageBasketSize`, `MedianBasketSize`, `CustomerTenure`, `RetentionAge`, `DaysSinceLastPurchase`, `PurchaseGap`: lifecycle and buying cadence fields.
- `MonthlySpend`, `QuarterlySpend`, `AnnualSpend`, `CustomerVelocity`, `PurchaseMomentum`, `CustomerGrowthRate`, `CategoryDiversity`, `ProductDiversity`, `CountryDiversity`: behavioral measures.
- `RollingRevenue_30`, `RollingRevenue_60`, `RollingRevenue_90`, `RollingRevenue_180`, plus matching frequency and basket measures: rolling performance context.
- `ChurnProbability`, `RetentionProbability`, `NextPurchaseProbability`, `ExpectedLifetimeValue`, `CustomerHealthScore`, `RiskScore`, `RiskCategory`, `HealthBand`, `CustomerSegment`: executive retention outputs.
- `PredictedChurn`, `PredictedChurnLabel`, `RecommendedAction`, `ActionReasoning`, `ProbabilityConfidence`: actionability fields.

## Implementation Notes
- Hide technical keys and expose only business-friendly fields in the field list.
- Mark `DimDate` as the model date table.
- Keep one active relationship per fact date role and use `USERELATIONSHIP` for alternate date analysis where needed.
- Use a disconnected `KPI Targets` table for budget or target-driven measures such as variance and target achievement.
