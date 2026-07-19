# RetailPulse Performance Guidelines

## Storage Mode
- Use Import mode for the current file-based implementation.
- Keep DirectQuery as a future option only if the project moves to a managed warehouse or lakehouse.
- Do not mix storage modes unless the source architecture requires it.

## Aggregations
- Build summary tables for executive pages, especially by month, country, category, segment, and horizon.
- Use aggregate tables for forecast and inventory views when the fact grain becomes too detailed for the executive canvas.
- Keep transaction-level visuals behind drillthrough pages.

## Incremental Refresh
- Enable incremental refresh on `FactSales`, `FactForecast`, `FactInventory`, and `FactChurn` using their date columns.
- Partition by recent refresh windows and preserve a long historical range for trend analysis.
- Keep the refresh window aligned with the business cadence, not just the technical schedule.

## Query And Model Optimization
- Push cleaning and shaping into Power Query before creating calculated columns.
- Prefer surrogate integer keys over text joins.
- Avoid bidirectional relationships unless a specific calculation needs them.
- Hide technical columns, helper columns, and staging queries from report view.
- Keep calculated columns to a minimum on large fact tables.

## DAX Optimization
- Prefer simple measures over repeated iterator-heavy expressions.
- Reuse base measures such as `Total Revenue`, `Total Orders`, and `Total Customers`.
- Use variables in complex measures to reduce repeated evaluation.
- Avoid `SUMX` and `FILTER` on very large tables unless the logic truly requires them.

## Visual Optimization
- Keep each page focused on one executive question.
- Limit each page to the visuals needed for the decision.
- Avoid high-cardinality tables on overview pages.
- Reduce the use of custom visuals that are not essential to the story.

## Monitoring
- Use Performance Analyzer to identify expensive visuals and DAX queries.
- Review model size, refresh duration, and interaction latency after each major change.
- Validate that report pages still feel responsive after adding drillthrough, tooltips, or field parameters.
