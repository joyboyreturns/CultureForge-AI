# CultureForge AI

**Concept directions that have to survive their Qloo evidence.** CultureForge
is for location and concept strategists at hospitality and retail groups and
brand agencies. They need to argue which concept fits which neighbourhood,
and defend it. From a brief (business category, specific idea, audience, location),
CultureForge retrieves the audience's Qloo tags, local places and what the
same audience gravitates to beyond places. It composes directions in which
every decision cites its evidence, and then lets the evidence push back: a
bounded agent runs further Qloo workflows, a written policy can return
*contested*, model claims without a Qloo citation are rejected, and
follow-up questions are answered from the evidence or refused. Every number
shown is one Qloo returned. Nothing claims demand, rent, footfall or
willingness to pay.

**A prototype.** Where Qloo doesn't have enough data for an idea in a place, CultureForge says so plainly instead of inventing an answer.

**Try it in the first minute:** choose from **14 trial briefs** or enter your own
idea. The first evidence-backed answer opens automatically as soon as it is
available. A floating card follows the continuing research; when it finishes,
the preview updates to the full report with a completion message.
London's fresh vegan-restaurant test produced its initial answer in about
**11 seconds**. This is a measured example, not a latency guarantee; the full
analysis continues in the background. See the [verification record](docs/JUDGE_SCENARIOS.md).

![The landing page: put the idea on trial](docs/screenshots/landing.jpg)

## What it does, at a glance

| | |
| --- | --- |
| **One look, front page to studio** | The studio shares the landing page's dusk: the same scene drawn in code behind every screen, the pixel display face for headlines, white pills for the next step and dark glass for everything else. A light theme is one tap away. |
| **Executive decision brief** | The studio opens on the answer: the lead direction, its verdict, the top cultural anchors with `[evidence id]` chips, who it is for, and the lead place Qloo returned. There is deliberately **no 0-100 fit score**: Qloo returns none, so the brief shows citation coverage and the evidence test instead. |
| **Seven sections, not one long scroll** | The concept studio is split into *Executive brief, Evidence trace, Places & signals, Directions, Evidence test, Decision* and *Cultural roots*. Each is reachable from the sidebar (nested under Concept studio, with live counts) or from a sticky section bar, and ends with *Previous / Next*. |
| **Evidence that can say no** | Directions are tested against the places Qloo returned. A direction can come out *supported*, *unproven* or *contested*, and the order can change. |
| **Refresh-proof** | A reload reopens the exploration you last had open, from this browser's copy of it. |
| **Take evidence away** | Remove each returned venue in turn and see which one is carrying the answer. It runs on held evidence, with no Qloo or model call. |
| **First evidence, automatically** | The initial answer opens as soon as real evidence supports a preview, clearly labelled as research in progress. No extra click to reveal it. |
| **Visible background research** | A floating card shows the latest real step. The preview updates automatically to the full report on completion. If you have switched to another exploration, the card offers the completed report without taking you away. |
| **14 trial ideas to explore** | A scrollable, category-filtered gallery spans food, wellness, entertainment, retail and hospitality, including Berlin, Vienna and a Mexico City café-bookshop. Held evidence retains its original provenance. |
| **City-specific place retrieval** | Fresh place searches constrain the returned places to the requested city. Shared retrieval covers primary ideas, hybrid components, agent recommendations and replacement searches. |
| **Always a way out** | Back, Switch idea and Try another example in the Concept studio and Scenario lab. |
| **A tour that keeps up** | The guided tour moves to the right screen and the right section for each step, and highlights the target. |

## See it in 60 seconds

1. Press **Try the demo** and choose one of the **14 trial ideas**, or enter a fresh brief. The gallery has category filters and notes explaining the scope of each example. A brief marked **Evidence held** reuses real Qloo evidence without a new Qloo request.
2. Read the **initial answer** when it opens automatically. Open a source in **Evidence trace** to inspect the actual request and response excerpt. A floating card shows the research continuing in the background.
3. Try the **Evidence test** or remove a cited venue to see whether the direction survives. Verdicts can be supported, contested or unproven; missing evidence stays explicit.
4. When research completes, the initial view updates to the **full evidence and report**, with a completion message. If you switch ideas, the completed report remains available from the floating card. Use **Watch it live** to return to the detailed research trace.

The first-minute experience is about seeing and testing evidence immediately;
it does not promise that every fresh report finishes within a minute. Missing
coverage, invalid inputs and upstream failures have stated recovery paths.

### The studio

Every screenshot below is from a real run on the `judging` profile against the live Qloo API, with the
optional model on: a wellness studio for *mindful professionals who want a slow afternoon* in London.

