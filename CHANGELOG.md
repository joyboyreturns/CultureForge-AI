# Changelog

## Unreleased — live-run hardening, 2026-10-23

Every item below was found by running a real brief against Qloo and the configured model (see
docs/LIVE_MATRIX.md), and each has a test that fails without the fix.

- **Held demos no longer replay a failed agent.** An agent loop that ended because Qloo was switched off,
  rate-limited or out of quota is never held, and one already held is discarded and re-run. The featured
  demos had been held with a lone `LIVE_DISABLED` step. With no evidence added, no analysis is written.
- **A held replay costs nothing.** A held agent report's steps carried the requests of the run that paid
  for them, so a free replay reported "2 upstream requests". It now reports 0, and the agent card says
  "held · fetched earlier".
- **Category words follow the model reading.** A category read by the model carried only the typed word, so
  Qloo's own "bookstore" and "Librerías" never matched and ten real Mexico City bookshops produced no
  direction. It now uses the category's synonyms.
- **Unfamiliar categories match on identity.** A drive-thru coffee shop that lists tea among its drinks was
  a "direct tea house"; a place now matches on its name and how its description opens.
- **No agent for an empty answer.** With no direction composed the agent loop no longer spends requests and
  two minutes on claims about nothing. The reason names the place Qloo returned for the wrong city.
- **Agent analysis tolerates length.** An over-long summary clipped at a sentence rather than discarding the
  whole answer; fenced JSON is read; rejections log the failing schema fields (never the text).
- **Unsupported categories offer a way out** built from the founder's own words ("film camera shop" →
  "camera shop").
- **Fair use for a public demo** (`backend/admission.py`): identical running briefs are joined; at most
  three new ideas at once; eight new ideas an hour per visitor (address from `X-Forwarded-For` behind a
  local proxy only); two agent loops at once. Held evidence is never limited. A refusal is a 429 with
  `Retry-After` and a way forward.
- **Open the initial answer now.** The directions exist seconds after Qloo answers. The workspace offers
  them at once, labelled as initial, while the run keeps going and the monitor offers the finished results.
- **What Qloo contributed** strip in the executive brief: cited decisions, the extra workflows the agent
  chose (and which were refused), who produced each (rules or model), and whether anything pushed back.
- The landing page's example and the Create form now open the Tokyo bakery (it names its idea and ships in
  the demo pack) instead of the Brooklyn brief that named none.
- `scripts/brief_probe.py`: one brief through the real research-run path with timings and cost.

## Unreleased — business intent and tag resolution

- **Business intent** (`backend/intent.py`). An idea is read into typed components: every business it names
  (a hybrid is two components, never one), every specialisation word, and every simplification as a sentence.
  Fixes the silent truncation of "bakery combined with a bookstore" to a bakery, and the silent loss of
  "vegan" and "specialty".
- **Tag resolution is staged and honest.** `rank_category_tag` reports `exact` or `near` (name matches
  only: Qloo documents no tag hierarchy). A specific phrase that matches no tag may fall back to one broader
  search string, disclosed as CultureForge's own broadening. Nothing else is ever substituted. New code
  `UNSUPPORTED_CATEGORY` when no returned tag matches; a category with no local places is `NO_EVIDENCE`
  with `details.reason = category_no_places`.
- **Hybrids.** The second business is resolved and retrieved separately (at most two extra workflows, three
  with the category-only fallback), shown as its own evidence stream; overlap is only places Qloo returned
  for both, otherwise "Overlap not established".
- **One optional model reading** (`llm.interpret_business`) only when the rules cannot read the idea. Its
  answer is a validated proposal of component phrases and search strings; it cannot name a tag.
- **Negative cache.** A verified empty `recommend` for a category, city and audience is trusted for
  `CULTUREFORGE_NEGATIVE_TTL_HOURS` (default 6) instead of the full evidence TTL. Failures are never held.
- **Relevance.** An unfamiliar business matches on all its product words (not any one), plurals count, and
  specialisation words are reported against the returned text ("1 of 10 returned places mention vegan").
- **UI.** "How your idea was read" panel, a typed clarification card whose actions all work, and typed
  failure copy with Try again / Change the location.

## Earlier unreleased — judging hardening, 2026-10-22

- Resolve business categories from returned Qloo taxonomy IDs and expose
  direct/indirect relevance decisions. Compose only relevant, differentiated
  directions; abstain when the retrieved references do not support one.
- Publish actual intermediate research results, reconnect after reload, and
  show an interactive evidence graph with source removal and recomposition.
- Withhold comparative model winners without completed comparison evidence;
  expose partial challenge checks under policy `anchor-fit-5`.
- Harden cache publication, persistence warnings, replay versions, API errors
  and CORS. Fix Linux PDFs with a Latin primary font and CJK fallback.
