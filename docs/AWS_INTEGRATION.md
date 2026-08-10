# AWS Integration

POPIA Guard uses a single S3 bucket to store generated scan reports as
JSON objects. This document covers how that's set up and secured.

## What's stored, and where

Each completed scan produces a JSON report (see
[`app/services/report/generator.py`](../backend/app/services/report/generator.py))
uploaded to:

```
s3://<bucket>/reports/<user_id>/<scan_id>.json
```

Only the object key is persisted in PostgreSQL (the `Report.s3_key`
column — see [`docs/DATABASE.md`](DATABASE.md)). No long-lived URL is
stored, because presigned URLs expire; `GET /scans/{id}/report` generates
a fresh one (1 hour expiry) on every request.

## Bucket setup

1. Create a bucket (region should match `AWS_REGION` in your `.env` —
   defaults to `af-south-1`).
2. Enable **Block all public access** — nothing in this bucket is ever
   meant to be publicly reachable. All access goes through presigned URLs
   issued by the API on behalf of an authenticated, authorized user, or
   through the IAM credentials below.
3. No bucket policy is required beyond the default (private) — access is
   controlled entirely via the IAM policy below, not bucket-level rules.

## IAM policy

The API needs exactly two permissions, scoped to the `reports/` prefix
only — not the whole bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PopiaGuardReportReadWrite",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject"],
      "Resource": "arn:aws:s3:::popia-guard-reports/reports/*"
    }
  ]
}
```

Full policy: [`infra/iam/s3-report-access-policy.json`](../infra/iam/s3-report-access-policy.json)
— update the bucket name in the `Resource` ARN if yours differs from the
default.

Deliberately excluded: `s3:ListBucket` (the app never lists objects, only
reads/writes known keys), `s3:DeleteObject` (no deletion flow exists),
and any action outside the `reports/` prefix.

To create the IAM user and attach this policy via the AWS CLI:

```bash
aws iam create-user --user-name popia-guard-api
aws iam put-user-policy \
  --user-name popia-guard-api \
  --policy-name PopiaGuardReportReadWrite \
  --policy-document file://infra/iam/s3-report-access-policy.json
aws iam create-access-key --user-name popia-guard-api
```

Put the resulting access key ID and secret into `.env` as
`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`.

## Behaviour without AWS credentials configured

`.env.example` ships with blank AWS credentials. With no credentials
configured, **scanning still works fully** — findings are detected,
scored, and returned — but report storage silently fails and is skipped
(see `scan_service._try_store_report`, which treats S3 as best-effort and
logs a warning rather than failing the scan). `GET /scans/{id}/report`
will 404 in that case. This is a deliberate resilience choice: an S3
outage or missing credentials shouldn't take down the core scanning
feature.

## How this was tested

This project doesn't have a live AWS account wired up for automated
testing. The S3 integration is tested against a mocked S3 backend
([`moto`](https://github.com/getmoto/moto)) — every backend test runs
inside a mocked AWS environment via an autouse pytest fixture, so no test
ever makes a real network call to AWS. The integration test for the
report endpoint goes as far as actually issuing an HTTP GET against the
generated presigned URL and checking the returned content matches what
was scanned — not just asserting the URL string looks plausible.

Before pointing this at a real bucket, verify manually: set real
credentials in `.env`, run a scan, and confirm `GET /scans/{id}/report`
returns a URL that downloads the expected JSON.
