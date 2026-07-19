# Project Setup

## Goal

Set up a Power BI Desktop project that reuses the existing RetailPulse outputs without changing the upstream pipeline.

## Recommended Folder Structure

```text
powerbi/
  theme.json
  theme-light.json
  report_specification.md
  dashboard_layout.md
  data_model.md
  star_schema.md
  dax_measures.md
  design_guidelines.md
  interactivity_guidelines.md
  performance_guidelines.md
  business_kpis.md
  implementation/
    README.md
    project_setup.md
    power_query.md
    data_model.md
    dax_catalog.md
    visual_inventory.md
    build_checklist.md
    qa_checklist.md
    developer_handoff.md
    page_checklists/
```

## Source Loading Order

1. `data/processed/final_processed_dataset.csv`
2. `processed/rfm_table.csv`
3. `processed/customer_segments.csv`
4. `processed/customer_retention_metrics.csv`
5. `processed/customer_churn_predictions.csv`
6. `processed/customer_health_scores.csv`
7. `processed/customer_probability_scores.csv`
8. `processed/customer_business_actions.csv`
9. `processed/customer_model_leaderboard.csv`
10. `processed/forecast_results.csv`
11. `processed/future_predictions.csv`
12. `processed/forecast_metrics.csv`
13. `processed/forecast_dashboard.csv`
14. `processed/forecast_comparison.csv`
15. `processed/inventory_dataset.csv`
16. `processed/inventory_metrics.csv`
17. `processed/inventory_risk.csv`
18. `processed/inventory_recommendations.csv`
19. `processed/inventory_dashboard.csv`
20. `processed/abc_analysis.csv`
21. `processed/xyz_analysis.csv`
22. `processed/abc_xyz_matrix.csv`
23. `processed/segment_summary.csv`
24. `processed/leaderboard.csv`

## Import Settings

- Use Import mode for every table.
- Promote the first row to headers.
- Disable implicit type detection on staging queries and set types deliberately after cleaning.
- Use comma-delimited CSV imports with UTF-8 encoding.
- Force date and date-time columns to explicit `date` or `datetime` types.
- Convert business identifiers such as `CustomerID` to whole number or text consistently before relationship creation.

## Refresh Strategy

- Refresh the model from the processed CSV outputs after the upstream pipeline finishes.
- Rebuild the semantic model on every refresh because the current source pattern is file-based.
- If the files are later moved to a folding-capable source, incremental refresh can be layered on top of the same model design.
- Keep the duplicate compatibility file `retailpulse_processed.csv` excluded from refresh and load.

## Naming Conventions

- `stg_*` for staging queries.
- `dim_*` for dimension queries.
- `fact_*` for fact queries.
- `agg_*` for helper aggregation tables.
- `KPI Targets` and `KPI Selector` for disconnected control tables.
- Page names should stay business-facing: `Executive Dashboard`, `Sales Analytics`, and so on.
- Bookmarks should use intent-based names such as `Risk Focus` or `Opportunity Focus`.

## Required Datasets

- Sales: `final_processed_dataset.csv`
- Customer intelligence: `rfm_table.csv`, `customer_segments.csv`, `customer_retention_metrics.csv`, `customer_churn_predictions.csv`, `customer_health_scores.csv`, `customer_probability_scores.csv`, `customer_business_actions.csv`
- Forecasting: `forecast_results.csv`, `future_predictions.csv`, `forecast_metrics.csv`, `forecast_dashboard.csv`, `forecast_comparison.csv`
- Inventory: `inventory_dataset.csv`, `inventory_metrics.csv`, `inventory_risk.csv`, `inventory_recommendations.csv`, `inventory_dashboard.csv`, `abc_analysis.csv`, `xyz_analysis.csv`, `abc_xyz_matrix.csv`
- Governance and comparison: `customer_model_leaderboard.csv`, `leaderboard.csv`, `segment_summary.csv`

## Power Query Loading Sequence

1. Load the sales staging table and clean transaction-level types.
2. Build the product, customer, country, category, and warehouse dimensions from reference queries.
3. Load the customer snapshot tables and merge them into `FactCustomer` and `FactChurn`.
4. Load the forecast evaluation and future forecast tables and standardize them into `FactForecast`.
5. Load the inventory planning tables and standardize them into `FactInventory`.
6. Load the disconnected target and selector tables.
7. Hide staging queries, duplicate compatibility files, and governance-only tables from report view.
