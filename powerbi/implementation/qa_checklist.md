# QA Checklist

## Source And Refresh

- [ ] `final_processed_dataset.csv` is the only loaded sales source.
- [ ] `retailpulse_processed.csv` is excluded from load.
- [ ] Backup files with `.bak_` in the name are not loaded.
- [ ] The refresh completes without type conversion errors.

## Model

- [ ] All dimension-to-fact relationships are 1:*.
- [ ] All active relationships flow from dimensions to facts.
- [ ] `DimDate` is marked as the date table.
- [ ] Surrogate keys are hidden.
- [ ] Helper queries and governance tables are hidden from report view.

## Measures

- [ ] `Total Revenue`, `Total Orders`, and `Total Customers` return values in all expected filter contexts.
- [ ] Time intelligence measures respond correctly to the date slicer.
- [ ] Forecast and inventory measures return blanks only when the source data is actually empty.
- [ ] Target and variance measures resolve correctly when `KPI Selector` changes.

## Pages

- [ ] Each of the 12 pages uses the correct title and subtitle.
- [ ] Each page matches the intended canvas layout and spacing.
- [ ] Slicers and buttons are placed consistently.
- [ ] Bookmarks open the intended page state.

## Interactions

- [ ] Drillthrough works for customer, product, country, category, warehouse, and forecast series.
- [ ] Tooltips show the intended short-form context.
- [ ] Cross-highlighting does not distort executive summary pages.
- [ ] Sync slicers behave consistently across related pages.

## Accessibility And Formatting

- [ ] Theme colors match the dark or light standard.
- [ ] Text contrast is readable on projector and laptop displays.
- [ ] Red is reserved for risk and exception states.
- [ ] No page relies on color alone to convey meaning.

## Performance

- [ ] Executive pages stay visually sparse.
- [ ] High-cardinality tables remain behind drillthrough or detail views.
- [ ] Unused columns are removed from the final model.
- [ ] Any helper aggregation table still matches the detailed fact totals.

## Export

- [ ] Export to PDF preserves the layout.
- [ ] Exported pages show the intended titles and legends.
- [ ] No hidden table appears in exported visuals.
- [ ] The board-ready summary page remains readable when printed.
