# CultureForge AI

An interactive prototype for turning a founder’s audience and business idea into cultural signals and concept directions. Mock mode works without Qloo access. When configured, the FastAPI backend can use the official Qloo Hackathon Kit CLI for live aggregate cultural signals.

## Stack

- React, TypeScript, Vite, Tailwind CSS
- FastAPI with Pydantic request/response contracts
- `CultureProvider` abstraction with `MockCultureProvider` and optional `QlooHarnessProvider`

The Qloo adapter uses the public `qloo exec find_tags` and `qloo exec recommend` workflows; it does not invent endpoints or query fields. The adapter makes at most two Qloo calls per uncached generation and caches results in memory for 24 hours. Mock concepts are generated from a shared catalog for food and beverage, retail, hospitality, wellness, and entertainment. Explicit audience keywords select a family, creative, mindful, value, professional, discovery, or general mock lens. That lens changes concept names, offerings, delivery choices, cultural hypotheses, and experience blueprints. Unmatched audiences use the supplied brief without inferred preferences. Location, objectives, and budget inform the pilot notes and illustrative pilot cost bands. Qloo signals, when live, are shown separately from these mock concepts. Scenario comparisons remain illustrative.

Keep credentials in the backend environment or Qloo CLI's private configuration. Never put a Qloo key in Vite client variables, source control, or command arguments.

## Run locally

Requires Node.js 18+ and Python 3.10+.

```bash
npm install
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start the API in one terminal:

```bash
uvicorn backend.main:app --reload --port 8000
```

Start the frontend in a second terminal:

```bash
npm run dev
```

Open the local Vite URL printed by the dev server. Vite proxies `/api` to FastAPI. If the API is unavailable, the frontend uses labeled sample data.

## Entry points

| Route | What it is |
|---|---|
| `/` | **The front page** — the marketing landing page with the full-screen background video (`index.html`, `main.js`, `styles.css`, `assets/`, `fonts/`). Static, no API calls. Its "Open studio" button loads the concept studio in place. |
| `/studio/` | The React concept studio — agent workspace, concept studio, scenario lab. Also reachable directly. |

The studio is a Vite entry point (`studio/index.html` → `/src/main.tsx`), so `npm run build` emits both `dist/index.html` and `dist/studio/index.html`. The front page reaches the studio in two ways: the "Open studio" button loads `/src/main.tsx` in place, and the studio's "Landing" button hands control back to the front page. The studio also carries a "Front page" link in its topbar for when it is opened directly.

`index.html` at the repository root must stay the front page. Vite builds from it, so replacing it with another page silently drops the marketing site from both `npm run dev` and `npm run build`.

## Optional live Qloo signals

Install the official harness (Node.js 22.19+ and `@qloo/qloo-harness` 0.1.26+), then configure its private credential store:

```bash
npm install --global @qloo/qloo-harness
qloo setup --qloo
qloo --version
```

### Hackathon keys need the hackathon base URL

A hackathon API key works **only** against `https://hackathon.api.qloo.com`. The same key returns `401` against `api.qloo.com` or `staging.api.qloo.com`. This is the most common cause of 401s, so set it explicitly:

```bash
qloo config set base-url https://hackathon.api.qloo.com
qloo config set api-key YOUR_QLOO_API_KEY
```

`qloo config set base-url` also marks the endpoint as trusted, which the CLI requires before it will send credentials to a non-production host. Both settings live in `~/.qloo/config` (mode 0600). Check the result with `qloo doctor --network`.

### Check your setup without spending quota

```bash
python3 scripts/check_api.py            # read-only: credentials, base URL, quota headroom
python3 scripts/check_api.py --live     # opt in to a single test request
```

### Quota guard

Hackathon keys carry rate and monthly limits that Qloo does not publish. Two guards keep this project from exhausting them:

- **Request timeout.** The stock `qloo exec` client caps each HTTP attempt at 20s, but `/v2/insights` needs roughly 25s against the hackathon environment. Every live request would time out, retry three times, and burn three calls for no result. `scripts/qloo_exec.mjs` reuses the harness's own client with an explicit timeout (`QLOO_REQUEST_TIMEOUT_MS`, default 60000) and no blind retries. It is a drop-in replacement for the `qloo` binary and the backend prefers it automatically.
- **Call budget.** `QLOO_MAX_CALLS_PER_HOUR` (default 20) and `QLOO_MAX_CALLS_PER_DAY` (default 100) bound how many Qloo workflows the backend may issue. The budget is checked *before* each request, so an exhausted budget pauses live signals instead of spending the quota. Usage is tracked in `~/.cache/cultureforge/qloo_calls.json`.

### Running with live data

```bash
CULTUREFORGE_PROVIDER=qloo uvicorn backend.main:app --reload --port 8000
```

The harness can also read `QLOO_API_KEY` from the backend process environment. Do not expose this variable through `VITE_*` variables. With no key and the default `auto` provider mode, the backend uses mock data. If a configured Qloo request fails, the API returns an error; it does not silently relabel the response as live or substitute mock data.

Responses are cached in memory for 24 hours per business type, audience, and location, so repeated requests for the same project do not re-spend quota. Qloo's API terms limit how long returned data may be retained — the in-memory cache is deliberately not written to disk.

## Prototype journey

1. Overview landing page → **Start creating**.
2. Enter business type, audience, location, budget, and objectives.
3. Review the agent progress sequence.
4. Select among three concept proposals and inspect fit scores and supporting sample signals.
5. Compare scenarios by changing the target audience and applying the draft.

