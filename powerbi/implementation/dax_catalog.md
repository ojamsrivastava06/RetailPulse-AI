# DAX Catalog

## Design Rules

- Build base measures first and reuse them everywhere.
- Keep time intelligence on `DimDate`.
- Use `KPI Targets` for target-driven cards and `KPI Selector` for dynamic switching.
- Format measures at the report layer, not inside the data source.

## Base Sales And Revenue

| Measure | Purpose | Formula | Depends On | Formatting | Performance Notes |
| --- | --- | --- | --- | --- | --- |
| `Total Revenue` | Core revenue metric | `Total Revenue = SUM(FactSales[Revenue])` | `FactSales[Revenue]` | Currency | Base measure for most sales pages |
| `Total Orders` | Unique order count | `Total Orders = DISTINCTCOUNT(FactSales[InvoiceNo])` | `FactSales[InvoiceNo]` | Whole number | Keep `InvoiceNo` as text if cancellation codes exist |
| `Total Customers` | Unique customer count | `Total Customers = DISTINCTCOUNT(DimCustomer[CustomerKey])` | `DimCustomer[CustomerKey]` | Whole number | Reuse on customer and churn pages |
| `Total Products` | Unique product count | `Total Products = DISTINCTCOUNT(DimProduct[ProductKey])` | `DimProduct[ProductKey]` | Whole number | Reuse on product and inventory pages |
| `Average Order Value` | Revenue per order | `Average Order Value = DIVIDE([Total Revenue], [Total Orders])` | `[Total Revenue]`, `[Total Orders]` | Currency | Safe divide avoids blank errors |
| `Revenue Growth %` | Friendly alias for YoY growth | `Revenue Growth % = [YOY Growth]` | `[YOY Growth]` | Percentage | Avoid duplicating logic |
| `YOY Growth` | Year-over-year growth | `YOY Growth = DIVIDE([Total Revenue] - CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(DimDate[Date])), CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(DimDate[Date])))` | `DimDate[Date]`, `[Total Revenue]` | Percentage | Relies on a marked date table |
| `MOM Growth` | Month-over-month growth | `MOM Growth = DIVIDE([Total Revenue] - CALCULATE([Total Revenue], DATEADD(DimDate[Date], -1, MONTH)), CALCULATE([Total Revenue], DATEADD(DimDate[Date], -1, MONTH)))` | `DimDate[Date]`, `[Total Revenue]` | Percentage | Keep `DimDate` contiguous |
| `Monthly Revenue` | Month-to-date revenue | `Monthly Revenue = CALCULATE([Total Revenue], DATESMTD(DimDate[Date]))` | `DimDate[Date]`, `[Total Revenue]` | Currency | Works best on sales and finance pages |
| `Quarterly Revenue` | Quarter-to-date revenue | `Quarterly Revenue = CALCULATE([Total Revenue], DATESQTD(DimDate[Date]))` | `DimDate[Date]`, `[Total Revenue]` | Currency | Use with `Quarter` hierarchy |
| `Gross Profit` | Profitability metric | `Gross Profit = SUM(FactSales[Profit])` | `FactSales[Profit]` | Currency | Use the pipeline profit estimate consistently |
| `Profit Margin` | Profit as a share of revenue | `Profit Margin = DIVIDE([Gross Profit], [Total Revenue])` | `[Gross Profit]`, `[Total Revenue]` | Percentage | Keep the format at 1 or 2 decimals |
| `Revenue per Customer` | Monetization per account | `Revenue per Customer = DIVIDE([Total Revenue], [Total Customers])` | `[Total Revenue]`, `[Total Customers]` | Currency | Useful on customer and finance pages |
| `Rolling Revenue` | 90-day rolling revenue | `Rolling Revenue = CALCULATE([Total Revenue], DATESINPERIOD(DimDate[Date], MAX(DimDate[Date]), -90, DAY))` | `DimDate[Date]`, `[Total Revenue]` | Currency | Avoid on very high-cardinality visuals |
| `Running Total` | Cumulative revenue | `Running Total = CALCULATE([Total Revenue], FILTER(ALLSELECTED(DimDate[Date]), DimDate[Date] <= MAX(DimDate[Date])))` | `DimDate[Date]`, `[Total Revenue]` | Currency | Use `ALLSELECTED` to keep slicers respected |
| `Top Product Revenue` | Revenue from the leading product in context | `Top Product Revenue = MAXX(TOPN(1, SUMMARIZE(DimProduct, DimProduct[ProductKey], "ProductRevenue", [Total Revenue]), [ProductRevenue], DESC), [ProductRevenue])` | `DimProduct`, `[Total Revenue]` | Currency | Use on summary cards only |
| `Category Revenue` | Category-scoped revenue | `Category Revenue = [Total Revenue]` | `[Total Revenue]` | Currency | Context-driven, no extra aggregation |
| `Country Revenue` | Country-scoped revenue | `Country Revenue = [Total Revenue]` | `[Total Revenue]` | Currency | Context-driven, no extra aggregation |

