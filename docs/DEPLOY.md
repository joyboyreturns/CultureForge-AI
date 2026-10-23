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

## 2. Run it on your own Ubuntu server

The live demo runs from a server you control. You need: Ubuntu 22.04 or
24.04 (x86_64 or arm64), a way for the public to reach it over HTTPS, and a
machine that stays on until judging ends (5 November under the rules checked on 22 October, per
[SUBMISSION.md](SUBMISSION.md); recheck it).

**1. Install Docker with the Compose plugin.** On 24.04:

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"     # log out and back in once
```

On other releases follow [Docker's Ubuntu instructions](https://docs.docker.com/engine/install/ubuntu/).

**2. Get the code and set the secrets.**

```bash
git clone https://github.com/joyboyreturns/CultureForge-AI.git && cd CultureForge-AI
cp .env.example .env && chmod 600 .env
nano .env     # QLOO_API_KEY, RUN_PROFILE=judging, CULTUREFORGE_KEY_SALT=<long random>,
              # and AI_GATEWAY_ENABLED / AI_GATEWAY_API_KEY / AI_GATEWAY_MODEL if you use the model
```

Generate a salt with `openssl rand -hex 32`. `.env` stays on the server; it is
never committed or baked into the image.

**3. Start it.**

```bash
docker compose up -d --build
docker compose logs -f cultureforge         # Ctrl-C to leave
curl -s localhost:8000/health
```

The container restarts after a reboot (`restart: unless-stopped`, and Docker
is enabled at boot). The port is bound to `127.0.0.1`, so nothing is public yet.

**4. Put HTTPS in front of it.** The simplest route is Caddy, which gets and
renews a certificate by itself. You need a domain whose A record points at
the server's public IP, and ports 80 and 443 reachable from the internet:

```bash
sudo apt install -y caddy
printf 'demo.example.com {\n    reverse_proxy 127.0.0.1:8000\n}\n' | sudo tee /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Replace `demo.example.com`. Research runs and cold lookups can take over a
minute, so if you use nginx instead, set `proxy_read_timeout 180s;`. Caddy's
default has no such limit.

**4b. Alternative: a named Cloudflare Tunnel (no open ports).** You need a domain on Cloudflare. A *named*
tunnel has a stable address; the temporary `trycloudflare.com` ones change and cannot be submitted.

```bash
# install cloudflared from Cloudflare's apt repository (see developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
cloudflared tunnel login                              # opens a browser once, picks your domain
cloudflared tunnel create cultureforge
cloudflared tunnel route dns cultureforge demo.example.com
sudo mkdir -p /etc/cloudflared && sudo tee /etc/cloudflared/config.yml >/dev/null <<'YML'
tunnel: cultureforge
credentials-file: /root/.cloudflared/<TUNNEL-ID>.json
ingress:
  - hostname: demo.example.com
    service: http://127.0.0.1:8000
  - service: http_status:404
YML
sudo cloudflared service install && sudo systemctl enable --now cloudflared
```

Things that matter for judging:

- **Keep `docker-compose.yml` bound to `127.0.0.1`** (the default). The tunnel is then the only way in.
- **Visitors are told apart automatically.** The tunnel connects from this machine, so the app reads
  `CF-Connecting-IP`; the per-visitor allowance and each visitor's private saved explorations depend on it.
  Operator routes (`/api/workspaces`, keys) stay closed to anything that arrives through the tunnel; they
  answer only on the machine itself, or with `CULTUREFORGE_OPERATOR_TOKEN`.
- **Cloudflare cuts a request after 100 seconds (error 524).** The studio's long work is a polled research run,
  so each request is short; only a direct call to a slow cold route could hit it.
- **Do not put Cloudflare Access, "Under Attack" mode or Bot Fight Mode in front of the demo hostname.** A
  challenge page blocks judges and any automated check of your URL.
- The landing background is drawn in code (no video file), so there is no large media to serve through Cloudflare.
- Check from a phone on mobile data, then run `python3 scripts/smoke_test.py https://demo.example.com`.

**5. Firewall.** Keep port 8000 private:

```bash
sudo ufw allow OpenSSH && sudo ufw allow 80,443/tcp && sudo ufw enable
```

**6. Keep it reachable and awake.**

```bash
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
```

- A home or office connection often has a changing IP, or sits behind
  carrier-grade NAT, so ports 80/443 cannot be forwarded. In that case use a
  tunnel with a stable name (for example a *named* Cloudflare Tunnel) instead
  of Caddy. Temporary tunnel URLs change, so they are not suitable for a link
  you submit.
