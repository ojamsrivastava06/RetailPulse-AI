# RetailPulse API Launch Notes

This document covers local and server launch behavior only. The repository intentionally does not add Docker, Kubernetes, or deployment automation.

## Local Run

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

## Production-Like Run

Use the same ASGI app without reload:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Recommended environment variables:

```bash
set RETAILPULSE_ENV=production
set RETAILPULSE_API_KEYS=replace-with-secure-key
set RETAILPULSE_CORS_ORIGINS=https://your-streamlit-host.example.com
set RETAILPULSE_RATE_LIMIT_REQUESTS=120
set RETAILPULSE_RATE_LIMIT_WINDOW_SECONDS=60
```

Optional JWT:

```bash
set RETAILPULSE_JWT_SECRET=replace-with-jwt-secret
```

## Artifact Contract

The API assumes the completed RetailPulse phases have already produced these directories:

- `data/processed/`
- `processed/`
- `reports/`
- `models/`

The API reads these artifacts and never runs training, retraining, preprocessing, or artifact-write workflows.

## Operational Checks

Use:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/status
```

Then verify a secured endpoint:

```bash
curl -H "X-API-Key: retailpulse-dev-api-key" http://127.0.0.1:8000/decision/executive
```

