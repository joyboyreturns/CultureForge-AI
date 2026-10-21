# CultureForge AI

An interactive prototype for turning a founder’s audience and business idea into cultural signals and concept directions. The studio answers with live Qloo evidence: the FastAPI backend drives the official Qloo Hackathon Kit CLI, and there is no mock data anywhere in the product.

## Stack

- React, TypeScript, Vite, Tailwind CSS
- FastAPI with Pydantic request/response contracts
- `CultureProvider` abstraction with `QlooHarnessProvider` (the product) and `MockCultureProvider` (the test fixture only)

The Qloo adapter uses the public `qloo exec find_tags` and `qloo exec recommend` workflows; it does not invent endpoints or query fields. The adapter makes at most two Qloo calls per uncached generation and caches results in memory for 24 hours. The studio has no mock path: if the backend cannot reach Qloo, it says so and the founder is told what to fix, rather than being shown a rule-based fiction that looks like data. The mock provider survives only as the offline fixture the test suite runs against (`CULTUREFORGE_PROVIDER=mock`), so the HTTP contract can be checked without spending quota.

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

Open the local Vite URL printed by the dev server. Vite proxies `/api` to FastAPI. If the API is unavailable, the studio says so and asks for a retry — it never falls back to sample data.

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
- **Call budget.** `QLOO_MAX_CALLS_PER_HOUR` (default 30) and `QLOO_MAX_CALLS_PER_DAY` (default 150) bound how many Qloo workflows the backend may issue. A brief costs two calls, so that is fifteen briefs an hour and seventy-five a day for everyone at once. The budget is checked *before* each request, so an exhausted budget pauses live signals instead of spending the quota. Usage is tracked in `~/.cache/cultureforge/qloo_calls.json`.

### Running with live data

```bash
CULTUREFORGE_PROVIDER=qloo uvicorn backend.main:app --reload --port 8000
```

The harness can also read `QLOO_API_KEY` from the backend process environment. Do not expose this variable through `VITE_*` variables. With no key, the default `auto` provider mode refuses to answer rather than substituting mock data: the request comes back as a 503 with the reason, and `GET /api/health` reports `providerReady: false` and says what is missing. If a configured Qloo request fails, the API returns an error; it does not silently relabel the response as live or substitute mock data.

Responses are cached in memory for 24 hours per business type, audience, and location, so repeated requests for the same project do not re-spend quota. The evidence store also writes the envelopes to disk under `~/.cache/cultureforge`, so a restart does not lose what the demo already paid for, and the studio holds the composed answer in the browser for 12 hours on top of that — a reload paints the same exploration instantly, labelled as held rather than fetched.

## Prototype journey

1. Overview landing page → **Start creating**.
2. Enter business type, audience, location, budget, and objectives.
3. **Confirm the audience seeds.** The brief is resolved into the Qloo cultural signals it actually maps to. Each one is shown with its tag URN and its popularity. Drop anything that is not really your audience.
4. **Watch the agent work.** The workspace polls a real run and shows the steps the agent made, with the durations and correlation IDs the Qloo harness reported. If Qloo cannot resolve something, the agent asks rather than guesses.
5. **Read the three directions.** Each cites the venues it was built from.
6. **Inspect the evidence.** Click any venue to see the exact call that produced it, the request that was sent, and what came back.
7. **Test the answer.** Remove a venue and recompose, with no new call, to see how many directions actually depended on it.
8. **Change the lens.** Compare the two audiences with Qloo's own A/B, or rank the returned places against a demographic to pick the anchor.
9. **Investigate a direction.** Open the questions that direction has not answered — where does it concentrate, do the venues share a cultural signature, who is indexed against it — and see the tools the agent used, what it found, and what it could not establish.

Concept narratives, pilot-budget bands and implementation notes are CultureForge's reading of Qloo evidence, not validated business advice. Qloo outputs describe aggregate affinities, not individual preferences or guaranteed behavior. See the [Qloo Hackathon Kit](https://github.com/qloo/qloo-hackathon-kit) API access and safe-use guidance before using live data.

## Studio interface

The interface includes persistent dark and light themes, a live example brief, a saved-concept collection (stored locally in the browser), concept blueprint dialogs, a concept comparison matrix, evidence tabs, and a Markdown brief export. The scenario lab holds no local score model: it asks Qloo to research the new audience and to run its own A/B between the two groups of venues, and the chart that used to shift fit scores locally is gone because it was not a measurement. Theme and saved concepts persist across reloads, as does the last real answer, which the browser holds for twelve hours.

