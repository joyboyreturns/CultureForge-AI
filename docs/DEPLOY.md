# Deploy

CultureForge deploys as **one Docker service**. FastAPI serves the built studio
at `/` and `/studio/` and the API at `/api/*` from the same origin, so a judge
needs no Node, no Qloo CLI and no key. The image bundles Node 22, Python 3.12,
the built UI and the Qloo harness (`@qloo/qloo-harness@0.1.26`), and calls
`https://hackathon.api.qloo.com` through `scripts/qloo_exec.mjs`, which sets a
60-second request timeout and disables the CLI's blind retries.

Secrets live only in the host's environment. Never pass them as build
arguments, and never copy `.env` into the image. `.dockerignore` excludes it.

## 1. Rehearse locally

```bash
cp .env.example .env        # then set QLOO_API_KEY (and the AI_GATEWAY_* values, if used)
docker compose up --build
```

Open `http://localhost:8000/studio/`. Evidence, the call ledgers
(`budget.db`) and saved explorations persist in the `cultureforge-data`
volume, mounted at `/data`.

## 2. Deploy on Render (blueprint included)

1. Push this repository to GitHub.
2. In Render: **New → Blueprint**, then pick the repository. Render reads
   [`render.yaml`](../render.yaml): one Docker web service, one instance, a
   1 GB disk at `/data`, and a health check on `/health`.
3. When prompted, enter the secret values: `QLOO_API_KEY`, and, if the model
   layer is wanted, `AI_GATEWAY_API_KEY` and `AI_GATEWAY_MODEL` with
   `AI_GATEWAY_ENABLED=true`. Leave `CULTUREFORGE_ALLOWED_ORIGINS` empty: the
   studio is served from the same origin.
4. Deploy. When the health check passes, run the smoke test:

   ```bash
   python3 scripts/smoke_test.py https://<your-service>.onrender.com
   ```

   It spends no Qloo quota. Until the briefs are prewarmed it reports that
   none is held.
5. Prewarm the prepared briefs into the service's own disk (this **does**
   spend quota, once per brief):

   ```bash
   python3 scripts/prewarm.py --live --base-url https://<your-service>.onrender.com
   ```

6. Record the public URL in [`submission.json`](../submission.json) and run
   `npm run check:release`.

Any host that runs a long-lived Docker web service with HTTPS, a persistent
volume, and requests of at least 120 seconds will do (Fly.io and Railway, for
example). Set the same environment variables, mount storage at `/data`
(writable by UID 10001), and point the health check at `/health`.

## Settings

| Variable | Value |
| --- | --- |
| `QLOO_API_KEY` | Your private hackathon key (secret) |
| `RUN_PROFILE` | `dev` while rehearsing; `judging` lifts every call-count budget ([JUDGING_DAY.md](JUDGING_DAY.md)) |
| `QLOO_LIVE_ENABLED` | `true`; `false` serves held evidence only |
| `QLOO_MAX_CALLS_PER_HOUR` / `_PER_DAY` | 20 / 100 (dev profile only) |
| `AI_GATEWAY_ENABLED` | `false`, or `true` to turn on naming, the agent loop and *Ask the evidence* |
| `AI_GATEWAY_API_KEY`, `AI_GATEWAY_MODEL` | Vercel AI Gateway key (secret) and model id, if enabled |
| `CULTUREFORGE_ALLOWED_ORIGINS` | Empty for same-origin; otherwise the exact studio origins, comma-separated |
| `CULTUREFORGE_KEY_SALT` | A long random string (the Render blueprint generates one). It salts the hashes of issued workspace API keys; the built-in default is for development only |
| `CULTUREFORGE_OPERATOR_TOKEN` | Unset unless operator administration is deliberately enabled |
| `PORT` | Set by most hosts; the container listens on it (default 8000) |

The Dockerfile sets `CULTUREFORGE_PROVIDER=qloo`, the trusted Qloo base URL,
and the `/data` paths.

## Constraints

- **One process, one instance.** Research runs and in-flight de-duplication
  are held in memory. The call ledgers are SQLite and safe across workers,
  but the rest is not, so do not scale out or add workers.
- **Keep the disk.** Losing `/data` loses held evidence, quota history, saved
  explorations and share links. The prewarm then has to be repeated.
- **Health is not retrieval.** `/api/health` reports configuration, the
  profile, budgets and cache size without calling Qloo. Use the smoke test
  and a click-through to confirm real retrieval.
- **Shared demo workspace.** Anonymous visitors share one workspace. Use
  non-confidential example briefs.

## Status of these instructions

Not yet verified end to end. The Dockerfile, `docker-compose.yml` and
`render.yaml` were written and reviewed, but no image was built here, because
no Docker daemon was available. The smoke test was run against a local
server. Build the image and deploy once before relying on these steps.