## Forecast And Planning

| Measure | Purpose | Formula | Depends On | Formatting | Performance Notes |
| --- | --- | --- | --- | --- | --- |
| `Forecast Demand` | Future demand volume | `Forecast Demand = SUM(FactForecast[ForecastDemand])` | `FactForecast[ForecastDemand]` | Whole number or decimal | Use on the forecasting page and inventory page |
| `Forecast Revenue` | Future revenue value | `Forecast Revenue = SUM(FactForecast[ForecastRevenue])` | `FactForecast[ForecastRevenue]` | Currency | Pair with actual revenue on trend lines |
| `Forecast Error` | Signed residual total | `Forecast Error = SUMX(FILTER(FactForecast, NOT ISBLANK(FactForecast[Actual])), FactForecast[Residual])` | `FactForecast[Residual]`, `FactForecast[Actual]` | Currency or decimal | Keep the filter scoped to evaluated rows |
| `MAPE` | Mean absolute percentage error | `MAPE = AVERAGEX(FILTER(FactForecast, NOT ISBLANK(FactForecast[Actual]) && FactForecast[Actual] <> 0), ABS(DIVIDE(FactForecast[Actual] - FactForecast[Forecast], FactForecast[Actual])))` | `FactForecast[Actual]`, `FactForecast[Forecast]` | Percentage | Use only on evaluation rows |
| `Forecast Accuracy %` | Accuracy score | `Forecast Accuracy % = 1 - [MAPE]` | `[MAPE]` | Percentage | Higher is better |
| `Forecast Bias %` | Normalized signed bias | `Forecast Bias % = DIVIDE([Forecast Error], CALCULATE(SUM(FactForecast[Actual]), FILTER(FactForecast, NOT ISBLANK(FactForecast[Actual]))))` | `[Forecast Error]`, `FactForecast[Actual]` | Percentage | Optional diagnostic |
| `Forecast Coverage` | Number of forecast series in view | `Forecast Coverage = DISTINCTCOUNT(FactForecast[SeriesKey])` | `FactForecast[SeriesKey]` | Whole number | Useful for model comparison |
| `Best Model Count` | Count of selected best-model rows | `Best Model Count = CALCULATE(DISTINCTCOUNT(FactForecast[SeriesKey]), FactForecast[Model] = SELECTEDVALUE(FactForecast[Model]))` | `FactForecast[SeriesKey]`, `FactForecast[Model]` | Whole number | Useful on comparison pages |

## Inventory Intelligence