![The studio overview, in the landing page's dusk](docs/screenshots/studio-overview.jpg)

*The overview. The same dusk scene as the front page sits behind the studio, painted once as a still frame.*

![The agent workspace during a live run](docs/screenshots/agent-workspace.jpg)

*The agent workspace during a live run. Evidence appears as it arrives, the clock says what to expect, and when Qloo's first answer supports no direction yet the screen says so instead of guessing.*

![Executive decision brief with the seven sections in the sidebar](docs/screenshots/executive-brief.jpg)

*The concept studio opens on the answer. The seven sections sit under Concept studio in the sidebar and in the section bar above the brief. Here the live evidence test has already contested the first anchor.*

![Evidence trace: what the answer is built on](docs/screenshots/evidence-trace.jpg)

*Evidence trace. Qloo returned the sources; CultureForge proposed the decisions; the lines show attached citations, not proof.*

![Places and signals: how the idea was read, and what Qloo returned](docs/screenshots/places-signals.jpg)

*Places & signals. How the idea was read, every returned result sorted by relevance, and the real Qloo photographs and measurements.*

![Directions: each proposal with its photograph and citations](docs/screenshots/directions.jpg)

*Directions. A lone direction takes the full width: the Qloo photograph of its anchor beside the words, the tagline and the evidence it cites.*

![The evidence test: contested on one anchor, supported on another](docs/screenshots/evidence-test.jpg)

*The evidence test can disagree with the composer. Held to Third Space City the direction is contested; held to Biome by Corinthia London it is supported. The screen names the alternative anchor, the original reference, and that the concept was not rebuilt.*

![Decision: the research agent's steps](docs/screenshots/decision.jpg)

*Decision. What the bounded research agent asked Qloo, step by step, including the steps it was refused. Every step is held, so a replay costs nothing.*

![The model's analysis, citing evidence ids](docs/screenshots/analysis.jpg)

*The optional model analysis. Its claims cite only evidence on screen; the verdict label and the citation coverage are computed by the application, not the model.*

![The cultural opportunity map in London](docs/screenshots/map.jpg)

*Cultural roots, with the interest map: a real street map with named pins and a venue list that says why each unplotted place is not drawn. Pins are address matches, never surveyed points.*

![Investigating one direction](docs/screenshots/investigate.jpg)

*Investigate opens the questions a direction has not answered, each one a named Qloo workflow: here, where interest in the anchor concentrates.*

![Which place is carrying this answer?](docs/screenshots/dependence-test.jpg)

*The dependence test removes each returned venue once and reports whether the answer, or only its sources, changed. No Qloo or model call.*

![Scenario lab: same vision, a different audience](docs/screenshots/scenario-lab.jpg)

*Scenario lab. Qloo's own comparison of two audiences, including when they overlap so much that it cannot show a difference.*

![Guided tour highlighting the evidence test](docs/screenshots/guided-tour.jpg)

*The guided tour follows the reader to each step, opens the section it needs and highlights what it describes.*

![The light theme](docs/screenshots/light-mode.jpg)

*The light theme keeps the dusk masthead and the same section navigation.*

<p>
  <img src="docs/screenshots/mobile.jpg" alt="The concept studio on a phone" width="260"/>
  <img src="docs/screenshots/mobile-menu.jpg" alt="The sections in the phone menu" width="260"/>
</p>

*It works on a phone: the section bar scrolls to the open section, and the menu lists every section.*

The studio assesses reference relevance, resolves explicit business categories, and exposes an initial answer before optional model work. See the [verified implementation review](docs/IMPLEMENTATION_REVIEW.md) and [demo journey](docs/DEMO.md).

## How a brief becomes a verdict

```mermaid
flowchart TB
  A([Brief: category, idea, audience, place]) --> R[Read the idea into typed components<br/>hybrids, specialisations, disclosed simplifications]
  R --> T[find_tags: resolve audience and category<br/>tags come only from returned envelopes]
  T --> H{Evidence held?}
  H -- yes --> K[Serve from the evidence store<br/>zero upstream requests]
  H -- no --> Q[Qloo workflows<br/>recommend, where_popular, entity_tags ...]
  Q --> K
  K --> C[Rule composer: directions,<br/>every decision cites its evidence]
  C --> I[Initial answer on screen]
  I --> G[Bounded agent: up to 8 plan-act-observe steps]
  G --> V[Citation validator:<br/>claims need an observed ID or tag URN]
  C --> X[Evidence test<br/>supported, contested or unproven]
  X --> O[Studio, PDF, share link]
  V --> O
```

### What the reader sees while it runs

```mermaid
sequenceDiagram
  participant J as Judge
  participant UI as Studio
  participant API as Backend run
  J->>UI: Start an exploration or open a demo
  UI->>API: Start research run
  loop every ~1 s
    UI->>API: Fetch run state and real steps
    API-->>UI: steps, timings, partial answer
  end
  UI-->>J: Automatically open first evidence / initial answer
  Note over UI,API: Research continues; a floating card shows real progress.
  API-->>UI: Complete with full report
  alt Judge is still reading this preview
    UI-->>J: Update to full report and show completion message
  else Judge has moved to another idea or screen
    UI-->>J: Your exploration is ready - Open the results
  end
```

### How the test can say no

```mermaid
flowchart LR
  D[Direction + anchor place] --> P1[rank: anchor vs places returned for the profile]
  D --> P2[compare_audiences: anchor tags vs every other place]
  P1 & P2 --> POL{Policy<br/>anchor-fit-5}
  POL -- both pass --> S[supported]
  POL -- one check missing --> U[unproven]
  POL -- a check fails --> N[contested]
  N --> RE[Re-anchor to another place and re-test]
  S --> RE
```

## Architecture

```mermaid
flowchart LR
  B[Brief or prepared example] --> S{Evidence store}
  S -- held --> C
  S -- miss --> Q[Qloo harness<br/>9 workflows] --> S
  C[Deterministic composer<br/>cited decisions] --> AG[Agent loop<br/>≤8 allowlisted steps]
  AG --> V[Citation validator]
  C --> T[Evidence test<br/>anchor-fit-5]
  C --> CH[Ask the evidence] --> V
  T & V & C --> OUT[Studio · PDF · share link]
  P[RUN_PROFILE · ledger · kill switch] -.-> Q
```

More in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## How Qloo is used

All nine workflows of the official Hackathon Kit harness, each with its own
request builder, cached, and shown in a provenance drawer with allowlisted
query keys.

| Workflow | Used for | Returns | Carried forward |
| --- | --- | --- | --- |
| `find_tags` | Resolve the audience | Up to 3 tags | Tag URNs (`urn:tag:…`) become the audience seeds; a separate exact category tag filters explicit business ideas |
| `recommend` (place) | Local evidence | Up to 10 places with affinity, popularity, rating, price, description, image | Entity IDs; each direction's anchor and citations |
| `recommend` (artist, movie, brand) | The audience bridge: same tags, no location | Up to 5 per domain | Entity IDs, shown as audience-level cross-references |
| `rank` | The evidence test | The places ranked for a demographic profile | Rank position of each anchor |
| `compare_audiences` | The evidence test | Tags for the anchor against every other place | Qualifying cultural tag URNs |
| `where_popular` | Interest map, investigation | Lat/lon interest cells | Drawn as cells, never as venue pins |
| `entity_tags`, `describe`, `audience_demographics`, `trends` | Investigation, agent loop, chat | Tags, metadata, demographic index, time series | IDs added to what the agent may cite |

## How the LLM is used, and validated

The model layer is optional and uses **Vercel AI Gateway only**
(`backend/llm.py`, `backend/reasoning.py`). The studio names the model that
answered.

- **Naming.** It may rename and retag directions. Claims, evidence and
  verdicts stay with the rules, and unsupported numbers are rejected.
- **Agent loop** (`backend/agent.py`). Up to 8 plan-act-observe steps. The
  model picks the next tool from an allowlist, naming only entity IDs and tag
  URNs already observed; the server builds and caches every Qloo request.
  Its analysis is a list of claims, and a claim survives only if every
  citation was observed in this run's envelopes and it states no number of
  its own.
- **Ask the evidence** (`backend/chat.py`). The same allowlist and
  validator, plus at most 3 justified Qloo calls. A question the evidence
  cannot answer gets a refusal.
- **Fallback.** No model, malformed output or no valid claim: the rule
  composer's answer stands, and the trace says so.

## Quick start

**Hosted demo:** not deployed yet. [docs/DEPLOY.md](docs/DEPLOY.md) has the
steps; the URL goes here and in `submission.json`.

**Local** (Node 22.19+, Python 3.10+, a Qloo hackathon key):

```bash
npm ci
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
npm install --global @qloo/qloo-harness@0.1.26
cp .env.example .env            # set QLOO_API_KEY; model settings are optional
uvicorn backend.main:app --port 8000
```

```bash
npm run dev                     # then open the printed URL at /studio/
```

Or as the deployed container: `docker compose up --build`, then open
`http://localhost:8000/studio/`. Pick a prepared brief; one marked **Evidence
held** costs no Qloo request. The held evidence ships with the code in
`shared/demoPack.json` (prepared Qloo evidence, held evidence tests and available
agent reports, plus briefs researched while building this). A fresh server
can replay the prepared evidence without new Qloo requests. Optional model
analysis can continue in the background when its result is not already held.
`python3 scripts/export_evidence_store.py` adds whatever your own store holds;
`python3 scripts/prewarm.py` shows which briefs are held, and `--live` fetches the rest.

## Configuration

`RUN_PROFILE` is the one switch. **dev** enforces the call budgets below;
**judging** lifts every call-count budget and keeps the timeouts, the error
mapping, a cool-down after a Qloo 429, single-flight de-duplication and the
cache. `GET /api/health` reports the profile, each budget (or `unlimited`)
and the cache size. In dev, a budget can be lowered but not switched off: a
value below one becomes one, and the analysis allowance cannot exceed 10.
`backend/tests/test_config.py` fails if this table or `.env.example` drifts
from `backend/config.py`.

| Variable | dev | judging | Meaning | Read in |
| --- | --- | --- | --- | --- |
| `RUN_PROFILE` | dev | judging | Budget profile; unknown values fall back to dev | `config.py` |
| `QLOO_MAX_CALLS_PER_HOUR` | 20 | unlimited | Qloo workflows per hour | `config.py` |
| `QLOO_MAX_CALLS_PER_DAY` | 100 | unlimited | Qloo workflows per day | `config.py` |
| `LLM_MAX_CALLS_PER_HOUR` | 20 | unlimited | Model naming calls per hour | `config.py` |
| `LLM_MAX_CALLS_PER_DAY` | 50 | unlimited | Model naming calls per day | `config.py` |
| `AI_GATEWAY_ANALYSIS_DAILY_LIMIT` | 10 | unlimited | Agent, analysis and chat model calls per day | `config.py` |
| `RESEARCH_RUN_MAX_WORKFLOWS` | 8 | unlimited | Qloo workflows per research run (judging is bounded by the 420 s deadline) | `config.py` |
| `CULTUREFORGE_EVIDENCE_TTL_HOURS` | 24 | 720 | How long held evidence answers | `config.py` |
| `CULTUREFORGE_NEGATIVE_TTL_HOURS` | 6 | 6 | How long a verified "no places for this category here" answer is trusted (never longer than the evidence TTL) | `config.py` |
| `QLOO_LIVE_ENABLED` | true | true | `false` serves held evidence only | `config.py` |
| `QLOO_RATE_LIMIT_COOLDOWN_SECONDS` | 60 | 60 | Pause after two Qloo rate-limit answers in a row | `config.py` |
| `QLOO_MIN_CALL_INTERVAL_SECONDS` | 2 | 2 | Least time between live Qloo requests, server-wide (0 disables) | `config.py` |
| `CULTUREFORGE_BRIDGE_DOMAINS` | artist,movie,brand | same | Audience-bridge domains; `off` disables | `config.py` |
| `QLOO_API_KEY` | — | — | Hackathon key (secret, server only) | `providers.py`, `qloo_exec.mjs` |
| `QLOO_BASE_URL`, `QLOO_TRUSTED_BASE_URL` | hackathon host | same | Set by the Dockerfile; hackathon keys work only against `https://hackathon.api.qloo.com` | Dockerfile, `check_api.py` |
| `PORT` | 8000 | same | Port the container listens on | Dockerfile |
| `BASE_URL`, `DEV_URL` | local | — | Targets of the `verify_*` scripts | `scripts/verify_*.mjs` |
| `QLOO_REQUEST_TIMEOUT_MS` | 60000 | same | Per-request Qloo timeout | `scripts/qloo_exec.mjs` |
| `QLOO_MAX_ATTEMPTS` | 1 | same | HTTP attempts per request (no blind retries) | `scripts/qloo_exec.mjs` |
| `QLOO_CLI`, `QLOO_HARNESS_PATH` | — | — | Override the harness command or package path | `providers.py`, `qloo_exec.mjs` |
| `CULTUREFORGE_PROVIDER` | auto | auto | `auto`/`qloo` need a key; `mock` is the test fixture only | `providers.py` |
| `AI_GATEWAY_ENABLED` | false | false | Turns the model layer on | `llm.py` |
| `AI_GATEWAY_API_KEY`, `AI_GATEWAY_MODEL` | — | — | Vercel key (secret) and model id | `llm.py` |
| `AI_GATEWAY_DISPLAY_MODEL` | model id | same | Readable name shown for the model | `llm.py` |
| `LLM_TIMEOUT_SECONDS` | 30 | same | Naming request timeout | `llm.py` |
| `LLM_REQUESTS_PER_MINUTE` | 5 | 5 | Model requests that may start in a rolling minute (pacing, not a budget; 0 disables) | `modelpace.py` |
| `CULTUREFORGE_CACHE_DIR` | `~/.cache/cultureforge` | same | Evidence store and `budget.db` | `evidence_store.py`, `ledger.py` |
| `CULTUREFORGE_DB` | `~/.cache/cultureforge/platform.db` | same | Workspaces and saved explorations | `platform.py` |
| `CULTUREFORGE_STATIC_DIR` | unset | same | Serve the built UI (set in Docker) | `main.py` |
| `CULTUREFORGE_PDF_FONT` | auto-detected | same | A `.ttf` that covers non-Latin text, for the PDF (the Docker image installs one) | `report_pdf.py` |
| `CULTUREFORGE_ALLOWED_ORIGINS` | empty | same | Extra CORS origins if the UI is hosted elsewhere | `main.py` |
| `CULTUREFORGE_KEY_SALT` | dev default | set it | Salt for issued workspace keys | `platform.py` |
| `CULTUREFORGE_OPERATOR_TOKEN` | unset | unset | Opens operator routes away from localhost | `main.py` |
| `CULTUREFORGE_API_TARGET` | `http://127.0.0.1:8000` | — | Where the Vite dev server proxies `/api` | `vite.config.ts` |

## API

FastAPI documents every route at `/docs`. The main ones:

| Route | Purpose |
| --- | --- |
| `GET /api/health` | Readiness, profile, budgets, cache; no upstream call |
| `GET /api/examples` | Prepared briefs and whether each is held |
| `POST /api/research/runs` → `GET /api/research/runs/{id}` | The observable research run, with agent steps |
| `POST /api/projects/generate` | Answer a brief directly |
| `POST /api/projects/challenge` | The evidence test (anchor-fit-5), with an optional anchor and profile |
| `POST /api/chat` | Ask the evidence |
| `POST /api/report/pdf` | The PDF report |

The full table and the error envelope are in [docs/API.md](docs/API.md).

## Checks

```bash
npm run lint && npm run build
python -m pytest backend/tests -q        # none of these tests can reach Qloo or a model
npm run test:unit && npm run check:submission
python3 scripts/smoke_test.py <url>      # a running deployment, no quota spent
```

CI runs all of these except the smoke test, with coverage.

## Limits and non-claims

- The verdict is about **anchor fit within the retrieved sample**: at most
  ten places, ranked against one demographic profile that CultureForge
  proposes and the reader can change. Confidence is never higher than
  *moderate*.
- No demand, revenue, footfall, rent, competition or willingness to pay is
  measured or implied. No customer validation exists yet; the commercial
  case is a set of assumptions in [docs/BUSINESS.md](docs/BUSINESS.md).
- The model layer is optional; its validator checks citations and numbers,
  not the soundness of reasoning.
- The deployment is one process and one instance. The judging profile lifts
  local budgets, not Qloo's own quota, so prewarm first.
- The landing and studio backgrounds are drawn in code (`landing-scene.js`):
  no video, photograph or third-party media. The studio paints one still
  frame. It was checked in Chromium, not in Safari.

The full list is in [docs/LIMITATIONS.md](docs/LIMITATIONS.md). Also see
[EVIDENCE_POLICY](docs/EVIDENCE_POLICY.md), [DEPLOY](docs/DEPLOY.md),
[JUDGING_DAY](docs/JUDGING_DAY.md), [DEMO](docs/DEMO.md),
[SUBMISSION](docs/SUBMISSION.md), [CHANGELOG](CHANGELOG.md) and
[THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md). MIT licensed.

## Thank you

Thank you to **Qloo** for providing access to its API and for hosting this hackathon, and to everyone who made it possible. Thanks as well to the tools and services this project is built on: the Qloo harness, Vercel AI Gateway, FastAPI, React and Vite, MapLibre, and the open-source community behind them. Your support made CultureForge AI possible.

## Business direction

**Commercial direction:** a proposed $1,500 design partner pilot for one
hospitality strategy team, five scoped briefs and a 30-day review. Pricing
and customer value are unvalidated; commercial data terms are a prerequisite.
The landing page leads with **Why Qloo** and a demo. A quieter **For teams**
footer link offers the team-specific pilot discussion brief.
See the [business model](docs/BUSINESS.md), [investment pitch](docs/INVESTOR_BRIEF.md)
and [release audit](docs/RELEASE_AUDIT.md).

