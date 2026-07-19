# RetailPulse Star Schema Blueprint

## Logical Layout

```text
                 DimDate
                    |
 DimCustomer --- FactSales --- DimProduct
      |              |             |
      |              |             |
   FactCustomer   FactForecast   FactInventory --- DimWarehouse
      |              |             |
      |              |             |
   FactChurn ---- DimCountry ---- DimCategory
```

## Design Summary
- `FactSales` is the core transactional fact and should anchor revenue, profit, order, and product analysis.
- `FactForecast` is the planning fact and should be used for demand trends, horizon views, model comparison, and forecast accuracy.
- `FactInventory` is the operational optimization fact and should drive replenishment, stock coverage, service level, and warehouse analysis.
- `FactCustomer` is the customer intelligence snapshot fact and should power RFM, segment, CLV, and customer lifetime views.
- `FactChurn` is the retention snapshot fact and should power churn, health, risk, and recommended action analysis.

## Key Strategy
- Use integer surrogate keys wherever possible.
- Keep the original business identifiers as attributes, not as relationships.
- Build a product mapping query during Power Query import so product descriptions from forecast and inventory can resolve to the same `DimProduct`.
- Treat `SeriesKey` as a degenerate analysis field inside forecast and inventory facts, not as a replacement for the product dimension.
- Use a shared `DimDate` for transaction, forecast, inventory, and snapshot analysis.

## Relationship Rules
- All relationships flow from dimensions to facts.
- Avoid many-to-many relationships.
- Avoid bidirectional filters unless a specific calculation requires a temporary override.
- Use inactive date relationships only when a report page needs an alternate date role.
- Keep warehouse analysis limited to inventory facts unless a future bridge is explicitly introduced.

## Modeling Notes By Fact

### FactSales
- Grain: one row per invoice line.
- Primary business uses: revenue, quantity, profit, basket size, customer value, product mix, and geography.
- Best relationships: `DimDate`, `DimCustomer`, `DimProduct`, `DimCountry`, `DimCategory`.

### FactForecast
- Grain: one row per forecasted date and forecast series.
- Primary business uses: forecast evaluation, horizon planning, model comparison, and forecasted revenue.
- Best relationships: `DimDate`, `DimProduct`, `DimCountry`, `DimCategory`.

### FactInventory
- Grain: one row per product-country-category-horizon-date combination.
- Primary business uses: reorder point, safety stock, EOQ, risk, service level, and warehouse allocation.
- Best relationships: `DimDate`, `DimProduct`, `DimCountry`, `DimCategory`, `DimWarehouse`.

### FactCustomer
- Grain: one row per customer snapshot.
- Primary business uses: RFM, segmentation, CLV, customer tiering, and affinity analysis.
- Best relationships: `DimCustomer`, `DimDate`, `DimCountry`, `DimCategory`.

### FactChurn
- Grain: one row per customer snapshot.
- Primary business uses: churn, retention, health, next-purchase probability, and actions.
- Best relationships: `DimCustomer`, `DimDate`, `DimCountry`, `DimCategory`.

## Practical Implementation Sequence
1. Load `DimDate` and mark it as the date table.
2. Create the customer, product, country, category, and warehouse dimensions.
3. Load `FactSales` and verify that the row grain stays at invoice line level.
4. Load `FactForecast` and `FactInventory` using the same conformed product and country mapping.
5. Load `FactCustomer` and `FactChurn` as snapshot facts.
6. Hide surrogate keys, staging columns, and helper mapping tables from report view.
