# Changelog

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
