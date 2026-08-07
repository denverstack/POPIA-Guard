# POPIA Guard — Frontend

React + TypeScript + Vite dashboard for POPIA Guard. See the [root README](../README.md) for the full project overview and quick start.

## Development

```bash
npm install
cp .env.example .env
npm run dev
```

Requires the backend API running (see `../backend/README.md`-equivalent instructions in the root README).

## Checks

```bash
npm run lint                              # oxlint
npx tsc --noEmit -p tsconfig.app.json     # type check
npm run build                             # production build
```