Mock-mode signals and all concept-fit scores, narratives, and scenario deltas are illustrative demo content, not validated business advice. In live mode, only the separate cultural signal list comes from Qloo. Qloo outputs describe aggregate affinities, not individual preferences or guaranteed behavior. See the [Qloo Hackathon Kit](https://github.com/qloo/qloo-hackathon-kit) API access and safe-use guidance before using live data.

## Studio interface

The interface includes persistent dark and light themes, a guided demo, a saved-concept collection (stored locally in the browser), concept blueprint dialogs, a concept comparison matrix, evidence tabs, and a Markdown brief export. The scenario lab includes audience presets and adjustable preference sliders; its scores are an explicitly illustrative model. Theme and saved concepts persist across reloads, while exploration data stays in memory for the prototype.

The landing page provides separate Product, Case Studies, and Contact views. Its background video is bundled locally at `assets/cultureforge-background.mp4` so playback does not depend on the original remote URL.

### Background video and Safari

The background video uses the attributes Safari requires for inline autoplay — `autoplay muted loop playsinline` — plus `preload="auto"` and a `poster`. Two details matter:

- **The MP4 is faststart.** Its `moov` index sits in the first 40 KB rather than at the end of the 13.8 MB file. Without that, a browser that does not do a tail-range lookup has to download the entire file before it can play anything. The file is remuxed by `python3 scripts/fix_mp4_faststart.py assets/cultureforge-background.mp4`, which moves `moov` ahead of `mdat` and rewrites the `stco` chunk offsets to match. It is a container-only operation, so there is no re-encoding and no quality loss.
- **Autoplay can still be refused.** Safari applies its own autoplay policy, and a visitor who has blocked autoplay for the site will not get motion. `initBackgroundVideo()` in `main.js` therefore retries playback on the first pointer, touch, key, or scroll event.
- **The page never shows a white panel.** Safari paints a video's own surface white until a frame is decoded, and it draws the native play/pause bar over a paused video. The poster is therefore painted on the `.bg` container as a CSS background, and the `<video>` element stays at `opacity: 0` until it fires `playing` and gets the `is-playing` class. A blocked or paused video is invisible, so there is nothing to flash white and no control bar to show. The video is decorative, so it is paused entirely for visitors who prefer reduced motion.

## Verifying the backend and frontend agree

`npm run test:contracts` pins the `GenerateResponse` contract from `src/contracts.ts` and checks both producers against it:

```
$ npm run test:contracts
[ok]   GET /api/health -> live
[ok]   GET /health alias -> 200
[ok]   POST /api/projects/generate -> live, 3 concepts, 5 signals
[ok]   frontend mockGenerate -> mock, 3 concepts
[ok]   422 detail is readable -> "businessType: Input should be 'Food & beverage', ..."
All contract checks passed.
```

It fails if the backend renames, drops, or retypes a field the UI renders, if the mock fallback drifts from the same contract, or if an error stops returning a readable `detail` string. It needs the backend on port 8000 and the dev server on port 5173; `BASE_URL` and `DEV_URL` override them.

## API

The FastAPI backend exposes two endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | `{"status":"ok","dataMode":"live"\|"mock"}` — which provider is active. |
| `POST /api/projects/generate` | Takes a `ProjectRequest`, returns a `GenerateResponse`. |

`GET /health` is an alias of `/api/health` for tooling that probes the conventional path.

Validation failures return `422` with a readable `detail` string rather than FastAPI's default list of objects, and a Qloo failure returns `502` with a message the UI can show directly. In development Vite proxies `/api` to port 8000; a static build of `dist/` needs the same proxying, or the browser will need the origin allowed by the backend's CORS configuration.


## Knowledge graph and Obsidian vault

This repo ships a **graphify** knowledge graph over the code at `graphify-out/graph.json` and an **Obsidian vault** of per-node notes at `CultureForge AI/`. Both are scoped retrieval surfaces for AI coding assistants — a graph query returns a small subgraph, and a vault note returns one node's frontmatter (`source_file`, `location`, `community`) plus its connections.

`graph.json` is committed, so a fresh clone has a working graph with no build step. The vault's generated notes are not committed; regenerate them with:

```bash
uv tool install graphifyy --with mcp
graphify update .                                    # re-extract code (AST only, no API cost)
graphify export obsidian --dir "CultureForge AI"      # refresh the vault
```

The Obsidian vault is an **export** of the graph, not an input to it. `.graphifyignore` excludes it from the scan — do not remove that exclusion, or the graph will ingest its own output and inflate every query.

### OpenCode

`opencode.json` registers the `cultureforge-graph` MCP server, exposing `query_graph`, `get_node`, `get_neighbors`, `get_community`, `shortest_path`, `god_nodes`, and `graph_stats`. It starts through `scripts/graphify_mcp.sh`, which resolves the graphify interpreter for the current machine instead of hardcoding a path.

### Retrieval helpers

```bash
python3 scripts/vault_query.py "QlooHarnessProvider" --code   # one node + its source excerpt
python3 scripts/vault_query.py --search "cultural signal"      # search note contents
python3 scripts/vault_query.py --source "backend/providers.py" # notes from one source file
python3 scripts/vault_query.py --list --community "Backend Provider Models"
python3 scripts/vault_query.py --stats
```

`AGENTS.md` documents the full retrieval ladder and the delegation protocol.

## Check mock generation

Run `npm run test:mock` after installing frontend dependencies and the Python requirements. It checks 120 backend/frontend parity cases across five business types, eight audience briefs, and three budget bands, along with category-specific concepts, mock provenance, and pilot-budget limits. Both runtimes use `shared/mockCatalog.json`; the backend generator is in `backend/mock_generator.py` and the offline generator is in `src/mockData.ts`.

Typography now uses 14–16px body and control text with larger card headings. Longer concept descriptions flow naturally, medium-width cards use a wider image/text layout, and mobile scenarios stack audience summaries vertically.
