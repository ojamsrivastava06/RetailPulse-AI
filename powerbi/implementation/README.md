# RetailPulse Power BI Implementation Blueprint

This folder turns the existing RetailPulse Power BI design specs into a buildable desktop implementation plan. It is documentation only: no PBIX files, no dataset rewrites, and no business logic changes.

## Canonical Inputs

- `../report_specification.md`
- `../dashboard_layout.md`
- `../data_model.md`
- `../star_schema.md`
- `../dax_measures.md`
- `../design_guidelines.md`
- `../interactivity_guidelines.md`
- `../performance_guidelines.md`
- `../business_kpis.md`

## Build Order

1. Read `project_setup.md` to confirm source files, naming, and refresh behavior.
2. Build the Power Query layer from `power_query.md`.
3. Create the semantic model from `data_model.md`.
4. Add the DAX catalog from `dax_catalog.md`.
5. Wire the report pages using the `page_checklists/` files.
6. Validate the visual map in `visual_inventory.md`.
7. Walk through `build_checklist.md`, then `qa_checklist.md`.
8. Hand off the model with `developer_handoff.md`.

## Folder Contents

- `project_setup.md` - source inventory, file order, and model conventions
- `power_query.md` - dataset-by-dataset loading and transformation notes
- `data_model.md` - semantic model, relationships, keys, and hidden fields
- `dax_catalog.md` - measure definitions, dependencies, and formatting guidance
- `visual_inventory.md` - master list of visuals and field bindings
- `build_checklist.md` - build sequence for Power BI Desktop
- `qa_checklist.md` - validation checklist before publish
- `developer_handoff.md` - implementation notes for the BI developer
- `page_checklists/` - one implementation file per report page

## Source Rules

- Use `data/processed/final_processed_dataset.csv` as the canonical sales fact.
- Use the `processed/*.csv` outputs as conformed subject-area inputs.
- Ignore `*.bak_*` files and keep `retailpulse_processed.csv` out of the model so sales rows are not duplicated.

## Design Standard

- Keep the model in Import mode.
- Build a star schema with single-direction relationships from dimensions to facts.
- Hide technical keys and staging queries.
- Use the existing `../theme.json` and `../theme-light.json` files for styling.
