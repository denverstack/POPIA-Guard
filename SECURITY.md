# Security Policy

## Reporting a vulnerability

This is a portfolio/demonstration project, not a monitored production
service. If you find a security issue, please open a GitHub issue
describing it. For a project at this stage, a public issue is fine
rather than a private disclosure process, but use your judgement if
you've found something that would be actively harmful if exploited before
a fix lands.

## Supported versions

Only the latest commit on `master` is supported. There's no LTS branch or
backport policy at this stage.

## Security decisions already made in this codebase

Documenting these here rather than just in code comments, since "what did
you actually think about" is more useful in one place than scattered
across files:

- **Zip-slip protection on uploads** ([`app/services/archive.py`](backend/app/services/archive.py)) 
  every archive member's resolved path is checked to stay inside the
  extraction directory before anything is extracted. Verified against an
  actual crafted exploit archive during development (a `../../../tmp/...`
  path), not just written and assumed correct.
- **Passwords are hashed with bcrypt**, never stored or logged in plain
  text ([`app/core/security.py`](backend/app/core/security.py)).
- **Findings store redacted matches only**.  the raw sensitive value
  (an actual ID number, email, or credential) never gets written to the
  database. See `app/services/scanner/engine.py::redact` and the
  rationale in [`docs/DATABASE.md`](docs/DATABASE.md).
- **Every scan/finding query is scoped to the owning user**
  ([`app/repositories/scan_repository.py`](backend/app/repositories/scan_repository.py)) 
  There's no endpoint that returns another user's data by guessing an ID.
  Covered by a test (`test_get_scan_not_owned_by_user_returns_404`).
- **S3 access is least-privilege**, scoped to a single prefix with only
  `PutObject`/`GetObject`  see [`docs/AWS_INTEGRATION.md`](docs/AWS_INTEGRATION.md)
  and [`infra/iam/s3-report-access-policy.json`](infra/iam/s3-report-access-policy.json).
- **No secrets in the repo.** `.env` is gitignored; `.env.example` ships
  only placeholder/default values. AWS credentials are optional in local
  dev (see the "Behaviour without AWS credentials configured" section of
  `docs/AWS_INTEGRATION.md`).
- **Upload size is capped** (20MB) before any extraction happens, and
  vendored/binary paths are skipped during scanning. See
  [`docs/SCANNER_DESIGN.md`](docs/SCANNER_DESIGN.md) for what's explicitly
  out of scope (full zip-bomb defence, entropy-based secret detection).

## Known limitations (not vulnerabilities, but worth being upfront about)

- JWTs are stored in the frontend's `localStorage`, not an httpOnly
  cookie. A pragmatic simplification for this project's scope, not what
  a production auth system would do. An XSS vulnerability elsewhere in
  the app could exfiltrate a token; there's no CSP configured to mitigate
  that.
- No rate limiting on `/auth/login` or `/auth/register` brute-force
  protection would be needed before this went anywhere near production
  traffic.
- The JWT secret key defaults to a placeholder value in `.env.example`.
  This *must* be replaced with a real random secret before any real
  deployment.  see `docs/DEPLOYMENT.md`.
