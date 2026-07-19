# RetailPulse Enterprise API Guide

The Enterprise API is a read-only FastAPI backend over the completed RetailPulse artifacts. It reuses:

- `processed/` generated forecast, inventory, churn, customer, and decision tables
- `data/processed/` curated transactional datasets
- `reports/` markdown reports and generated figures
- `models/` saved model artifacts for catalog and governance visibility

It does not retrain models, overwrite datasets, or invoke pipeline write paths.

## Launch

Start the API from the repository root:

```bash
uvicorn api.main:app --reload
```

The legacy service entry point also points to the same app:

```bash
uvicorn service.main:app --reload
```

Default local documentation URLs:

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
- Redoc: `http://127.0.0.1:8000/redoc`

## Authentication

Health endpoints are open. Business endpoints require an API key by default:

```bash
curl -H "X-API-Key: retailpulse-dev-api-key" http://127.0.0.1:8000/forecast/future?limit=5
```

Set production API keys with:

```bash
set RETAILPULSE_API_KEYS=key-one,key-two
```

JWT bearer validation is ready for HS256 tokens when `RETAILPULSE_JWT_SECRET` is configured.

## Standard Response

JSON endpoints return:

```json
{
  "status": "success",
  "message": "Forecast results returned.",
  "timestamp": "2026-07-06T18:30:00+00:00",
  "data": [],
  "metadata": {
    "dataset": "forecast_results",
    "total_records": 450,
    "returned_records": 5,
    "limit": 5,
    "offset": 0
  }
}
```

`/reports/download/{filename}` streams a whitelisted generated artifact as a file download.

## Pagination And Filtering

Most table endpoints support:

- `limit`: records to return, default `100`, maximum `1000`
- `offset`: records to skip, default `0`
- Domain filters such as `product`, `country`, `category`, `risk_level`, `customer_id`, `domain`, or `priority`

Example:

```bash
curl -H "X-API-Key: retailpulse-dev-api-key" \
  "http://127.0.0.1:8000/inventory/risk?risk_level=High&limit=10"
```

## Streamlit Integration

The API and Streamlit app read the same generated artifacts. Run Streamlit separately with:

```bash
streamlit run app/Home.py
```

The default CORS configuration allows local Streamlit at `localhost:8501` and `127.0.0.1:8501`.