| Measure | Purpose | Formula | Depends On | Formatting | Performance Notes |
| --- | --- | --- | --- | --- | --- |
| `Inventory Cost` | Total inventory cost | `Inventory Cost = SUM(FactInventory[TotalInventoryCost])` | `FactInventory[TotalInventoryCost]` | Currency | Use on finance and inventory pages |
| `Inventory Savings` | Optimization upside | `Inventory Savings = SUM(FactInventory[InventorySavings])` | `FactInventory[InventorySavings]` | Currency | Often shown alongside cost |
| `Inventory Turnover` | Average stock turns | `Inventory Turnover = AVERAGE(FactInventory[InventoryTurnover])` | `FactInventory[InventoryTurnover]` | Decimal | Useful for category and warehouse views |
| `Stock Coverage` | Average days of stock coverage | `Stock Coverage = AVERAGE(FactInventory[StockCoverageDays])` | `FactInventory[StockCoverageDays]` | Decimal | Keep as days, not percentage |
| `Safety Stock` | Safety buffer | `Safety Stock = AVERAGE(FactInventory[SafetyStock])` | `FactInventory[SafetyStock]` | Whole number or decimal | Use with reorder visuals |
| `EOQ` | Economic order quantity | `EOQ = AVERAGE(FactInventory[EconomicOrderQuantity])` | `FactInventory[EconomicOrderQuantity]` | Whole number or decimal | Use sparingly on executive pages |
| `Inventory Health Score` | Executive health indicator | `Inventory Health Score = AVERAGE(FactInventory[InventoryHealthScore])` | `FactInventory[InventoryHealthScore]` | 0-100 score | Prefer on KPI cards |
| `Inventory Risk Score` | Executive risk indicator | `Inventory Risk Score = AVERAGE(FactInventory[InventoryRiskScore])` | `FactInventory[InventoryRiskScore]` | 0-100 score | Prefer on KPI cards and matrices |
| `High Risk Inventory Series` | Exception count | `High Risk Inventory Series = CALCULATE(DISTINCTCOUNT(FactInventory[SeriesKey]), FactInventory[InventoryRiskLevel] IN {"High", "Critical"})` | `FactInventory[SeriesKey]`, `FactInventory[InventoryRiskLevel]` | Whole number | Use in exception tables |
| `Reorder Today Count` | Immediate reorder backlog | `Reorder Today Count = CALCULATE(DISTINCTCOUNT(FactInventory[SeriesKey]), FactInventory[ReorderToday] = TRUE())` | `FactInventory[SeriesKey]`, `FactInventory[ReorderToday]` | Whole number | Good for action cards |

## Customer Intelligence And Churn

| Measure | Purpose | Formula | Depends On | Formatting | Performance Notes |
| --- | --- | --- | --- | --- | --- |
| `Customer Lifetime Value` | Total expected lifetime value | `Customer Lifetime Value = SUM(FactChurn[ExpectedLifetimeValue])` | `FactChurn[ExpectedLifetimeValue]` | Currency | Use on churn and executive pages |
| `Average CLV` | Average predicted customer value | `Average CLV = AVERAGE(FactCustomer[PredictedCLV])` | `FactCustomer[PredictedCLV]` | Currency | Use on customer intelligence pages |
| `Customer Health Score` | Customer-level health | `Customer Health Score = MAX(FactChurn[CustomerHealthScore])` | `FactChurn[CustomerHealthScore]` | 0-100 score | Use on customer drillthrough pages |
| `Average Health Score` | Portfolio health view | `Average Health Score = AVERAGE(FactChurn[CustomerHealthScore])` | `FactChurn[CustomerHealthScore]` | 0-100 score | Good for summary cards |
| `Churn Rate` | Share predicted to churn | `Churn Rate = AVERAGE(FactChurn[PredictedChurn])` | `FactChurn[PredictedChurn]` | Percentage | Keep the score scaled consistently |
| `Retention Rate` | Share retained | `Retention Rate = 1 - [Churn Rate]` | `[Churn Rate]` | Percentage | Complement of churn rate |
| `High Risk Customers` | Critical or high-risk customer count | `High Risk Customers = CALCULATE([Total Customers], FactChurn[RiskCategory] IN {"Critical", "High"})` | `[Total Customers]`, `FactChurn[RiskCategory]` | Whole number | Use on retention workload pages |
| `Low Risk Customers` | Healthy customer count | `Low Risk Customers = CALCULATE([Total Customers], FactChurn[RiskCategory] = "Low")` | `[Total Customers]`, `FactChurn[RiskCategory]` | Whole number | Use as a balancing KPI |
| `VIP Customers` | Highest-value customers | `VIP Customers = CALCULATE([Total Customers], FactChurn[HealthBand] = "VIP")` | `[Total Customers]`, `FactChurn[HealthBand]` | Whole number | Use on executive and customer pages |
| `Customer Segment Count` | Number of segments in view | `Customer Segment Count = DISTINCTCOUNT(FactCustomer[Segment])` | `FactCustomer[Segment]` | Whole number | Use on segment mix pages |
| `Recommended Action Count` | Distinct recommendations in view | `Recommended Action Count = DISTINCTCOUNT(FactChurn[RecommendedAction])` | `FactChurn[RecommendedAction]` | Whole number | Use on AI and churn pages |

## Executive Utilities

