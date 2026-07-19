# RetailPulse DAX Measures

## Measure Design Rules
- Build a small set of base measures first, then reuse them everywhere.
- Keep time intelligence on `DimDate` and mark that table as the official date table.
- Use a disconnected `KPI Targets` table for variance and target achievement.
- Use field parameters for KPI switching and page-level metric selection.

## Sales And Revenue
| Measure | DAX | Notes |
| --- | --- | --- |
| `Total Revenue` | `Total Revenue = SUM(FactSales[Revenue])` | Core revenue card and trend measure |
| `Total Orders` | `Total Orders = DISTINCTCOUNT(FactSales[InvoiceNo])` | Unique invoice count |
| `Total Customers` | `Total Customers = DISTINCTCOUNT(DimCustomer[CustomerKey])` | Conformed customer count |
| `Total Products` | `Total Products = DISTINCTCOUNT(DimProduct[ProductKey])` | Conformed product count |
| `Average Order Value` | `Average Order Value = DIVIDE([Total Revenue], [Total Orders])` | Order quality and basket value |
| `Revenue Growth %` | `Revenue Growth % = [YOY Growth]` | Readable alias for year-over-year growth |
| `YOY Growth` | `YOY Growth = DIVIDE([Total Revenue] - CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(DimDate[Date])), CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(DimDate[Date])))` | Standard yearly growth |
| `MOM Growth` | `MOM Growth = DIVIDE([Total Revenue] - CALCULATE([Total Revenue], DATEADD(DimDate[Date], -1, MONTH)), CALCULATE([Total Revenue], DATEADD(DimDate[Date], -1, MONTH)))` | Month-over-month growth |
| `Monthly Revenue` | `Monthly Revenue = CALCULATE([Total Revenue], DATESMTD(DimDate[Date]))` | Month-to-date revenue |
| `Quarterly Revenue` | `Quarterly Revenue = CALCULATE([Total Revenue], DATESQTD(DimDate[Date]))` | Quarter-to-date revenue |
| `Gross Profit` | `Gross Profit = SUM(FactSales[Profit])` | Uses the pipeline profit estimate |
| `Profit Margin` | `Profit Margin = DIVIDE([Gross Profit], [Total Revenue])` | Profitability rate |
| `Revenue per Customer` | `Revenue per Customer = DIVIDE([Total Revenue], [Total Customers])` | Portfolio monetization |
| `Rolling Revenue` | `Rolling Revenue = CALCULATE([Total Revenue], DATESINPERIOD(DimDate[Date], MAX(DimDate[Date]), -90, DAY))` | Rolling 90-day view |
| `Running Total` | `Running Total = CALCULATE([Total Revenue], FILTER(ALLSELECTED(DimDate[Date]), DimDate[Date] <= MAX(DimDate[Date])))` | Cumulative trend line |
| `Top Product Revenue` | `Top Product Revenue = MAXX(TOPN(1, SUMMARIZE(DimProduct, DimProduct[ProductKey], "ProductRevenue", [Total Revenue]), [ProductRevenue], DESC), [ProductRevenue])` | Revenue from the top-ranked product in context |
| `Category Revenue` | `Category Revenue = [Total Revenue]` | Used on category-sliced pages |
| `Country Revenue` | `Country Revenue = [Total Revenue]` | Used on geography-sliced pages |

