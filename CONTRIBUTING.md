# Contributing

## Setup

See the [README](README.md#local-development) for getting the full stack
running. For backend-only or frontend-only work:

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest

# Frontend
cd frontend
npm install
npm run dev
```

## Before opening a PR

Run the same checks CI runs:

```bash
# Backend
cd backend
ruff check app tests
pytest

# Frontend
cd frontend
npm run lint
npx tsc --noEmit -p tsconfig.app.json
npm run build
```

All four must pass — CI will block the merge otherwise (see
[`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## Commit messages

[Conventional Commits](https://www.conventionalcommits.org/):
`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `ci:`, `build:`. Keep the
summary line under ~72 characters; use the body to explain *why*, not
just *what* — the diff already shows what changed.

## Code style

- Backend: `ruff` enforces style; type hints are expected on function
  signatures. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the
  API → service → repository layering — new endpoints should follow it
  (routers stay thin, business logic goes in `services/`, DB queries go
  in `repositories/`).
- Frontend: `oxlint` enforces style. Components go in `src/components/`
  if reusable, `src/pages/` if route-level. Prefer TanStack Query for any
  new data fetching rather than manual `useEffect` + `fetch`.

## Adding a detection rule

New POPIA or secret patterns go in
`backend/app/services/scanner/patterns/`, following the existing `Rule`
shape. If the pattern is prone to false positives on a bare regex match
(the way SA ID numbers and bank account numbers are), add a validator in
`validators.py` rather than trying to make the regex itself more
precise — see `docs/SCANNER_DESIGN.md` for the reasoning. Add both a
positive and (if there's a validator) a negative test case to
`tests/test_scanner_engine.py`.

## Database changes

Add or modify a SQLAlchemy model in `backend/app/models/`, then generate
a migration:

```bash
cd backend
alembic revision --autogenerate -m "describe the change"
```

Review the generated migration before committing — autogenerate is a
starting point, not a guarantee of correctness, especially for renames
(it'll see a rename as a drop + add unless you edit it manually).
