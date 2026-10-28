# Changelog

## Unreleased — first evidence and visible completion, 2026-10-23

- Open evidence-bearing initial answers automatically while research continues.
- Follow the run in a floating status card; update the matching preview to the
  full report automatically, with a completion message. Preserve other screens
  and other briefs; keep the detailed trace accessible without redirect loops.
- Replace generic waiting-time copy in the form and README with the actual
  first-evidence journey. Document London's measured eleven-second initial
  answer separately from its 109-second completed report.
- Describe the 14-trial gallery, shared city-filter fix and evidence challenge
  in the README before the proposed commercial offer.

## Unreleased — fix live place retrieval and expand trials, 2026-10-23

- Isolated the Berlin timeout to a wrongly used location role: with the same
  tags, category and result count, a result-location filter returned ten places
  in under nine seconds. Full Berlin research and its evidence test completed.
- Use result-location filters for fresh primary, hybrid, agent and replacement
  place searches. Preserve original successful cache keys and provenance;
  prefer modern held responses and do not reuse legacy empty answers.
- Extend known-location recovery to the corrected request form. Keep audience
  location signals for demographic ranking, where they are intentional.
- Added Berlin, Mexico City and Vienna to a 14-brief trial library, exposed on
  overview/results with category filters and in a scrollable creation list.
- Package their real responses without fetching or inventing replacement data.
- Regression suite: 444 passed.

## Unreleased — judge input hardening, 2026-10-23

- Verified all 11 prepared ideas across five categories, including citations,
  cited-place removal, scoped verdicts and PDF responses, without new calls.
- Tested fresh Berlin, Mexico City hybrid and unsupported Singapore inputs;
  recorded successful, clarification and upstream-timeout outcomes separately.
- Reject whitespace-only audience/city inputs before provider access and offer
  a direct edit action for unresolved audiences.
- Stop planning after three consecutive invalid agent requests, and explain
  that audience comparisons require place entities rather than tag URNs.
- Make the live one-brief probe fail its exit status when the run fails.

## Unreleased — hackathon first presentation, 2026-10-23

- Replaced Pilot in desktop and mobile navigation with Why Qloo: a source,
  challenge and removal walkthrough connected to the working studio.
- Made Try the demo the primary landing action.
- Removed the landing example's fixed promise of three directions; the
  composer returns only the directions its retrieved evidence supports.

## Unreleased — commercial pilot and validation, 2026-10-23

- Added a Pilot page with a proposed offer, scope, acceptance criteria and a
  local downloadable discussion brief. No inquiry or payment is transmitted.
- Renamed the landing navigation's Case Studies to Evidence test to describe
  the actual content without implying customer case studies.
- Added accountable owner, review date and a team-entered spending cap to the
  existing local decision notebook and its Markdown export. Older notes remain readable.
- Wrote a concrete business model, customer-validation gates, illustrative
  cost constraints and investment milestones; prices and results remain labeled hypotheses.
- Updated the contract checker to recognise the existing agent, intent,
  address, coordinates and running-state fields.
- Rechecked the held-evidence HTTP journey with Qloo and model calls disabled.

## Unreleased — the studio takes the landing page's look, 2026-10-23

- **One look from front page to studio.** A new last stylesheet (`src/dusk.css`) gives the studio the
  landing page's dusk: the same scene from `landing-scene.js`, painted once as a still frame and veiled
  behind every screen, the Geist Pixel display face for headlines, Inter for text, white pills for the next
  step, dark glass for panels and lavender as the one accent. The old green tokens and hard-coded greens
  were moved to the matching violet at the same lightness; "supported" and "ok" stay mint so they still
  read as good. The light theme follows.
- **The concept studio is read one section at a time.** The evidence workbench was one long scroll. It is
  now seven sections — Executive brief, Evidence trace, Places & signals, Directions, Evidence test,
  Decision, Cultural roots — listed under Concept studio in the sidebar (with place and direction counts and
  a mark once tested) and in a sticky section bar, each ending in Previous / Next. A finished evidence test
  opens its section; the guided tour opens the section its step points at.
- **Readability fixes found on the way.** The "Evidence based" badge, the replacement-probe button and its
  notes were unreadable on dark; the topbar overflowed a 375 px phone; small print set at 6–8 px now sits at
  10–11 px; a lone direction no longer leaves two empty columns.
- **Checked end to end against live Qloo on the judging profile**, with the model on. Found and fixed:
  - The model analysis failed whenever the model named a direction instead of giving its id, or wrote an
    over-long field. Rows are now matched to the direction by id or exact name, and prose is cut back to its
    last sentence (`EvidenceAnalysisOutput.tame`); a missing direction or an unknown citation still fails.
  - Investigate called the original anchor "the alternative anchor this direction was last tested against".
    Only a counterfactual anchor is named as one now.
  - The landing example card said Brooklyn while it ran the Tokyo bakery brief; it now names the brief it runs.
  - A reload forgot the exploration on screen. The studio reopens the last one this browser holds.
  - "Curiosity isconnecting the dots" lost its space when the partial answer hid the line break; icons sat on
    the text of the audience and location fields; the More menu stayed open after a choice.
  - An answer with no direction said "0 directions. Assumptions to test." and still offered the evidence
    test; it now says why, with ways forward, and offers only what can run.
  - After a scenario re-research the studio stayed on the old section; it opens on the new brief.
  - Same-named Qloo tags in the audience comparison are told apart by their family.
- **Every prepared brief now supports a direction.** Four returned none from Qloo (vinyl in Chicago, slow
  fashion in Los Angeles, a local stay in Lisbon, ceramics in Tokyo). They are replaced by a jazz club in
  Chicago, a clothing boutique for streetwear fans in Los Angeles, a boutique hotel in Lisbon and an
  independent bookshop in London, each researched once live and shipped in the pack with its agent report
  and evidence test.
- **README screenshots retaken from the live run**, including the agent workspace mid-run, the model analysis
  and an alternative anchor turning a contested verdict into a supported one.

## Unreleased — live-run hardening, 2026-10-23

Every item below was found by running a real brief against Qloo and the configured model, and each has a test that fails without the fix.

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
- **The demo pack now ships the model's names and the agent reports** (`export_demo_pack.py --with-agent`), so
  a fresh host opens the three featured demos in ~1 s with no Qloo and no model request.
- The picker offers only the three featured demos; the eight weaker prepared briefs stay in the JSON for
  prewarming. The Create form says what kind of idea works and how long a new one takes. The guided tour gains
  a step for the Qloo-contribution strip.

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
