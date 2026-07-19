# RetailPulse Interactivity Guidelines

## Navigation
- Use a horizontal page navigator for executive users and a compact button rail for analysts.
- Reserve one primary landing page and make every other page accessible with one click.
- Keep page names short and business-facing.

## Bookmarks
- Use bookmarks for scenario switching, such as current vs forecast, detail vs summary, and risk vs opportunity views.
- Name bookmarks by intent, not by visual state, for example `Exec Summary`, `Risk Focus`, or `Action View`.
- Keep bookmark sets limited to what a user can explain in a meeting.

## Drillthrough
- Add drillthrough targets for customer, product, country, category, warehouse, and forecast series.
- Pass the minimum viable context: customer, product, country, category, horizon, and model.
- Use a detail page header that repeats the selected entity and key KPIs.

## Sync Slicers
- Sync `Date`, `Country`, `ProductCategory`, `CustomerSegment`, `RiskCategory`, and `Warehouse` slicers across all pages where relevant.
- Keep diagnostic slicers such as `Model`, `SeriesKey`, and `HorizonDays` page-specific.
- Hide slicers that are not part of the executive experience.

## Report Tooltips
- Use tooltips for compact KPI explanations, mini-trends, and context cards.
- Keep tooltip pages lightweight and focused on one entity.
- Use tooltips to expose supporting metrics that would otherwise crowd the canvas.

## Dynamic Titles And Labels
- Drive titles from selected date range, entity name, and current scenario.
- Keep labels short and readable in cards and charts.
- Use field parameters for metric switching instead of duplicating visuals.

## Field Parameters
- Use one field parameter for sales KPIs, one for inventory KPIs, and one for customer health KPIs.
- Include only metrics that make sense together in a single visual.
- Default the parameter to the executive headline metric on each page.

## Interaction Defaults
- Keep cross-highlighting on for exploratory pages and reduce it on executive pages if the story becomes noisy.
- Prefer single-select slicers for scenario controls and multi-select only for analysis pages.
- Limit interactive bookmarks to meaningful context changes, not cosmetic toggles.