## Forecast And Planning
| Measure | DAX | Notes |
| --- | --- | --- |
| `Forecast Demand` | `Forecast Demand = SUM(FactForecast[ForecastDemand])` | Future demand planning |
| `Forecast Revenue` | `Forecast Revenue = SUM(FactForecast[ForecastRevenue])` | Future revenue planning |
| `Forecast Error` | `Forecast Error = SUMX(FILTER(FactForecast, NOT ISBLANK(FactForecast[Actual])), FactForecast[Residual])` | Directional bias across evaluation rows |
| `MAPE` | `MAPE = AVERAGEX(FILTER(FactForecast, NOT ISBLANK(FactForecast[Actual]) && FactForecast[Actual] <> 0), ABS(DIVIDE(FactForecast[Actual] - FactForecast[Forecast], FactForecast[Actual])))` | Mean absolute percentage error |
| `Forecast Accuracy %` | `Forecast Accuracy % = 1 - [MAPE]` | Higher is better |
| `Forecast Bias %` | `Forecast Bias % = DIVIDE([Forecast Error], CALCULATE(SUM(FactForecast[Actual]), FILTER(FactForecast, NOT ISBLANK(FactForecast[Actual]))))` | Optional bias normalizer |
| `Forecast Coverage` | `Forecast Coverage = DISTINCTCOUNT(FactForecast[SeriesKey])` | Useful on forecast model pages |
| `Best Model Count` | `Best Model Count = CALCULATE(DISTINCTCOUNT(FactForecast[SeriesKey]), FactForecast[Model] = SELECTEDVALUE(FactForecast[Model]))` | Supports model comparison visuals |

## Inventory Intelligence
| Measure | DAX | Notes |
| --- | --- | --- |
| `Inventory Cost` | `Inventory Cost = SUM(FactInventory[TotalInventoryCost])` | Total carrying and stockout cost |
| `Inventory Savings` | `Inventory Savings = SUM(FactInventory[InventorySavings])` | Optimization upside |
| `Inventory Turnover` | `Inventory Turnover = AVERAGE(FactInventory[InventoryTurnover])` | Operational efficiency |
| `Stock Coverage` | `Stock Coverage = AVERAGE(FactInventory[StockCoverageDays])` | Coverage in days |
| `Safety Stock` | `Safety Stock = AVERAGE(FactInventory[SafetyStock])` | Reorder buffer |
| `EOQ` | `EOQ = AVERAGE(FactInventory[EconomicOrderQuantity])` | Optimal order quantity |
| `Inventory Health Score` | `Inventory Health Score = AVERAGE(FactInventory[InventoryHealthScore])` | Executive health KPI |
| `Inventory Risk Score` | `Inventory Risk Score = AVERAGE(FactInventory[InventoryRiskScore])` | Executive risk KPI |
| `High Risk Inventory Series` | `High Risk Inventory Series = CALCULATE(DISTINCTCOUNT(FactInventory[SeriesKey]), FactInventory[InventoryRiskLevel] IN {"High", "Critical"})` | Exception count |
| `Reorder Today Count` | `Reorder Today Count = CALCULATE(DISTINCTCOUNT(FactInventory[SeriesKey]), FactInventory[ReorderToday] = TRUE())` | Immediate action backlog |

## Customer Intelligence And Churn
| Measure | DAX | Notes |
| --- | --- | --- |
| `Customer Lifetime Value` | `Customer Lifetime Value = SUM(FactChurn[ExpectedLifetimeValue])` | Portfolio lifetime value |
| `Average CLV` | `Average CLV = AVERAGE(FactCustomer[PredictedCLV])` | Customer intelligence average |
| `Customer Health Score` | `Customer Health Score = MAX(FactChurn[CustomerHealthScore])` | Detail-page customer score |
| `Average Health Score` | `Average Health Score = AVERAGE(FactChurn[CustomerHealthScore])` | Portfolio health view |
| `Churn Rate` | `Churn Rate = AVERAGE(FactChurn[PredictedChurn])` | Proportion of churned customers |
| `Retention Rate` | `Retention Rate = 1 - [Churn Rate]` | Retention complement |
| `High Risk Customers` | `High Risk Customers = CALCULATE([Total Customers], FactChurn[RiskCategory] IN {"Critical", "High"})` | Retention workload |
| `Low Risk Customers` | `Low Risk Customers = CALCULATE([Total Customers], FactChurn[RiskCategory] = "Low")` | Healthy base |
| `VIP Customers` | `VIP Customers = CALCULATE([Total Customers], FactChurn[HealthBand] = "VIP")` | Highest-value customers |
| `Customer Segment Count` | `Customer Segment Count = DISTINCTCOUNT(FactCustomer[Segment])` | Segment distribution |
| `Recommended Action Count` | `Recommended Action Count = DISTINCTCOUNT(FactChurn[RecommendedAction])` | Action diversity |

