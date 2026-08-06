# POPIA Guard

Source code compliance scanner that detects POPIA-sensitive data and leaked
credentials in a codebase, then produces a report you can upload to S3 and
review in a dashboard.

> **Status:** Phase 1 — project scaffolding, architecture, and database
> design. Not yet functional end-to-end. See [ROADMAP](#roadmap) below.

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
| Frontend  | React, TypeScript, Vite, TailwindCSS               |
| Cloud     | Amazon S3 (report storage, presigned URLs)         |
| Auth      | JWT (password + bcrypt)                            |
| Testing   | Pytest                                             |
| Container | Docker, Docker Compose                             |
| CI        | GitHub Actions (lint + test)                       |

## Local development

```bash
cp .env.example .env
docker compose -f docker/docker-compose.yml up --build
```

The API will be available at `http://localhost:8000`, with interactive docs
at `http://localhost:8000/docs`.

## Running tests

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

## Roadmap

- [x] Phase 1 — Project structure, architecture, database design
- [ ] Phase 2 — Backend: auth, REST API, scanner engine implementation
- [ ] Phase 3 — Frontend dashboard
- [ ] Phase 4 — S3 integration
- [ ] Phase 5 — CI pipeline
- [ ] Phase 6 — Documentation pass and v1.0.0 release

## License

MIT — see [LICENSE](LICENSE).