The studio's own decision loop is **Investigate**: pick a direction, open the
questions it has not answered, and let the agent answer them with named Qloo
workflows. It is reachable from every concept card and from the results
header.

The concept studio has six tabs, and the last four are the ones a judge should be pointed at:

| Tab | What it shows |
|---|---|
| Cultural signals | The aggregate Qloo signals behind the brief. |
| Constellation | The evidence-to-idea graph: seeds at the centre, the places Qloo returned around them, the business decisions on the outside. Solid lines are relationships Qloo returned; dashed lines are CultureForge's reading of them. A popularity heat overlay draws each node's size from Qloo's own popularity metric. |
| Cultural heat | Qloo's popularity for everything retrieved, as a heat grid. It measures how widely a place or a signal is known, not how well it fits the brief, and the labels say so. |
| Anchor tournament | Qloo's `rank` workflow comparing the returned places against a demographic near the brief's location. The converted age and gender signal is shown, taken from the request Qloo actually sent. |
| Blueprint | The experience the concept implies. |
| Evidence & source | What is behind the idea, and what is not. |

### The evidence surfaces

- **Provenance inspector.** Any piece of evidence opens a panel showing the workflow that produced it, the allowlisted request that was sent, the duration, the correlation ID, and an excerpt of what came back. The request is filtered through a fixed allowlist of query keys, so a new field cannot quietly start being exposed.
- **The evidence test.** Removing a venue and recomposing costs no upstream call, because the envelopes are already held. It is the strongest claim the app makes, so it is a button rather than a claim: if a direction survives without a venue, that direction was not really resting on it.
- **A/B with Qloo.** The scenario lab asks Qloo to compare the two audiences' venues directly, and shows the cultural tags the two groups share, the comparison score, and how many entities in each side carry each tag.
- **Sharing.** A share link reopens exactly the exploration, from a stored snapshot, rather than re-running the research.

The landing page provides separate Product, Case Studies, and Contact views. Its background video is bundled locally at `assets/cultureforge-background.mp4` so playback does not depend on the original remote URL.

### The editorial layer

`src/wildroot.css` is imported last, so it wins over `styles.css` and `readability.css`. It moves the studio out of the dashboard register and into an editorial, seed-packet one:

- **Deep colour blocks.** The results masthead is a beet block with cream type and a sun-coloured accent; the scenario card is the same block on the other side of the page. Type is set oversized and uppercase, with the serif italic kept for the one phrase that should not shout.
- **Stickers, not panels.** Cards have square corners, a hard offset shadow, and a slight rotation, so a row of three directions reads as printed cards laid on a table rather than as a grid of widgets.
- **Banded labels.** Monospace labels sit on solid colour bands — the direction number, the evidence badge, the cultural themes, the top-line facts — so the eye can find the structure without reading it.
- **The photography is given room.** Each concept card is a wide 16:10 banner of the Qloo photograph that came with the venue, credited to the place it belongs to, and the places Qloo returned are shown again as a full strip with their own affinity, popularity and rating printed beside them.
- **The constellation reads.** The graph's rings are further apart, every label is broken over at most two lines, each label sits on its own band just outside its ring, and a halo of the panel colour keeps a word readable where it crosses an edge.

Both themes were re-drawn for it: the dark theme is warm soil, beet and clay; the light theme is cream paper with near-black rules and flat offset shadows. `prefers-reduced-motion: reduce` still stands the new transforms down.

### Background video and Safari

The background video uses the attributes Safari requires for inline autoplay — `autoplay muted loop playsinline` — plus `preload="auto"` and a `poster`. Two details matter:

- **The MP4 is faststart.** Its `moov` index sits in the first 40 KB rather than at the end of the 13.8 MB file. Without that, a browser that does not do a tail-range lookup has to download the entire file before it can play anything. The file is remuxed by `python3 scripts/fix_mp4_faststart.py assets/cultureforge-background.mp4`, which moves `moov` ahead of `mdat` and rewrites the `stco` chunk offsets to match. It is a container-only operation, so there is no re-encoding and no quality loss.
- **Autoplay can still be refused.** Safari applies its own autoplay policy, and a visitor who has blocked autoplay for the site will not get motion. `initBackgroundVideo()` in `main.js` therefore retries playback on the first pointer, touch, key, or scroll event.
- **The page never shows a white panel.** Safari paints a video's own surface white until a frame is decoded, and it draws the native play/pause bar over a paused video. The poster is therefore painted on the `.bg` container as a CSS background, and the `<video>` element stays at `opacity: 0` until it fires `playing` and gets the `is-playing` class. A blocked or paused video is invisible, so there is nothing to flash white and no control bar to show. The video is decorative, so it is paused entirely for visitors who prefer reduced motion.

