# RetailPulse API Endpoints

All business endpoints require `X-API-Key` unless JWT bearer validation is configured.

## Health

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/health` | Liveness and artifact directory status |
| GET | `/version` | API name, version, and environment |
| GET | `/status` | Read-only artifact source availability |

## Forecast

| Method | Endpoint | Backing artifact |
| --- | --- | --- |
| GET | `/forecast` | `processed/forecast_results.csv` |
| GET | `/forecast/leaderboard` | `processed/leaderboard.csv` |
| GET | `/forecast/metrics` | `processed/forecast_metrics.csv` |
| GET | `/forecast/future` | `processed/future_predictions.csv` |

Example:

```bash
curl -H "X-API-Key: retailpulse-dev-api-key" \
  "http://127.0.0.1:8000/forecast/future?horizon_days=30&forecast_level=SKU&limit=3"
```

## Inventory

| Method | Endpoint | Backing artifact |
| --- | --- | --- |
| GET | `/inventory` | `processed/inventory_dataset.csv` |
| GET | `/inventory/recommendations` | `processed/inventory_recommendations.csv` |
| GET | `/inventory/risk` | `processed/inventory_risk.csv` |
| GET | `/inventory/abc` | `processed/abc_analysis.csv` |
| GET | `/inventory/xyz` | `processed/xyz_analysis.csv` |

## Customer

| Method | Endpoint | Backing artifact |
| --- | --- | --- |
| GET | `/customer/segments` | `processed/customer_segments.csv` |
| GET | `/customer/rfm` | `processed/rfm_table.csv` |
| GET | `/customer/clv` | `processed/customer_segments.csv` |
| GET | `/customer/health` | `processed/customer_health_scores.csv` |

## Churn

| Method | Endpoint | Backing artifact |
| --- | --- | --- |
| GET | `/churn` | `processed/customer_churn_predictions.csv` |
| GET | `/churn/predictions` | `processed/customer_churn_predictions.csv` |
| GET | `/churn/actions` | `processed/customer_business_actions.csv` |
| GET | `/churn/probabilities` | `processed/customer_probability_scores.csv` |

## Decision Intelligence

| Method | Endpoint | Backing artifact |
| --- | --- | --- |
| GET | `/decision` | `processed/business_decisions.csv` |
| GET | `/decision/alerts` | `processed/business_alerts.csv` |
| GET | `/decision/scenarios` | `processed/scenario_analysis.csv` |
| GET | `/decision/recommendations` | `processed/priority_actions.csv` |
| GET | `/decision/executive` | `processed/executive_summary.csv` |

## Analytics

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/analytics/overview` | Cross-domain enterprise overview |
| GET | `/analytics/kpis` | Compact KPI list |
| GET | `/analytics/summary` | Artifact coverage and counts |

## Reports

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/reports` | Catalog of reports, figures, CSV outputs, and models |
| GET | `/reports/download/{filename}` | Stream a whitelisted generated artifact |
| GET | `/reports/preview/{filename}` | JSON preview for CSV artifacts |

