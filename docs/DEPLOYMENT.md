# Publish the complete application

The frontend and API can run as **one Docker service**. FastAPI serves `dist/` at `/` and `/studio/`, with `/api/*` on the same origin. A static-only upload will not run the research service.

## Build and rehearse

```bash
docker build -t cultureforge .
docker run --rm -p 8000:8000 --env-file .env -v cultureforge-data:/data cultureforge
```

Docker packages Node 22, Python 3.12, the built UI, and Qloo harness 0.1.26. It sets the trusted hackathon endpoint without needing an interactive CLI setup. Supply a real `QLOO_API_KEY` in the private runtime environment. Never pass secrets as build arguments or copy `.env` into the image.

Open `http://localhost:8000/studio/`. `/api/health` reports configuration; it does not call Qloo or prove upstream availability. Complete the judge walkthrough to verify actual retrieval.

## Hosting configuration

Use a host that supports a long-running Docker web service, HTTPS, a persistent volume and requests lasting at least 120 seconds. Configure these values in the host's secret/environment panel:

| Setting | Value |
| --- | --- |
| QLOO_API_KEY | Your private hackathon key |
| CULTUREFORGE_PROVIDER | qloo |
| QLOO_BASE_URL | https://hackathon.api.qloo.com |
| QLOO_TRUSTED_BASE_URL | https://hackathon.api.qloo.com |
| QLOO_MAX_CALLS_PER_HOUR | 20, or a lower bound |
| QLOO_MAX_CALLS_PER_DAY | 100, or a lower bound |
| AI_GATEWAY_ENABLED | false, or true if deliberately enabling the model |
| AI_GATEWAY_API_KEY | Private Vercel key, if enabled |
| AI_GATEWAY_MODEL | Your configured Gateway model identifier, if enabled |

The container listens on `PORT`, default 8000. Mount durable storage at `/data`, writable by UID 10001. Keep one process and one replica: research runs and request de-duplication are held in memory; this is not a multi-instance architecture. Do not add workers as a performance workaround.

Evidence and all provider budget journals live under `/data/cache`; saved explorations and share links use `/data/platform.db`. Losing that volume loses saved links and quota history. A bind mount must be writable by the container user. The anonymous studio uses a shared demo workspace; use synthetic/non-confidential business briefs during public judging. Keep operator administration disabled unless you deliberately set a private `CULTUREFORGE_OPERATOR_TOKEN`.

For container-native health checks use `/health`. The Docker health command follows `PORT`. Keep the service awake and free to try throughout judging.

## Without Docker

Install Node 22.19+, Python 3.10+, Python requirements and the Qloo harness as described in README. Build the frontend, then run:

```bash
npm run build
CULTUREFORGE_STATIC_DIR="$PWD/dist" uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1
```

Set durable `CULTUREFORGE_CACHE_DIR` and `CULTUREFORGE_DB` paths on the host. Keep `/api` paths intact in any reverse proxy. No CORS customization is needed for same-origin deployment.

## Release verification

Record the public HTTPS root URL in `submission.json`, then run `npm run check:release`. It only reads public pages and configuration endpoints; it never spends a Qloo or model call. It is not a substitute for the manual end-to-end walkthrough from a signed-out browser.