## How Qloo drives the answer

The app does not display Qloo data next to a mock answer. The Qloo data *is* the answer.

```
audience text
  → find_tags   → real Qloo audience tags        (varies per audience)
  → recommend   → real local venues for the brief (varies per location)
  → composer    → three business directions, each citing the venues it used
```

- **The audience lens** is the set of Qloo tags `find_tags` resolves for the founder's audience description. A brief about "mindful professionals" resolves to `mindful_dining` and `mindful_nutrition`; a brief about "design-conscious Gen Z" resolves to `gen_z_foodies` and `modern_restaurant_design`. These tags select which business direction the composer builds.
- **The local evidence** is the set of venues `recommend` returns for the location, each with its real name, description, popularity, affinity, local rating, price level, geocode and image. Every concept cites the venue it was built from.
- **The business reading** is CultureForge's, and is labelled as such. `backend/concept_composer.py` holds the rules; every proposal records the evidence it came from, and the UI shows them under "Why this direction?".
- **The verdict is not CultureForge's opinion.** `backend/challenge.py` puts each direction on trial against the local evidence with two more Qloo workflows, and a direction can come out contested. The order the directions are shown in afterwards is the order the evidence leaves them in, not the order they arrived in.
- **No invented scores.** An evidence-composed concept has no audience-fit percentage, because Qloo's affinity does not measure business fit. The UI says so rather than showing a number that means nothing.
- **Abstention beats padding.** If the evidence does not support three distinct directions, the app returns fewer and says why, rather than filling the gap with catalog concepts.
- **A dead end is not a dead end.** Some places Qloo simply cannot resolve — "Greenpoint, Brooklyn" comes back empty. The app says which location failed, and, if it already holds places for the same signals somewhere else, offers that location as a one-click way forward. The suggestion is only ever a location Qloo actually returned places for, so it is evidence rather than a guess, and taking it spends no request.

The scenario lab re-researches for real. Changing the audience calls `POST /api/projects/compare`, which runs the same two Qloo workflows against the new audience and returns fresh evidence and freshly composed directions — not a locally computed score shift.

### Naming the directions with a free model

The composer is a rule engine. A direction inherits the recipe's name, so every brief that unlocks the same recipe gets the same title — "The Design Floor" twice, for two different cities. That is the one place where the answer reads as though it was written before the venue was known.

An optional layer fixes it. A free model writes the **name**, the **tagline**, and **one sentence of why this audience fits this place**. It is given the audience signals and the venues the direction is built from — and **no numbers at all**, so it cannot quote one. Anything else it writes is discarded: a number that Qloo did not return, a citation, a field that is too long or too short. The rules keep every decision: which tags, which venues, which facet, which evidence each decision cites.

It is free, and it stays free:

