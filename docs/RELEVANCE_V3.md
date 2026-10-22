# Relevance v3, outcome states, simpler results and the interest map (22 Oct 2026)

**Root cause.** Categories were a closed keyword table; only 9 families sent a Qloo category filter, question-style ideas
were not parsed, and attractions had no class of their own.

**Changes.** `backend/category.py` (19 categories, multilingual synonyms, open-vocabulary lookup, ambiguity -> unresolved);
`relevance-3` evidence classes; `backend/outcome.py` (`outcome` on the response, shown in the empty state);
agent claims labelled `inferred` by the server; MapLibre interest map (no basemap, no keys); results page simplified:
one evidence-mix bar, three primary insight tabs with "More views", secondary actions under "More".

**Verified (22 Oct 2026, RUN_PROFILE=judging).**
- `pytest -q`: 322 pass. `tsc --noEmit`, `npm run lint`, `npm run build`, `node scripts/test_unit.mjs`: pass.
- `verify_contracts.mjs`, `verify_endpoints.mjs` (71 checks), `verify_walkthrough.mjs` (61 checks, with DEV_URL set to the
  vite server): pass, run with live Qloo and the model disabled.
- Browser: evidence-mix chart, collapsed tabs, hero actions, held-only recovery message and the MapLibre map with 20 real
  Qloo interest cells all rendered; phone width (375 px) has no horizontal overflow after a topbar/hero fix.
- One live brief (Paris, ice cream): 34.5 s cold, 6 Qloo requests, 4 direct businesses, 3 other-city, 1 direction, no museums.
  One live interest-cell request (Tokyo).

**Not run.** The other nine judge scenarios against live Qloo (only deterministic text tests), Docker, a PDF render of the
new fields, screen-reader testing, other browsers, concurrent-request load, model-failure and rate-limit injection beyond
existing unit tests. The Paris run was not repeated after adding French ice-cream terms.

**Known limits.** Evidence carries no venue coordinates, so competitor and attraction layers stay empty; the map is a
latitude/longitude grid of interest cells with no streets. Text matching can misclassify (Lindt counted as ice cream).
`contested` comes from the challenge verdicts, not `outcome`. Cold runs take about 30 s or more.

**Skeptical judge view.** Strong: inspectable evidence, removal/recomposition, refusal to invent. Weak: one direction on a
cold brief, no real map of venues, features still numerous behind "More". Risk: live latency and the Qloo quota.


## Addendum (22 Oct 2026, later)
Fixed after live runs: pizza category; Qloo `specialty_dish` tags; other-city venues can no longer anchor; Qloo's `metro`
field now counts as the place (Melbourne suburbs were wrongly "another location"); place-namespaced category tags
(`category:place:…`, `genre:place:…`) are preferred because Qloo-namespace tags returned no places; two businesses in one
idea are ambiguous; "yoga cafe"-style phrases are looked up whole and match on the distinctive word; a narrow
"Local Reference Study" direction when real references exist but no recipe fits; unknown locations give a friendly
message. Not verified: Bengaluru, Berlin (Qloo timed out), the removal "unchanged/unresolved" outcomes.