- Check from a phone on mobile data, not from the same network.
- Power cuts and router restarts take the demo down. After one, confirm
  `docker compose ps` and run the smoke test.

**7. Smoke-test.** The held evidence travels with the code: `shared/demoPack.json`
holds every Qloo answer, agent report, model naming and analysis the
development machine held, under their original acquisition times, and the
server loads it into `/data` at start-up as pinned entries. So every prepared
brief, and every brief researched on the development machine, opens on the
server from held evidence, with no Qloo or model request. Check it costs
nothing (read-only):

```bash
python3 scripts/smoke_test.py https://demo.example.com
python3 scripts/prewarm.py --base-url https://demo.example.com          # lists held and cold briefs, spends nothing
```

To ship more held evidence later, research the briefs on the development
machine, then `python3 scripts/export_evidence_store.py`, commit
`shared/demoPack.json`, push, and on the server `git pull && docker compose up -d --build`.
A brief the pack does not hold can still be prewarmed on the server with
`python3 scripts/prewarm.py --live --base-url https://demo.example.com` (spends quota, once per brief).

Then record the URL in [`submission.json`](../submission.json).

**Update, back up, roll back:**

```bash
git pull && docker compose up -d --build                        # update
VOL=$(docker volume ls -q | grep cultureforge-data)             # the project's data volume
docker run --rm -v "$VOL":/data -v "$PWD":/backup busybox \
  tar czf /backup/data.tgz /data                                # back up held evidence and ledgers
git checkout <previous-commit> && docker compose up -d --build  # roll back
```

To change a setting, edit `.env` and run
`docker compose up -d --force-recreate`.

## 3. Alternative: deploy on Render (blueprint included)

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
| `RUN_PROFILE` | `judging` in `render.yaml` and `docker-compose.yml`: the demo runs with every call-count budget off. Set `dev` in `.env` while testing, to keep the caps; running the backend directly (`uvicorn`) also defaults to `dev` ([JUDGING_DAY.md](JUDGING_DAY.md)) |
| `QLOO_LIVE_ENABLED` | `true`; `false` serves held evidence only |
| `QLOO_MAX_CALLS_PER_HOUR` / `_PER_DAY` | 20 / 100 (dev profile only) |
| `AI_GATEWAY_ENABLED` | `false`, or `true` to turn on naming, the agent loop and *Ask the evidence* |
| `AI_GATEWAY_API_KEY`, `AI_GATEWAY_MODEL` | Vercel AI Gateway key (secret) and model id, if enabled |
| `CULTUREFORGE_ALLOWED_ORIGINS` | Empty for same-origin; otherwise the exact studio origins, comma-separated |
| `CULTUREFORGE_KEY_SALT` | A long random string (the Render blueprint generates one). It salts the hashes of issued workspace API keys; the built-in default is for development only |
| `CULTUREFORGE_OPERATOR_TOKEN` | Unset unless operator administration is deliberately enabled |
| `CULTUREFORGE_MAX_COLD_RUNS` / `_COLD_RUNS_PER_CLIENT_HOUR` | 3 / 8. Fair use in every profile: how many new ideas are researched at once, and how many one visitor may start an hour. Held evidence is never limited. A refusal is HTTP 429 with `Retry-After`, says when to come back and that prepared examples still open instantly |
| `CULTUREFORGE_AGENT_SLOTS` / `_AGENT_QUEUE_SECONDS` | 2 / 45. Agent loops that may run at once (about ten model requests each, against a route that allows five a minute). A loop that finds no slot in time is skipped and says so; it is not held, so a later open runs it |
| `CULTUREFORGE_TRUST_PROXY` | Blank (automatic). The per-visitor allowance needs each visitor's address. Behind Caddy, a tunnel or Docker's bridge the connecting address is local, so the last `X-Forwarded-For` value is used; an internet peer is never believed. `true`/`false` force it |
| `PORT` | Set by most hosts; the container listens on it (default 8000) |

The Dockerfile installs `fonts-dejavu-core` for Latin text and
`fonts-droid-fallback` for CJK characters. The PDF selects a Latin-capable
primary font before registering a CJK fallback; a CJK-only font otherwise
renders English blank. English and Japanese were visually verified together
in the actual Linux container (outside Docker, set `CULTUREFORGE_PDF_FONT`).

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

Not yet verified end to end. The Dockerfile, `docker-compose.yml`, the
Ubuntu steps and `render.yaml` were written and reviewed, but no image was
built and no Ubuntu machine was used, because the development machine had no
Docker daemon. The smoke test was run against a local server. Build the image
and run the Ubuntu steps once before the demo, and fix this page if a step
differs on your machine.
