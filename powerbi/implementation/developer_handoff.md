# Developer Handoff

## What Is In Scope

- Build the Power BI semantic model on top of the existing RetailPulse CSV outputs.
- Create the 12 report pages described in the implementation pack.
- Add the DAX measures, bookmarks, drillthrough pages, and slicer sync rules.
- Apply the existing enterprise theme files.

## What Is Not In Scope

- No PBIX generation in this repository.
- No dataset regeneration.
- No business logic changes upstream.
- No Streamlit, FastAPI, or deployment work.

## Source Of Truth

- Sales facts come from `data/processed/final_processed_dataset.csv`.
- Customer intelligence comes from the customer snapshot outputs in `processed/`.
- Forecasting comes from `processed/forecast_*.csv` and `processed/future_predictions.csv`.
- Inventory comes from `processed/inventory_*.csv`, `processed/abc_analysis.csv`, and `processed/xyz_analysis.csv`.

## Build Notes

- Keep `retailpulse_processed.csv` disabled so the sales fact is not duplicated.
- Treat `customer_model_leaderboard.csv` and `leaderboard.csv` as governance-only tables.
- Keep model tables in Import mode.
- Hide technical keys, helper sort columns, and staging queries.

## Assumptions

- Customer and product affinity fields are derived from the processed outputs, not from new source systems.
- Date intelligence is driven by a single shared `DimDate`.
- The developer will create manual `KPI Targets` and `KPI Selector` tables in Power BI Desktop.

## Acceptance Criteria

- The report opens with no broken relationships.
- The KPI cards match the approved measure definitions.
- The drillthrough paths work from every page that advertises them.
- The dashboard exports cleanly and reads correctly for an executive audience.

## Open Review Items

- Confirm whether the model will use the dark or light theme as the default publish variant.
- Confirm whether the forecast and inventory helper dashboard tables should remain hidden or be surfaced in a limited way.
- Confirm whether any additional executive bookmarks are needed beyond the ones listed in `report_specification.md`.
