# RetailPulse User Guide

## What This Report Is For
- This Power BI layer is the executive-facing analytics shell for the RetailPulse datasets.
- It does not replace the source pipeline or write new datasets.
- It is intended for business review, operational monitoring, and leadership decisions.

## Getting Started
1. Load the processed CSV outputs into Power BI Desktop.
2. Create the conformed dimensions and relationships described in `data_model.md`.
3. Import `theme.json` or `theme-light.json`.
4. Hide staging queries, helper columns, and technical keys from report view.
5. Publish only after validating the page filters, drillthrough targets, and measure results.

## How To Navigate
- Use the landing page first to understand overall health.
- Use the page navigator or button rail to move between subject areas.
- Use slicers to narrow the period, market, product set, customer segment, or warehouse.
- Use bookmarks when you want a preconfigured executive view instead of building one manually.

## How To Read The Pages
- `Executive Dashboard`: start here for the current story.
- `Sales Analytics`: use it to find what is growing and what is flattening.
- `Customer Intelligence`: use it to see which customer groups carry value.
- `Demand Forecasting`: use it to validate model quality and future demand.
- `Inventory Intelligence`: use it to decide what should be reordered or reduced.
- `Customer Churn`: use it to decide where retention work should go first.
- `Product Analytics`: use it to separate hero products from slow movers.
- `Geographic Analytics`: use it to understand country-level concentration and service gaps.
- `Financial Analytics`: use it to understand where profit is created or lost.
- `KPI Cockpit`: use it when a stakeholder wants to switch one metric across multiple perspectives.
- `AI Insights`: use it to understand why a metric changed and what action is recommended.
- `Executive Summary`: use it when preparing for a board or steering committee review.

## Drillthrough And Tooltips
- Right-click a customer, product, country, category, or series to open the related detail page.
- Use tooltips to show the short explanation before drilling into the report.
- Keep drillthrough pages focused on the selected entity and the few KPIs that matter most.

## Bookmarks And Field Parameters
- Bookmarks are best used for fixed business scenarios such as risk focus, opportunity focus, and summary packs.
- Field parameters are best used when the same visual needs to display multiple KPIs without duplicating the chart.
- If a page starts to feel crowded, replace repeated visuals with a parameter selector.

## Refresh And Maintenance
- Refresh the semantic model after the source CSVs are updated.
- Revalidate relationships when new fields are added to the processed datasets.
- Recheck any calculated columns or target tables if the business definitions change.
- Keep a short change log so business users know when the metric logic changed.

## Troubleshooting
- If a KPI looks blank, check the filter context first.
- If a drillthrough page returns no records, confirm that the selected field is mapped to the correct key.
- If a forecast or inventory measure looks inflated, verify the date range and horizon filters.
- If the report feels slow, switch to the performance guidance in `performance_guidelines.md`.
