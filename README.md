# POPIA Guard

[![CI](https://github.com/denverstack/POPIA-Guard/actions/workflows/ci.yml/badge.svg)](https://github.com/denverstack/POPIA-Guard/actions/workflows/ci.yml)

Source code compliance scanner that detects POPIA-sensitive data and leaked
credentials in a codebase, then produces a report you can upload to S3 and
review in a dashboard.

> **Status:** v1.0.0 — feature-complete for this project's stated scope,
> full stack working end to end. See [ROADMAP](#roadmap) and
> [CHANGELOG](CHANGELOG.md) below.

## Why this exists

South Africa's Protection of Personal Information Act (POPIA) requires
organisations to know where personal information lives in their systems.
Source code and config files are a common, overlooked leak vector, hardcoded
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

There's no frontend test suite yet (component/E2E tests). See the roadmap.

## Folder structure

```
popia-guard/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # thin routers — validation + delegation only
│   │   ├── core/               # config, security, logging, exceptions
│   │   ├── db/                 # SQLAlchemy engine/session/base
│   │   ├── models/              # ORM models
│   │   ├── repositories/        # the only layer that queries the DB directly
│   │   ├── schemas/             # Pydantic request/response shapes
│   │   └── services/
│   │       ├── scanner/         # detection engine, rules, validators
│   │       ├── report/          # scoring + report document generation
│   │       └── storage/         # S3 client wrapper
│   ├── alembic/                 # migrations
│   ├── tests/
│   ├── Dockerfile.dev / Dockerfile.prod
│   └── requirements*.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # reusable UI (badges, gauge, chart, layout)
│   │   ├── pages/                # route-level components
│   │   └── lib/                  # API client, auth context
│   └── Dockerfile.dev / Dockerfile.prod
├── docker/docker-compose.yml     # full local stack, one command
├── infra/iam/                    # least-privilege S3 policy
├── docs/                         # see below
└── .github/workflows/ci.yml
```

## Documentation

| Doc | Covers |
|-----|--------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Layer breakdown, data flow, why not more layers |
| [`docs/DATABASE.md`](docs/DATABASE.md) | Schema, rationale, what's deliberately excluded |
| [`docs/SCANNER_DESIGN.md`](docs/SCANNER_DESIGN.md) | Detection rules, validators, scoring formula |
| [`docs/API.md`](docs/API.md) | Endpoint reference, auth, error format |
| [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) | Walkthrough of the dashboard |
| [`docs/AWS_INTEGRATION.md`](docs/AWS_INTEGRATION.md) | S3 setup, IAM policy, presigned URLs |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Production images, target deployment shape |
| [`SECURITY.md`](SECURITY.md) | Real security decisions made, and known limitations |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Dev setup, PR checklist, commit conventions |
| [`CHANGELOG.md`](CHANGELOG.md) | What shipped in v1.0.0 |

## Future improvements

Ideas for where this could go next, not commitments:

- Role-based access control (an `Admin` role that can see all scans, not
  just its own), the schema was deliberately left without a `role`
  column, but it's a one-line migration away if needed
- Async scan processing for large repositories (currently synchronous;
  fine at the file counts this is designed for, not for a 50k-file
  monorepo)
- Rate limiting on `/auth/*`
- A frontend test suite (component tests + a couple of E2E smoke tests)
- Additional report export formats (PDF, CSV) cut from v1.0.0 scope
  deliberately, see the Scope section above
- Entropy-based generic secret detection, with the false-positive tuning
  that requires. see the exclusions in `docs/SCANNER_DESIGN.md`

## Roadmap

- [x] Phase 1 — Project structure, architecture, database design
- [x] Phase 2 — Backend: auth, REST API, scanner engine implementation
- [x] Phase 3 — Frontend dashboard
- [x] Phase 4 — S3 integration
- [x] Phase 5 — CI pipeline
- [x] Phase 6 — Documentation pass and v1.0.0 release

## License

MIT — see [LICENSE](LICENSE).