## Dynamic KPI Utilities
| Measure | DAX | Notes |
| --- | --- | --- |
| `Target Value` | `Target Value = SELECTEDVALUE('KPI Targets'[TargetValue])` | Requires a disconnected target table |
| `Dynamic KPI` | `Dynamic KPI = SWITCH(SELECTEDVALUE('KPI Selector'[KPI]), "Revenue", [Total Revenue], "Profit", [Gross Profit], "Orders", [Total Orders], "Customers", [Total Customers], "Churn Rate", [Churn Rate], "Inventory Cost", [Inventory Cost], "Forecast Revenue", [Forecast Revenue], [Total Revenue])` | Supports field-parameter style switching |
| `Variance` | `Variance = [Dynamic KPI] - [Target Value]` | Target variance |
| `Target Achievement %` | `Target Achievement % = DIVIDE([Dynamic KPI], [Target Value])` | Target completion rate |

## Calculated Columns
| Table | Column | DAX | Notes |
| --- | --- | --- | --- |
| `DimDate` | `Year` | `Year = YEAR(DimDate[Date])` | Calendar year |
| `DimDate` | `Quarter` | `Quarter = "Q" & FORMAT(DimDate[Date], "Q")` | Quarter label |
| `DimDate` | `Month` | `Month = FORMAT(DimDate[Date], "MMMM")` | Display month |
| `DimDate` | `Week` | `Week = WEEKNUM(DimDate[Date], 2)` | ISO-style week number |
| `DimDate` | `Day` | `Day = DAY(DimDate[Date])` | Day of month |
| `DimDate` | `Season` | `Season = SWITCH(TRUE(), MONTH(DimDate[Date]) IN {12,1,2}, "Winter", MONTH(DimDate[Date]) IN {3,4,5}, "Spring", MONTH(DimDate[Date]) IN {6,7,8}, "Summer", "Autumn")` | Retail season |
| `DimDate` | `Weekend` | `Weekend = IF(WEEKDAY(DimDate[Date], 2) > 5, "Weekend", "Weekday")` | Traffic and demand bucket |
| `DimCustomer` | `Customer Segment` | `Customer Segment = COALESCE(LOOKUPVALUE(FactChurn[CustomerSegment], FactChurn[CustomerID], DimCustomer[CustomerID]), LOOKUPVALUE(FactCustomer[Segment], FactCustomer[CustomerID], DimCustomer[CustomerID]), "Unassigned")` | Preferred customer label |
| `DimCustomer` | `Risk Category` | `Risk Category = COALESCE(LOOKUPVALUE(FactChurn[RiskCategory], FactChurn[CustomerID], DimCustomer[CustomerID]), "Unknown")` | Churn-focused risk tag |
| `FactForecast` | `Forecast Bucket` | `Forecast Bucket = SWITCH(TRUE(), FactForecast[HorizonDays] <= 30, "0-30 Days", FactForecast[HorizonDays] <= 90, "31-90 Days", FactForecast[HorizonDays] <= 180, "91-180 Days", "181+ Days")` | Planning horizon grouping |
| `FactInventory` | `Inventory Status` | `Inventory Status = SWITCH(TRUE(), FactInventory[InventoryRiskLevel] IN {"Critical", "High"} || FactInventory[StockCoverageDays] < 14, "Critical", FactInventory[InventoryRiskLevel] = "Medium" || FactInventory[StockCoverageDays] < 30, "Watch", FactInventory[InventoryRiskLevel] = "Low" && FactInventory[StockCoverageDays] > 120, "Overstock", "Balanced")` | Operational stock state |
| `FactChurn` | `Health Status` | `Health Status = SWITCH(TRUE(), FactChurn[CustomerHealthScore] >= 80, "Healthy", FactChurn[CustomerHealthScore] >= 60, "Watch", FactChurn[CustomerHealthScore] >= 40, "At Risk", "Critical")` | Retention readiness label |

## Support Tables
- `KPI Targets`: disconnected manual table with `KPI Name`, `TargetValue`, and `TargetPeriod`.
- `KPI Selector`: field parameter or disconnected slicer table used by `Dynamic KPI`.
