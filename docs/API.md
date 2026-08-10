# API Reference

Full interactive documentation (Swagger UI, generated directly from the
code — request/response schemas, try-it-out) is available at
`http://localhost:8000/docs` when the API is running. The raw OpenAPI
spec is also exported to [`docs/openapi.json`](openapi.json) in this repo
for reference without running the app.

## Authentication

All endpoints except `/health` and `/auth/*` require a bearer token:

```
Authorization: Bearer <access_token>
```

Obtained from `POST /auth/login`. Tokens expire after 60 minutes
(`ACCESS_TOKEN_EXPIRE_MINUTES` in `.env`).

## Endpoints

| Method | Path                        | Auth | Description |
|--------|-----------------------------|------|-------------|
| POST   | `/api/v1/auth/register`     | No   | Create an account |
| POST   | `/api/v1/auth/login`        | No   | Exchange credentials for a JWT |
| POST   | `/api/v1/scans`             | Yes  | Upload a `.zip`, scan it, return findings + score |
| GET    | `/api/v1/scans`             | Yes  | List your scans (metadata only, no findings) |
| GET    | `/api/v1/scans/{id}`        | Yes  | Full scan detail: findings + recomputed score |
| GET    | `/api/v1/scans/{id}/findings` | Yes | Findings only, lighter-weight than the above |
| GET    | `/api/v1/scans/{id}/report` | Yes  | Presigned S3 URL for the stored report (1hr expiry) |
| GET    | `/health`                   | No   | Liveness check |

Every `/scans/*` endpoint is scoped to the authenticated user, there's no
way to read another user's scan by guessing an ID (404, not 403, to avoid
confirming the ID exists at all).

## Error format

All errors return a consistent shape:

```json
{ "detail": "human-readable message" }
```

Status codes are meaningful, not just 400/500 for everything:

| Status | Meaning |
|--------|---------|
| 400    | Bad request — invalid file type, corrupt zip, oversized upload |
| 401    | Missing/invalid/expired token, or wrong credentials |
| 404    | Resource doesn't exist or isn't yours |
| 409    | Email already registered |
| 502    | Report storage (S3) unreachable |

See [`app/core/exceptions.py`](../backend/app/core/exceptions.py) for the
full exception → status code mapping.

## Example: full flow

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"a-strong-password","full_name":"Your Name"}'

TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"a-strong-password"}' | jq -r .access_token)

curl -X POST http://localhost:8000/api/v1/scans \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@my-project.zip"
```

(Requires [`jq`](https://jqlang.org/) for the token extraction shown
here. See the README's Quick Start for a version without it.)