| Measure | Purpose | Formula | Depends On | Formatting | Performance Notes |
| --- | --- | --- | --- | --- | --- |
| `Target Value` | Selected KPI target | `Target Value = SELECTEDVALUE('KPI Targets'[TargetValue])` | `KPI Targets[TargetValue]` | Currency or percentage by KPI | Keep the target table disconnected |
| `Dynamic KPI` | KPI switcher | `Dynamic KPI = SWITCH(SELECTEDVALUE('KPI Selector'[KPI]), "Revenue", [Total Revenue], "Profit", [Gross Profit], "Orders", [Total Orders], "Customers", [Total Customers], "Churn Rate", [Churn Rate], "Inventory Cost", [Inventory Cost], "Forecast Revenue", [Forecast Revenue], [Total Revenue])` | `KPI Selector`, base measures | Matches selected KPI | Keep the selector list curated |
| `Variance` | Difference to target | `Variance = [Dynamic KPI] - [Target Value]` | `[Dynamic KPI]`, `[Target Value]` | Same as selected KPI | Avoid divide-by-zero style issues |
| `Target Achievement %` | Goal attainment rate | `Target Achievement % = DIVIDE([Dynamic KPI], [Target Value])` | `[Dynamic KPI]`, `[Target Value]` | Percentage | Use on cockpit and summary pages |

## Calculated Columns

| Table | Column | Formula | Notes |
| --- | --- | --- | --- |
| `DimDate` | `Year` | `Year = YEAR(DimDate[Date])` | Calendar year |
| `DimDate` | `Quarter` | `Quarter = "Q" & FORMAT(DimDate[Date], "Q")` | Quarter label |
| `DimDate` | `Month` | `Month = FORMAT(DimDate[Date], "MMMM")` | Display month |
| `DimDate` | `Week` | `Week = WEEKNUM(DimDate[Date], 2)` | ISO-style week number |
| `DimDate` | `Day` | `Day = DAY(DimDate[Date])` | Day of month |
| `DimDate` | `Season` | `Season = SWITCH(TRUE(), MONTH(DimDate[Date]) IN {12,1,2}, "Winter", MONTH(DimDate[Date]) IN {3,4,5}, "Spring", MONTH(DimDate[Date]) IN {6,7,8}, "Summer", "Autumn")` | Retail season |
| `DimDate` | `Weekend` | `Weekend = IF(WEEKDAY(DimDate[Date], 2) > 5, "Weekend", "Weekday")` | Traffic bucket |
| `DimCustomer` | `Customer Segment` | `Customer Segment = COALESCE(LOOKUPVALUE(FactChurn[CustomerSegment], FactChurn[CustomerID], DimCustomer[CustomerID]), LOOKUPVALUE(FactCustomer[Segment], FactCustomer[CustomerID], DimCustomer[CustomerID]), "Unassigned")` | Preferred customer label |
| `DimCustomer` | `Risk Category` | `Risk Category = COALESCE(LOOKUPVALUE(FactChurn[RiskCategory], FactChurn[CustomerID], DimCustomer[CustomerID]), "Unknown")` | Churn-focused tag |
| `FactForecast` | `Forecast Bucket` | `Forecast Bucket = SWITCH(TRUE(), FactForecast[HorizonDays] <= 30, "0-30 Days", FactForecast[HorizonDays] <= 90, "31-90 Days", FactForecast[HorizonDays] <= 180, "91-180 Days", "181+ Days")` | Planning horizon grouping |
| `FactInventory` | `Inventory Status` | `Inventory Status = SWITCH(TRUE(), FactInventory[InventoryRiskLevel] IN {"Critical", "High"} || FactInventory[StockCoverageDays] < 14, "Critical", FactInventory[InventoryRiskLevel] = "Medium" || FactInventory[StockCoverageDays] < 30, "Watch", FactInventory[InventoryRiskLevel] = "Low" && FactInventory[StockCoverageDays] > 120, "Overstock", "Balanced")` | Operational stock state |
| `FactChurn` | `Health Status` | `Health Status = SWITCH(TRUE(), FactChurn[CustomerHealthScore] >= 80, "Healthy", FactChurn[CustomerHealthScore] >= 60, "Watch", FactChurn[CustomerHealthScore] >= 40, "At Risk", "Critical")` | Retention readiness label |
