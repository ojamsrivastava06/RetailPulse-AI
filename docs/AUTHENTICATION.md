# RetailPulse API Authentication

The API implements API key authentication now and a JWT-ready bearer layer for production integration.

## API Keys

Send API keys with the `X-API-Key` header:

```bash
curl -H "X-API-Key: retailpulse-dev-api-key" http://127.0.0.1:8000/analytics/kpis
```

The local default key is:

```text
retailpulse-dev-api-key
```

Override it by setting `RETAILPULSE_API_KEYS` to a comma-separated list:

```bash
set RETAILPULSE_API_KEYS=ops-key,bi-key,platform-key
```

## JWT-Ready Bearer Auth

Bearer auth is validated when `RETAILPULSE_JWT_SECRET` is set. The current implementation supports HS256 tokens using standard JWT fields:

- `sub`: subject identifier
- `scope`: space-separated scope list

Example header:

```text
Authorization: Bearer <jwt-token>
```

If `RETAILPULSE_JWT_SECRET` is not configured, bearer tokens are rejected and API keys remain the active authentication path.

## Open Endpoints

These endpoints are intentionally unauthenticated for probes:

- `GET /`
- `GET /health`
- `GET /version`
- `GET /status`

All capability, analytics, and report endpoints require credentials.

## Security Controls

- API key comparison uses constant-time matching.
- Rate limiting is enforced with an in-memory fixed window limiter.
- CORS is configured for local Streamlit and local web clients by default.
- Central exception handlers return a consistent error envelope.
- Security headers are added to all responses.