- The key comes from [openrouter.ai/keys](https://openrouter.ai/keys) and needs no credit. `OPENROUTER_MODEL=cohere/north-mini-code:free` is the model that answers this prompt; `openrouter/free` (the Free Models Router) is in the fallback chain.
- **The model is refused if it is not a free one.** A paid model in the fallback chain is billed by OpenRouter, so `backend/llm.py` keeps the chain free-only and refuses anything else.
- The free tier allows 50 requests a day — 1000 once $10 of credits is on the account. So the model is a **cache, not a service**: one call per brief, held in the same evidence store as the Qloo envelopes, and a repeated brief costs nothing. The local guard sits at the tier's own limit (20 an hour, 50 a day), so a judge can work through the whole allowance and no further.
- Without a key, or when the tier is spent, or when the model is late, the rule engine's wording is used and the trace says which happened: `name-the-directions → skipped`.

### The evidence test — the part that can come back with a no

Every tool that reads an API answers with what the API holds. This one asks the harder question, and it is built so the answer can be **no**.

The composer produces three directions. `POST /api/projects/challenge` puts them on trial against the local evidence, with two checks:

1. **Where does this place sit for that profile?** (`rank`) Qloo ranks the retrieved places for a demographic profile CultureForge proposed from the founder's own words — and says so, because the request carries a profile and a location, not the audience's own cultural tags. An anchor ranked *last* within the returned set fails this policy's relative-ranking check.
2. **What cultural tags were returned for this anchor?** (`compare_audiences`) The anchor is compared with **every other place that was returned**, cited or not, so changing the anchor changes one assumption and not two. Qloo's tag URNs carry their family, and the family is what makes this readable: a `genre` or `category` tag says what the place **is** — every place has one — while `cuisine`, `ambience`, `good_for`, `inclusivity` or `activities` says what culture **happens** there. A tag returned for the anchor is *a potential input to a concept*, never a claim of exclusivity: the comparison response is a bounded list, and absence from it is not proof.

The verdict is deliberately narrow, and the reason for it is the evidence that decided it:

| Verdict | What it means |
|---|---|
| `Anchor fit supported` | It passes the checks that could be run, within the evidence that was retrieved. |
| `Anchor fit contested` | The evidence contradicts a specific premise, and the premise is named. |
| `Unproven` | There was not enough retrieved evidence to say either way. |

**The scope is stated, because it is narrow.** The verdict says whether the *anchor fit* holds **within the retrieved sample** — whether the place a direction is built around ranks well for the proposed demographic profile, and whether Qloo returned a qualifying cultural tag for it in the comparison with the other retrieved places. It does **not** say the business is good, and it does not measure demand, profitability, footfall or commercial viability. A high-scoring place is not a high-scoring business, and a judge who reads the scope line knows it.

**The decision policy is inspectable.** Every direction states its claim, what would contradict it, and what would leave it unproven — *before* the verdict is read — and the panel shows the policy version that produced it (`anchor-fit-3`). A verdict that cannot be traced to the policy that made it is an opinion, not a verdict.

**The checks say what they actually did.** The ranking request carries a demographic profile and a location, not the audience's own cultural tags, and the verdict says so: *"Qloo ranks The Bell House first of the 5 places it returned for the 'gen z' demographic CultureForge proposed from the brief, near Brooklyn, New York. This ranking does not use the audience signals you selected."* The comparison is against **every other place that was returned**, cited or not, so changing the anchor changes one assumption and not two; and a tag returned for the anchor is never called exclusive, because the comparison response is a bounded list and absence is not proof.

**The judge holds the claim to a different place.** Each direction lists the other places it could have been built around. Click one and the same claim is re-tested against it: *"This wins under these assumptions; change this assumption and it loses."* On the example brief, "The Artful Pour" is contested on the Whitney Museum — and **supported** the moment it is held to The Bell House, at which point it takes first place. The dependence is exposed rather than hidden behind a score.

**Removing a place really rebuilds the answer.** Drop a venue from the evidence panel and the directions are composed again from what is left — the removed place goes out of the description, the photograph, the citations and the anchor. It costs no Qloo request, because the held evidence is enough. The names come back as the rules' own, because no model was asked.

**The order changes.** A direction the evidence supports leads; one it argues with is last. On the brief the studio ships with, the direction that arrived first is contested — *"Qloo ranks Whitney Museum of American Art last of the 5 places it returned for the 'gen z' demographic Qloo inferred from the brief, near Brooklyn, New York. It ranks last within this retrieved set."* — and a different one leads. The panel, the concept cards and the landing page all show the same order, and a card says what it was: **DIRECTION 01 · WAS 02**.

Every verdict states the limits, next to the badge rather than in a footnote: *anchor fit within the retrieved sample — not demand, profitability, footfall, or commercial viability.* The studio also discloses what it judged on: how many places Qloo returned, how many the direction cites, and the profile that was ranked against.

### The front page performs it

A judge who never clicks still sees the product working. The landing page runs one real brief on its own — the same backend, the same cache, the same Qloo calls — and then puts the answer on trial, and says plainly when the evidence contested it.

### What the free tier is actually like

The free pool is smaller and noisier than the model list suggests, and the code is shaped around what was measured rather than what is documented:

- **Most of the free models are withdrawn or busy.** Of the models OpenRouter lists as free, several now answer `404` (taken down) and one answers `429` (rate limited). A withdrawn model in the chain is not a failure — the request falls through to the next one.
- **Most of them are reasoning models**, and a reasoning model given the whole token budget spends all of it thinking and answers with nothing at all. The request caps the thinking (`reasoning.max_tokens`) and leaves the room the answer needs. Without that cap, the same model returns an empty answer and the direction keeps the rule engine's name.
- **Quality varies wildly.** One free model answers a direction's name with `...`. The guard drops any field that says nothing, so a weak model costs the founder the model's wording, never a wrong number.
- **Every request is one brief, not one interaction**, and the answer is held. A demo that runs the same brief twice spends one request between them.

### How the switching works

`openrouter/free` is a lottery: it picks a free model at random each time, and some of them take twenty seconds to think. So the backend does not leave the routing to chance:

- **A refusal is remembered.** A model that is rate limited is skipped for fifteen minutes, a withdrawn one for the rest of the day. The next brief does not pay for finding that out again.
- **The model the router picked is remembered and asked directly.** The answer names the model that gave it, so the next brief asks that model — no lottery, and the same few seconds every time.
- **A model that answers well and quickly is asked first.** How each model answered — usable or not, fast or slow — is kept in `~/.cache/cultureforge/llm_models.json`, and the order follows it.
- **The switch itself is instant.** Reading the local file takes no time; the wait is the model's own, and one attempt is capped at fourteen seconds, with the whole naming capped at twenty-two. A brief that has waited long enough gets the rule engine's wording rather than a slower title.
- **Only what was served is charged.** A model that is withdrawn or busy serves no inference, so it does not count against the allowance.

`GET /api/health` reports the whole thing: which models are answering, which are refusing, and how much of the daily allowance is left.

```bash
python3 scripts/llm_check.py          # read-only: what is configured
python3 scripts/llm_check.py --live   # one request, one answer
```

The step is visible in the studio's own trace, next to the Qloo calls it sat between.

### The honest boundary

| Label | Meaning |
|---|---|
| `Fresh Qloo evidence` | Retrieved from the Qloo API for this request. |
| `Cached Qloo evidence` | Retrieved earlier and reused from the server's evidence store. The acquisition time is shown. |
| `Held in this browser` | The same real answer, held locally by the studio so a reload is instant. Still zero upstream requests. |
| `Named by <model>` | The direction's name and tagline were written by the free model, from the venues the direction is built from. The evidence and every number are still Qloo's. |
| `Supported` / `Contested` / `Unproven` | What the evidence test found. The reason is the evidence that decided it. |

Nothing in the studio is a dead end: if the audience resolves to nothing, the agent can resolve it itself; if a run fails, there is a way back to the brief; if a place has no photograph, the card says so instead of showing a broken image; and if the demo has spent the quota, the answer says so and keeps serving the evidence it already holds.

The results screen also states what the demo has cost: *this workspace has served N API requests and spent M upstream Qloo calls.*

`How this was researched` shows the real tool calls with their real durations, result counts, endpoints and correlation IDs.

Each result also reports how many upstream requests it actually cost. Evidence that was already held costs nothing, and the count says `0 upstream requests` rather than pretending the API was asked. The durable store keeps the evidence across restarts, so a repeated brief is instant and free, and a live demo never spends the same quota twice. The studio holds the composed answer in the browser for twelve hours on top of that, so a reload paints the same exploration without a round trip, and the label says the answer was held rather than fetched.

## Investigating a direction

A brief produces three directions, and each one rests on the venues Qloo
returned. It also rests on things nobody has checked. The **Investigate**
action opens them.

| Question | Qloo workflow | What it answers |
|---|---|---|
| Where does it concentrate? | `where_popular` | Geographic cells with real latitude and longitude. |
| Do the venues share a signature? | `entity_tags` | The concepts that characterise them. |
| Who is indexed against it? | `audience_demographics` | A signed age and gender index. |
| What is Qloo's full record? | `describe` | Description, address, geocode, rating, image. |
| Is it gaining or losing momentum? | `trends` | Popularity over time. |

The founder picks the direction and the questions. Each question is one named
workflow, and the report says which workflow produced the answer, whether the
evidence was reused or freshly fetched, and what it could **not** establish. A
rate-limited or exhausted call becomes a stated limitation, never a crash.

### The geographic interest plot

`where_popular` returns geographic cells: a latitude, a longitude, an
affinity and a popularity. The studio draws them as an interest plot.

It is not a street map, and it is not where the venues are. Qloo's geocode
carries an address rather than a coordinate, so the venues themselves cannot
be pinned on a real map. What this plot shows is where *interest* in a kind
of place concentrates — which is a different, and supported, claim.

Within one area Qloo's affinity is often almost identical across every cell.
Encoding a spread of 0.001 would draw twenty identical dots and imply a
comparison the data does not support, so the plot falls back to popularity when
the affinity spread is negligible, and the legend says which metric it is
encoding. There is a table of every cell for anyone who would rather read the
numbers.

## Licensing the product

The studio runs in a local workspace, so a founder never signs up for anything
to try it. A partner calls the same API with an issued key and lands in their
own workspace, where everything they save is theirs.

- **Workspaces.** Every private resource belongs to one, and every read checks
  the caller owns it.
- **Issued keys.** A key is stored as a salted hash, shown once at issue, and
  never recoverable. Keys carry scopes, can expire, and can be revoked.
- **Saved explorations.** Every answer is saved automatically, with the
  composer version that produced it, and each recomposition becomes a new
  version rather than an overwrite.
- **Export.** An exploration downloads as JSON or as Markdown a founder could
  send to a partner.
- **Metering.** API requests and the upstream Qloo calls they cause are
  counted separately, because they are two different costs. A fresh brief is
  one API request and two upstream calls.
- **Share links.** A shared snapshot is immutable, explicitly created,
  revocable, and reached through a long random token rather than a guessable
  id.

What is deliberately not here yet: self-service signup, billing, member
invitations, role-based access, webhooks, and arbitrary workflow builders.
There is no commerce behind the operator-provisioned keys, and pretending
otherwise would be a bigger lie than leaving it out.

## Verifying the backend and frontend agree

`npm run test:contracts` pins the `GenerateResponse` contract from `src/contracts.ts` and checks both producers against it:

```
$ npm run test:contracts
[ok]   GET /api/health -> live, 9 workflows
[ok]   GET /health alias -> 200
[ok]   POST /api/projects/generate -> live, 3 concepts, 5 signals
[ok]   the frontend has no mock fallback -> real data, or a stated error
[ok]   422 detail is readable -> "businessType: Input should be 'Food & beverage', ..."
All contract checks passed.
```

It fails if the backend renames, drops, or retypes a field the UI renders, if the studio ever reaches for a mock generator again, or if an error stops returning a readable `detail` string. It needs the backend on port 8000 and the dev server on port 5173; `BASE_URL` and `DEV_URL` override them.

## Testing every endpoint by hand

The judges will click the API by hand, so `npm run test:endpoints` walks all
twenty-six routes the way a person would: the happy path, the missing thing,
the malformed thing, the wrong method, the empty body, and the same request
with a bearer key, a wrong key, and a revoked key.

```
$ npm run test:endpoints
[ok]   POST /api/projects/generate -> a bad brief is 422 with a readable reason
[ok]   a failure carries the error envelope -> VALIDATION_FAILED req-9f2c1a04b7de
[ok]   POST /api/projects/compare/audiences -> a malformed group is 422, not a silent character list
[ok]   POST /api/qloo/where-popular -> answers in its own shape -> 200 20 results
[ok]   POST /api/projects/investigate -> it names the workflow it called -> where_popular
[ok]   GET /api/workspaces/{id}/keys -> the secret is not stored in the clear -> 200
[ok]   a revoked key no longer authenticates -> 401
[ok]   GET /api/explorations/{id}/export -> Markdown a founder could send -> 200 3827 chars
----------------------------------------------------------
Endpoints exercised: 26
Every endpoint answers. 60 checks passed.
----------------------------------------------------------
```

It is the check that found the four defects the typed request models now
prevent: three routes took a raw dict, so a malformed request was
reinterpreted rather than rejected.

## Walking the product as a business owner

The contract check proves the shapes agree. It does not prove the product works. `npm run test:walkthrough` walks the whole journey a founder takes, in order, and asserts what each step must hand the next one:

```
$ npm run test:walkthrough
--- the founder walks in ---
[ok]   the backend reports which provider is active -> dataMode live
[ok]   the studio is served -> HTTP 200
[ok]   the brief returns a result -> 3 directions
[ok]   the audience resolves into candidate signals -> Gen Z Foodies, Modern Restaurant Design, Food Design
[ok]   the research run starts -> run-dc14db07d37e
[ok]   the run finishes -> status complete
[ok]   there are three directions -> The Design Floor | The Neighbourhood Table | The Slow Hour
[ok]   every decision cites evidence that exists -> 8 pieces of evidence
[ok]   no invented fit score is shown -> affinity does not measure business fit
[ok]   the request that was sent is recorded -> filter.type+take+signal.interests.tags+…
[ok]   no unexpected parameter reaches the provenance panel -> all allowlisted
[ok]   removing a venue returns a recomposition -> Qloo was not called again.
[ok]   the recomposition keeps only directions that still have support -> 3 of 3 survived
[ok]   Qloo compares the two groups -> 3 shared tags
[ok]   Qloo ranks the venues -> 1. The Bell House | 2. Brooklyn Bridge Park Corporation | …
[ok]   the signal Qloo actually sent is reported -> 24_and_younger
[ok]   the exploration can be shared -> snap-a575cbe437dc
[ok]   a repeated brief spends no upstream request -> 0 upstream requests, delivery cache
[ok]   the investigation returns real geographic cells -> 20 cells
[ok]   the map says what it is not -> interest cells, not venue pins
[ok]   changing the audience re-researches -> The Neighbourhood Table | The Slow Hour | The Third Place
[ok]   a location Qloo cannot resolve is reported, not guessed at -> Qloo returned no places for 'Greenpoint, Brooklyn'…
[ok]   the message offers a location Qloo already returned places for -> 'Brooklyn, New York' returned places for these same signals earlier.
----------------------------------------------------------
The whole journey works. 46 checks passed.
----------------------------------------------------------
```

Twelve steps, from landing to a cached repeat, including the investigation loop. Every step runs against cached evidence, so the whole journey is free and the script refuses to spend quota it did not intend to. It needs the backend on port 8000 and the dev server on port 5173.

## Cinematic layer

The front page is treated like a title sequence rather than a document.

- **Grade stack** — a colour wash, a vignette, and animated film grain sit over the video, so the frame reads as graded footage instead of a raw background.
- **Depth** — the video runs a slow Ken Burns push-in and drifts against the scroll, so the page has a foreground, a midground, and a background.
- **Masked reveal** — the headline lines rise out of a mask with a light sweeping across them once they settle.
- **View transitions** — moving between Home, Product, Case Studies, and Contact cross-fades and blurs rather than cutting.
- **Pointer light** — a soft glow follows the cursor on the call to action, which is also gently magnetic, and a spotlight tracks the hovered nav link.
- **Curtain** — "Open studio" wipes the front page away behind a branded curtain and hands over to the studio; "Landing" wipes back.
- **Studio atmosphere** — the workspace carries its own slow aurora and a fine grain, concept cards rise in one after another, and the selected card's photo carries a slow sheen.

Every effect respects `prefers-reduced-motion: reduce`: the grain, aurora, Ken Burns, headline sweep, curtain wipe, and card reveals all stand down and the content is shown immediately.

## API

Every route takes a typed request and answers with a typed response, or with one
error envelope. The FastAPI backend exposes:

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Which provider is active, the version, and the Qloo workflows the app can reach. |
| `POST /api/projects/generate` | Takes a `ProjectRequest`, returns a `GenerateResponse`. |
| `POST /api/projects/compare` | Re-researches the same brief for another audience, with real calls. |
| `POST /api/projects/compare/audiences` | Qloo's own A/B between two groups of entities. |
| `POST /api/projects/rank` | Ranks real Qloo entities against a signal set or a demographic. |
| `POST /api/projects/recompose` | Rebuilds the directions without a piece of evidence. No new call. |
| `POST /api/projects/investigate` | Opens the questions a direction has not answered, and answers them. |
| `GET /api/facets` | The questions an investigation can open, in plain language. |
| `POST /api/taste/resolve` | Resolves an audience into candidate Qloo seeds, before any research. |
| `POST /api/research/runs` | Starts a bounded research run. `202 Accepted`, with where to poll. |
| `GET /api/research/runs/{id}` | The run's events, status, and result. |
| `GET /api/research/runs` | The recent runs. |
| `POST /api/explorations/share` | Freezes an exploration into a shareable snapshot. `201 Created`. |
| `GET /api/snapshots/{id}` | A stored snapshot. |
| `GET /api/explorations` | The explorations this workspace has saved. |
| `GET /api/explorations/{id}` | One saved exploration, with its versions and its result. |
| `GET /api/explorations/{id}/export` | The exploration as JSON or Markdown. |
| `POST /api/workspaces` | Provisions a workspace for a partner. |
| `POST /api/workspaces/{id}/keys` | Issues an API key. Shown once. |
| `GET /api/workspaces/{id}/keys` | The keys issued for a workspace. |
| `DELETE /api/workspaces/{id}/keys/{keyId}` | Revokes a key. |
| `GET /api/usage` | Requests served, and the upstream calls they caused. |

Qloo's own workflows are reachable directly, one route each:

| Endpoint | Qloo workflow |
|---|---|
| `POST /api/qloo/describe` | `describe` — one entity, and the metadata Qloo holds. |
| `POST /api/qloo/entity-tags` | `entity_tags` — the concepts that characterise a set of entities. |
| `POST /api/qloo/where-popular` | `where_popular` — geographic cells for interest mapping. |
| `POST /api/qloo/audience-demographics` | `audience_demographics` — a signed age and gender index. |
| `POST /api/qloo/trends` | `trends` — popularity over time. |

`GET /health` is an alias of `/api/health` for tooling that probes the conventional path.

### The error envelope

Every failure answers the same way, so a caller branches on the code rather than
on the wording:

```json
{
  "detail": "Qloo returned no places for 'Greenpoint, Brooklyn' for this audience.",
  "error": {
    "code": "NO_EVIDENCE",
    "message": "Qloo returned no places for 'Greenpoint, Brooklyn' for this audience.",
    "retryable": false,
    "details": { "location": "Greenpoint, Brooklyn" }
  },
  "requestId": "req-9f2c1a04b7de"
}
```

`detail` is kept because the studio renders it straight to the founder. The
codes are `INVALID_REQUEST`, `INVALID_UPSTREAM_REQUEST`, `VALIDATION_FAILED`,
`NEEDS_INPUT`, `NO_EVIDENCE`, `NO_CACHED_EVIDENCE`, `RATE_LIMITED`,
`ALLOWANCE_EXHAUSTED`, `QUOTA_EXHAUSTED`, `PROVIDER_UNAVAILABLE`,
`UPSTREAM_TIMEOUT`, `UPSTREAM_UNAUTHENTICATED`, `UPSTREAM_MALFORMED`, and
`UPSTREAM_REJECTED`.

The status codes mean something: `201` for a created snapshot, `202` for
accepted background work, `422` for a request that is wrong or that Qloo's own
contract would reject, `404` for something that is not there, `409` for a
conflict, `429` for a rate limit, `503` for an exhausted budget or an
unavailable provider, `504` for a timeout, and `502` for anything else
upstream.

### The Qloo contract

Each Qloo workflow has its own request contract, and each rejects fields it
does not know. `describe` takes `type`; `where_popular` takes `entity_type`;
`rank` has no `limit` at all; `rank`'s `signals` are entities while tags belong
in `include_tags`; and a `demographic` requires an explicit location. The
payloads are built per workflow, in `backend/providers.py`, so the field names
are right by construction rather than by luck. The tests pin them.

In development Vite proxies `/api` to port 8000; a static build of `dist/`
needs the same proxying, or the browser will need the origin allowed by the
backend's CORS configuration.


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

It fails if the backend renames, drops, or retypes a field the UI renders, if the studio ever reaches for a mock generator again, if an error stops returning a readable `detail` string, or if a concept cites evidence that does not exist. It needs the backend on port 8000 and the dev server on port 5173; `BASE_URL` and `DEV_URL` override them.

## The offline fixture

`backend/mock_generator.py` is the only mock left, and it is not reachable from the product. It is what the pytest suite runs against, so the HTTP contract — the typed requests, the error envelope, the status codes — can be checked without touching the Qloo quota. `backend/tests/test_api.py` swaps it in explicitly; the rest of the suite uses the captured fixtures in `backend/fixtures/`. The studio cannot reach it: `get_provider()` returns it only when `CULTUREFORGE_PROVIDER=mock` is set by name.

Typography now uses 14–16px body and control text with larger card headings. Longer concept descriptions flow naturally, medium-width cards use a wider image/text layout, and mobile scenarios stack audience summaries vertically.
