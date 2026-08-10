# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning
follows [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-08-10

Initial release. Full stack, working end to end: register, log in, upload
a zip, get back scored findings, download a report.

### Added

- **Detection engine**: 4 POPIA data categories (SA ID numbers with
  checksum validation, email, SA phone numbers, bank account numbers with
  context validation) and 4 secret categories (AWS access keys, GitHub
  tokens, JWTs, generic password/API-key assignments). Redacted match
  storage, raw sensitive values never persisted.
- **REST API** (FastAPI): JWT auth, scan upload with zip-slip-protected
  extraction, findings retrieval, presigned report download URLs.
- **React dashboard**: login/register, drag-and-drop scan upload, a
  findings table with severity badges, a radial compliance gauge, and a
  severity breakdown chart.
- **S3 report storage**: JSON reports uploaded per scan, retrieved via
  presigned URL (fresh on each request, never stored). Best-effort, an
  S3 outage doesn't fail the underlying scan.
- **PostgreSQL schema** via SQLAlchemy + Alembic: users, scan jobs,
  findings, reports.
- **Docker**: development compose (Postgres + API + frontend, one
  command) and separate multi-stage production images for both services.
- **CI**: GitHub Actions running backend lint/tests and frontend
  lint/type-check/build on every push.
- **Documentation**: architecture and database design with rationale,
  scanner design doc, AWS integration guide with a least-privilege IAM
  policy, deployment guide.

### Fixed along the way

Real bugs caught during development, not just written and assumed
correct. Kept here rather than buried in commit history:

- SA-phone number regex never matched the `+27`-prefixed format  `\b`
  doesn't work as a word boundary before `+`.
- `passlib` 1.7.4 + `bcrypt` 5.x are incompatible (bcrypt dropped an
  attribute passlib's version probe depends on), causing every password
  hash to raise a spurious length error regardless of actual password
  length. Pinned `bcrypt==4.0.1`.
- `api.getScan()` was typed to return the lightweight `ScanJob` shape,
  but the backend endpoint actually returns the fuller `ScanResultRead`
  (findings + score) caught by `tsc`, not by manual testing.
- `datetime.utcnow()` (deprecated) replaced with a timezone-aware helper
  across all models and the scan service.

### Known limitations

See [`SECURITY.md`](SECURITY.md#known-limitations-not-vulnerabilities-but-worth-being-upfront-about)
and the "Scope" section of the [README](README.md#scope) — notably: no
RBAC, JWTs in `localStorage` rather than httpOnly cookies, no rate
limiting on auth endpoints, and production Docker images that follow
standard patterns but weren't build-tested (no Docker daemon available in
the development environment this project was built in).

## [Unreleased]

Nothing yet.
