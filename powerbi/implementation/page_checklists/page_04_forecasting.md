# Page 04 Demand Forecasting

## Purpose

Compare model quality and plan future demand by product, geography, and forecast horizon.

## Canvas And Grid

- Canvas: 16:9 widescreen, 1600 x 900 px design base.
- Grid: 8 px spacing system.
- Margins: 24 px outer margin.
- Header band: 96 px.

## Layout

- KPI strip at the top.
- Actual vs forecast trend dominates the center.
- Model ranking and residual analysis anchor the lower half.

## Visual Map

| ID | Type | Position | Main Fields |
| --- | --- | --- | --- |
| `DF-01` | KPI cards | `x24 y112 w1552 h92` | `Forecast Revenue`, `Forecast Demand`, `Forecast Accuracy %`, `MAPE`, `Forecast Error`, `Best Model Count` |
| `DF-02` | Line chart | `x24 y224 w1040 h250` | `Date`, `Actual`, `Forecast`, `Lower95`, `Upper95` |
| `DF-03` | Bar chart | `x1088 y224 w488 h250` | `Model`, `Forecast Accuracy %`, `MAPE` |
| `DF-04` | Histogram or scatter | `x24 y500 w760 h292` | `Residual`, `ResidualStd`, `Model` |
| `DF-05` | Matrix | `x808 y500 w768 h292` | `Product`, `Country`, `HorizonDays`, `Forecast Demand`, `Forecast Revenue` |

## Titles And Labels

- Title: `Demand Forecasting`.
- Subtitle: evaluation rows, future horizon, and model comparison context.
- Show the current horizon and model choice in the subtitle.

## Icons And Buttons

- Use a forecast or trend icon in the title band.
- Add navigation buttons to inventory and product pages.

## Filters And Slicers

- Slicers: `Model`, `HorizonDays`, `Product`, `Country`, `ProductCategory`.
- Keep diagnostic slicers page-specific.

## Bookmarks

- `Current Horizon`
- `Long Horizon`
- `Model Comparison`

## Tooltips And Drillthrough

- Tooltip: forecast value, confidence band, and error summary.
- Drillthrough: forecast series detail and model comparison detail.

## Dynamic Titles

- Reflect the selected model and horizon in the page title.

## Conditional Formatting

- Use color bands for forecast confidence intervals and error severity.
- Highlight the best-performing model in the ranking chart.

## Interaction Notes

- Keep the actual-vs-forecast line as the first story on the page.
- Use cross-highlighting carefully so the residual view does not overpower the trend.

## Export Notes

- Confidence bands and axis labels must remain readable in export.
