# User Guide

This walks through using the dashboard. For the API directly, see
[`docs/API.md`](API.md).

> **Note on screenshots:** this guide describes the actual UI rather than
> showing screenshots — the environment this project was built in doesn't
> have a browser available to capture real ones, and generating fake
> mockups pretending to be screenshots isn't something worth doing. Run
> the app locally (see the [README](../README.md#local-development)) to
> see it directly; it's a five-minute setup.

## 1. Create an account

Go to `http://localhost:5173/register`. Enter a name, email, and a
password (minimum 8 characters). You're signed in automatically after
registering — no separate login step.

## 2. Sign in

If you already have an account, `http://localhost:5173/login`. Sessions
persist across browser refreshes (the token is stored in `localStorage`)
until it expires (1 hour) or you log out.

## 3. Upload a scan

On the dashboard, drag a `.zip` file onto the upload area, or click it to
browse. Only `.zip` archives are accepted, up to 20MB. The scan runs
synchronously — you're taken straight to the results page once it
completes (typically well under a second for a small-to-medium codebase).

## 4. Read the results

The scan detail page shows:

- **Compliance gauge** — a radial indicator, colour-coded green/amber/red,
  showing the compliance percentage (100 minus the weighted risk score;
  see [`docs/SCANNER_DESIGN.md`](SCANNER_DESIGN.md#scoring) for the exact
  formula).
- **Severity breakdown chart** — a bar chart of how many findings fell
  into each severity tier.
- **Findings table** — every individual detection: which rule fired, the
  file and line number, and a redacted snippet (never the raw sensitive
  value — see [`SECURITY.md`](../SECURITY.md)).

## 5. Download the report

Click "Download report" to get a JSON file with the full scan results —
useful for archiving or feeding into another tool. This opens a presigned
S3 URL in a new tab, valid for 1 hour. If you see "No report is available
for this scan yet," it means S3 storage wasn't reachable when the scan
ran (see [`docs/AWS_INTEGRATION.md`](AWS_INTEGRATION.md)) — the scan
results themselves are still fully valid and viewable, just not
downloadable as a file.

## 6. Review past scans

The dashboard lists every scan you've run, most recent first, with
status and file count. Click any row to revisit its results.

## Signing out

Click "Log out" in the top nav. This clears your session locally — there's
no server-side session invalidation (a stateless JWT is valid until it
expires, whether or not you've logged out client-side; see the "Known
limitations" section of [`SECURITY.md`](../SECURITY.md)).
