# Build Checklist

## 1. Prepare The Workspace

- [ ] Confirm the source files listed in `project_setup.md`.
- [ ] Import `theme.json` or `theme-light.json`.
- [ ] Create a new PBIX with a 16:9 canvas.
- [ ] Set the file naming convention and report page names before building visuals.

## 2. Build Power Query

- [ ] Load the sales staging query from `final_processed_dataset.csv`.
- [ ] Create the conformed dimensions from reference queries.
- [ ] Merge customer, forecast, and inventory enrichment tables into their fact tables.
- [ ] Disable load for staging, duplicate, and governance-only tables.

## 3. Build The Model

- [ ] Create `DimDate`, `DimCustomer`, `DimProduct`, `DimCountry`, `DimCategory`, and `DimWarehouse`.
- [ ] Create `FactSales`, `FactForecast`, `FactInventory`, `FactCustomer`, and `FactChurn`.
- [ ] Add `KPI Targets` and `KPI Selector` as disconnected tables.
- [ ] Mark `DimDate` as the date table.
- [ ] Hide all surrogate keys and helper columns.

## 4. Add Measures

- [ ] Add the measures from `dax_catalog.md`.
- [ ] Validate that base measures work before adding derived measures.
- [ ] Apply currency and percentage formatting consistently.
- [ ] Confirm that target-driven measures use `KPI Targets`.

## 5. Build The Pages

- [ ] Create the 12 report pages in the same order as `report_specification.md`.
- [ ] Add the page-specific layout and positions from `page_checklists/`.
- [ ] Add navigation buttons and page bookmarks.
- [ ] Add report tooltips where specified.

## 6. Wire Interactions

- [ ] Sync date, country, category, customer, and warehouse slicers where relevant.
- [ ] Configure drillthrough pages for customer, product, country, category, warehouse, and forecast series.
- [ ] Check cross-highlighting on exploratory pages and reduce noise on executive pages.

## 7. Validate Performance

- [ ] Remove unused columns from staging queries.
- [ ] Keep only essential visuals on summary pages.
- [ ] Test report responsiveness in Power BI Desktop.
- [ ] Confirm that any aggregation tables still align with the base facts.

## 8. Finalize

- [ ] Run the QA checklist.
- [ ] Review each page in export and presentation view.
- [ ] Save the PBIX.
- [ ] Share the implementation package with the BI developer.
