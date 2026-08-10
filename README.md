# POPIA Guard

[![CI](https://github.com/denverstack/POPIA-Guard/actions/workflows/ci.yml/badge.svg)](https://github.com/denverstack/POPIA-Guard/actions/workflows/ci.yml)

Source code compliance scanner that detects POPIA-sensitive data and leaked
credentials in a codebase, then produces a report you can upload to S3 and
review in a dashboard.

> **Status:** Phase 5 complete — CI runs backend lint/tests and frontend
> lint/type-check/build on every push. See [ROADMAP](#roadmap) below.

## Why this exists

South Africa's Protection of Personal Information Act (POPIA) requires
organisations to know where personal information lives in their systems.
Source code and config files are a common, overlooked leak vector — hardcoded
test data, seeded fixtures, and `.env` files that made it into a commit all
count. POPIA Guard scans a repository or upload for that class of problem
alongside the more familiar secret-detection use case (API keys, tokens,
credentials).

## Scope

This is a focused implementation, not an attempt to rebuild a commercial DLP
suite. It covers:

- Pattern-based detection for a defined set of POPIA data categories and
  secret types (see [`docs/SCANNER_DESIGN.md`](docs/SCANNER_DESIGN.md))
- A scan → findings → report pipeline backed by PostgreSQL
- Report upload to S3 with presigned-URL retrieval
- A minimal dashboard to trigger scans and review results

It deliberately does **not** include role-based access control, an admin
console, or multi-format report export — those add surface area without
adding to the core demonstration of the detection engine and pipeline.

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full breakdown.
In short: a FastAPI service with a clean API → service → repository split,
PostgreSQL for persistence, S3 for report storage, and a React/TypeScript
frontend.

## Database design

See [`docs/DATABASE.md`](docs/DATABASE.md) for the schema and rationale.

## Tech stack

| Layer     | Choice                                             |
|-----------|-----------------------------------------------------|
| Backend   | FastAPI, SQLAlchemy, Alembic, Pydantic, PostgreSQL |
| Frontend  | React, TypeScript, Vite, TailwindCSS v4, TanStack Query, Chart.js |
| Cloud     | Amazon S3 (report storage, presigned URLs)         |
| Auth      | JWT (password + bcrypt)                            |
| Testing   | Pytest                                             |
| Container | Docker, Docker Compose                             |
| CI        | GitHub Actions (backend lint+test, frontend lint+build) |

## Local development

```bash
cp .env.example .env
docker compose -f docker/docker-compose.yml up --build
```

This brings up Postgres, the API, and the frontend together:

- Dashboard: `http://localhost:5173`
- API: `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`

### Running the frontend on its own

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Requires the API running separately (`docker compose up api db`, or run it
directly per the backend instructions below).

## Quick start (API)

Register, log in, and scan a zip of source files:

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "a-strong-password", "full_name": "Your Name"}'

# Log in — grab the access_token from the response
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "a-strong-password"}'

# Scan a zip of your project
curl -X POST http://localhost:8000/api/v1/scans \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@my-project.zip"

# List your past scans
curl http://localhost:8000/api/v1/scans \
  -H "Authorization: Bearer <access_token>"

# Get a fresh download link for the report (see docs/AWS_INTEGRATION.md)
curl http://localhost:8000/api/v1/scans/<scan_id>/report \
  -H "Authorization: Bearer <access_token>"
```

A scan response includes the computed findings, risk score, and compliance
percentage inline — see [`docs/SCANNER_DESIGN.md`](docs/SCANNER_DESIGN.md)
for what's detected and how findings are scored, and
[`docs/AWS_INTEGRATION.md`](docs/AWS_INTEGRATION.md) for how reports are
stored in S3. For running the production Docker images, see
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Running tests

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

### Frontend checks

```bash
cd frontend
npm install
npm run lint       # oxlint
npx tsc --noEmit -p tsconfig.app.json
npm run build
```

There's no frontend test suite yet (component/E2E tests) — see the roadmap.

## Roadmap

- [x] Phase 1 — Project structure, architecture, database design
- [x] Phase 2 — Backend: auth, REST API, scanner engine implementation
- [x] Phase 3 — Frontend dashboard
- [x] Phase 4 — S3 integration
- [x] Phase 5 — CI pipeline
- [ ] Phase 6 — Documentation pass and v1.0.0 release

## License

MIT — see [LICENSE](LICENSE).
