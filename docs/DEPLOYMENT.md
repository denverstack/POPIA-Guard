# Deployment

This covers the production Docker images and the deployment shape they're
built for. It's deliberately conceptual rather than an Infrastructure-as-Code
setup (Terraform/CloudFormation),  out of scope for this project; see the
[README](../README.md) for what's in and out of scope generally.

## Production images

Two separate images, each multi-stage to keep the final image lean:

- **`backend/Dockerfile.prod`** — installs dependencies in a builder
  stage, then copies only the installed packages (not build tools like
  `gcc`) into a slim runtime image, running as a non-root user.
- **`frontend/Dockerfile.prod`**  builds the static Vite bundle in a
  Node stage, then serves it from an nginx image with no Node runtime
  in the final image at all.

Build them:

```bash
docker build -f backend/Dockerfile.prod -t popia-guard-api:latest ./backend

docker build -f frontend/Dockerfile.prod \
  --build-arg VITE_API_BASE_URL=https://api.yourdomain.com/api/v1 \
  -t popia-guard-web:latest ./frontend
```

The frontend's API URL is a **build-time** argument, not a runtime env
var, Vite bakes it into the static bundle, so it has to point at wherever
the backend is actually reachable from a user's browser before you build.

**A note on verification:** these Dockerfiles were written following
standard multi-stage patterns (non-root user, minimal runtime deps,
healthchecks) but not build-tested — this sandbox doesn't have a Docker
daemon available. Run the build commands above before deploying to catch
anything environment-specific.

## Target deployment shape

Matches what's already described in
[`docs/ARCHITECTURE.md`](ARCHITECTURE.md#deployment-shape): a single EC2
instance (or equivalent), with:

- The two containers above running side by side (via `docker compose`
  with a production compose file, or run directly with `docker run`)
- **RDS PostgreSQL** instead of the containerized `db` service used in
  development
- **S3** for report storage, per [`docs/AWS_INTEGRATION.md`](AWS_INTEGRATION.md)
- A load balancer or reverse proxy in front, routing `/api/*` to the
  backend container's port 8000 and everything else to the frontend
  container's port 80, an Application Load Balancer with path-based
  routing is the natural fit given the rest of the stack is already AWS

## Migrations

Migrations are **not** run automatically on container start in
production (unlike the dev compose setup, which runs `alembic upgrade
head` before starting uvicorn, convenient for local iteration, risky in
production if multiple instances start simultaneously). Run them as a
separate, explicit step before rolling out a new version:

```bash
docker run --rm --env-file .env.production popia-guard-api:latest \
  alembic upgrade head
```

## Environment variables

Same variables as `.env.example`, with production values:

- `DATABASE_URL` — RDS connection string
- `JWT_SECRET_KEY` — a real random secret, not the dev default
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` — the IAM user credentials
  from `docs/AWS_INTEGRATION.md`, or omit both and use an EC2 instance
  role with the same policy attached instead (preferred  no long-lived
  credentials to rotate)
- `CORS_ALLOW_ORIGINS` the actual frontend origin, not `localhost`