- Record real Tokyo Qloo/model observations, browser checks, container
  execution, remaining release gates and a provider handoff in the review docs.

## 0.3.0 — 2026-10-22

### Added
- **Run profiles.** `RUN_PROFILE=dev|judging` in `backend/config.py`. Judging lifts every call-count budget and keeps the timeouts, the error mapping, a cool-down after a Qloo 429, single-flight de-duplication and the cache. `QLOO_LIVE_ENABLED=false` serves held evidence only.
- **Prewarming.** Eight prepared briefs (`shared/demoBriefs.json`), `scripts/prewarm.py`, `GET /api/examples` (which briefs are held), and an example picker in the studio.
- **Audience bridge.** The brief's audience tags are also sent to other domains (artist, movie and brand by default), and every direction cites the results as audience-level cross-references. The place sample doubled to 10.
- **Agent loop.** Up to eight plan-act-observe steps over the allowlisted Qloo workflows, with server-built requests, then an analysis whose claims must cite observed Qloo IDs.
- **Ask the evidence.** `POST /api/chat`: follow-up questions answered from the evidence, or refused.
- **Evidence policy anchor-fit-4.** A written rule with a minimum sample, a confidence label and leave-one-out and alternative-anchor sensitivity; the profile is chosen before the test runs (`docs/EVIDENCE_POLICY.md`).
- **Interest map.** `where_popular` interest cells as a results view.
- **PDF report.** `POST /api/report/pdf`.
- **Deployment.** `docker-compose.yml`, `render.yaml`, `scripts/smoke_test.py`.
- **Docs.** DEPLOY, DEMO, SUBMISSION, JUDGING_DAY, BUSINESS, EVIDENCE_POLICY, ARCHITECTURE, API, LIMITATIONS.
- **Tooling.** ESLint, payload snapshots, a complete harness error-mapping table, and coverage in CI.

### Changed
- The studio and the trace name the model that answered (`AI_GATEWAY_DISPLAY_MODEL`, or else the model id) instead of "Frontier AI".
- The "distinctive" facet is now a measurable least-mainstream ordering, and each direction states how its reference was chosen.
- The budget ledgers moved from JSON files to one SQLite file that is safe across processes; existing history is imported once.
- A held answer reports when its evidence was fetched and when it expires.
- The buyer named in the product and docs is location and concept strategists at hospitality and retail groups and brand agencies.
- Agent scaffolding (the graph, the vault and tool configs) is local-only and no longer tracked.

### Fixed
- A live "bakery in Tokyo" run found and fixed:
  * model requests are paced to the gateway's 5-a-minute limit (`LLM_REQUESTS_PER_MINUTE`) and a 429's `Retry-After` is waited out once, instead of ending the agent loop on a plan that was merely refused;
  * model timeouts were 40-60 seconds against a model that took 5-29 seconds for a low-effort answer, so they are 75-120 seconds, and the final analysis and chat answer get one more attempt if malformed;
  * the Qloo rate-limit pause is shared by every provider instance and starts only after two answers in a row, because Qloo refused one specific comparison on every attempt while others worked;
  * live Qloo requests are spaced (`QLOO_MIN_CALL_INTERVAL_SECONDS`);
  * the evidence test reports a partial result (unproven, with Qloo's code) when part of it cannot run, instead of one error;
  * the PDF prints Japanese and other non-Latin place names with a Unicode font when one is installed;
  * the answer states the whole run's cost, Ask the evidence survives a failed planning step, and any unexpected server error is the standard envelope with a request id instead of a bare 500;
  * the studio sent the proposed evidence-test profile as if the user had chosen it.
- The demo defaults to no call-count caps: `docker-compose.yml` and `render.yaml` run `RUN_PROFILE=judging`, and the judging evidence TTL is 30 days.
- The sidebar no longer shows a personal workspace name; it reads "Shared workspace".
- The Render blueprint deploys with `RUN_PROFILE=judging`, so the public demo runs with every call-count budget off (dev stays the default everywhere else).
- The provenance drawer stayed open over other screens, still showing a place that had been removed; it now closes when the screen or exploration changes.
- Changing the evidence-test profile after a test left verdicts on screen that were produced for another profile with no warning; the chooser now says so.
- Repeating the same brief filled the shared workspace with copies; it is now one saved exploration, with a new version only when the answer changed.
- The share link has a Copy link button.
- Stale or inconsistent copy: "founder" in the trace, "last fails" (now bottom third), a fixed count of open questions, "3 original directions", the footer line, mixed UK and US spelling, and a missing model-name fallback.
- The `where_popular` route accepted up to 100 cells; the harness caps the workflow at 20.
- The test suite could reach the real Qloo CLI and the model gateway when a workflow missed the test's store or a `.env` enabled the model. Both are now blocked in `conftest.py`.

## 0.2.0 and earlier

See the git history before `be3d142`.
