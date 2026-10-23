# Judge scenario verification — 23 October 2026

## First-evidence experience: London

A fresh vegan-restaurant brief in London returned its initial evidence and
rule-composed direction in about **11 seconds** (initial composition recorded
at 10.19 seconds). Full research completed in **109.2 seconds** with ten places
and one cited direction. The initial view now opens automatically while the
remaining research continues. A floating card shows actual progress, and a
reader still viewing that preview receives the completed report automatically.
Readers who move elsewhere receive an offer to open the finished report.
These are measured timings for one brief, not a guarantee for arbitrary inputs.
Record: `artifacts/validation/judge-london-plant-based.json`.

## Follow-up: Berlin failure isolated and shared method corrected

The original city parameter selected an audience-location signal rather than
constraining the location of returned places. The installed official Qloo
harness explicitly distinguishes `signal_location` from `filter_location`.
Using the same three observed audience tags, restaurant category tag, result
count and intersection operators, changing only that location role made the
Berlin request return ten places in **8.75 seconds**, after two original
signal-location requests had timed out at about 60 seconds.

The fresh-query builder now uses `filter_location`. This applies to primary
briefs, hybrid secondary businesses and agent place recommendations. Raw
replacement searches use `filter.location.query`, with policy
`replacement-probe-2`. Demographic ranking retains its audience-location
signal, which is intentional and separately disclosed.

Old successful evidence remains under its original cache key and provenance;
it is never copied under the corrected query key. Modern held responses take
precedence. Old empty responses cannot prevent the corrected search. The
known-location recovery lookup understands both query forms.

| Follow-up | Actual result |
| --- | --- |
| Berlin corrected retrieval | Ten places, 8.75 seconds, one fresh request |
| Berlin complete research | One cited direction, ten places, complete in ~135.5 seconds; initial answer at ~1 second from the now-held corrected response |
| Berlin evidence test | HTTP 200, unproven; general restaurant references do not establish the vegan specialisation |
| Vienna, same audience/category and shared method | Ten places in ~6 seconds; serving-app composition produced one direction |
| Helsinki independent bookshop | Returned no places, rather than timing out; recorded as an evidence coverage limitation, not a universal success claim |
| Original 11 demos after the shared fix | Passed again, including removal, verdicts and PDF responses, zero upstream requests |
| Regression suite | 444 passed; build, lint and frontend unit checks pass |

The timing comparison establishes that the corrected method worked for these
requests. It does not establish Qloo's internal reason for the original stall
or guarantee an answer for every future city, category or upstream outage.

The trial library now contains **14** briefs: the original 11 plus Berlin,
Mexico City and Vienna. Overview and result screens expose the full library
with category filters; the creation form offers a scrollable extended list.
All 14 have packaged real Qloo evidence and acquisition times. Final replay verified all 14, including cited-place removal, verdicts and PDF responses, with zero upstream requests; the full HTTP walkthrough passed 61 checks. Plant-based
and hybrid examples include explicit scope notes. Failed responses are not
packaged as successful answers.

Records: `berlin-location-filter.json`, `judge-berlin-fixed.json`,
`vienna-location-filter.json`, `vienna-fixed-result.json` and
`helsinki-bookshop-fixed.json` under `artifacts/validation/`.

The following sections preserve the earlier observations that led to this fix.

Testing used the existing judging profile. Fresh Qloo calls were deliberate,
one brief at a time; no limits were raised and no provider was substituted.

## Prepared evidence, all five business types

`python3 scripts/judge_replay.py` ran against an isolated judging server with
Qloo, models and geocoding disabled. All 11 prepared ideas returned directions,
valid citations, scoped verdicts and PDF responses. Removing a cited place
removed its entity and left only resolvable citations. Four malformed inputs
were rejected. The replay spent zero upstream requests.

| Category | Ideas tested | Directions per idea | Verdicts observed |
| --- | --- | --- | --- |
| Food & beverage | Brooklyn, Seattle, Tokyo, Paris, Melbourne | 1–2 | Contested and unproven |
| Wellness | London | 1 | Supported |
| Entertainment | Chicago, Austin | 1 | Unproven |
| Retail | Los Angeles, London | 1 | Unproven |
| Hospitality | Lisbon | 2 | Supported and unproven |

PDF verification here checked successful HTTP delivery and the PDF signature;
it did not inspect every rendered page. Detailed replay results are in
`artifacts/validation/judge-replay.json`.

## Fresh inputs on the live judging server

| Input | Result | Observation |
| --- | --- | --- |
| Vegan restaurant; design-conscious plant-based diners; Berlin | Recoverable provider timeout at ~64 seconds | Audience/category resolution worked; places did not arrive. No fabricated result. Initial run recorded one successful request; global accounting also counted the timed-out attempt. |
| Bookshop café; translated-fiction readers and natural-wine enthusiasts; Mexico City | Complete: one direction, ten returned places | Initial direction in ~7 seconds; complete in ~119 seconds, eight reported upstream requests. Hybrid components were researched separately. Unsupported comparative analysis was rejected. |
| Film camera shop; film-photography hobbyists; Singapore | Clarification in ~3 seconds | No matching category tag; offered broader “camera shop”. One upstream request; no substituted business or invented places. |

One deliberate Berlin retry reused its held audience and category responses,
but its places request timed out again at ~62 seconds. No further retries
were attempted. The fixed probe correctly exited with failure. Across the
three fresh inputs plus this retry, the global Qloo ledger moved from 241 to
253 attempted calls: 12 in total, including the two timed-out attempts. The
per-run successful-request totals exclude those failed attempts; do not
interpret them as the full upstream-attempt count on failure paths.

These outcomes establish one successful fresh research path, an unsupported
category recovery path and a provider failure path. They do not establish
universal coverage or reliable cold latency for all ideas and cities.

## Defects fixed

- Whitespace-only audience and city values previously passed minimum-length
  validation. Project and research inputs now strip padding before validation.
  The browser explains what to enter and focuses the field; the API rejects
  blanks before provider access.
- An audience clarification had no dedicated edit button. It now focuses the
  target-audience field, matching the location and business-idea recovery paths.
- The live hybrid agent repeatedly attempted invalid audience comparisons.
  Comparison feedback now explicitly requires observed place entity IDs and
  refuses tag URNs. Three consecutive rejected plans stop further planning,
  retaining existing evidence and allowing a cited final analysis. A valid
  action resets that streak. Existing successful held reports remain usable.
- The one-brief probe exited successfully even when a run failed. It now
  returns a failing exit code for failed/incomplete runs and failed challenges;
  a stated clarification remains a valid handled outcome.

The new agent guard is covered by deterministic tests; no claim is made that
it has already improved measured live latency. The Mexico City observation
above was recorded before that guard was installed.

## Final checks

- Backend: 437 tests passed, including blank-input rejection, agent early
  stopping, streak reset and actionable comparison rejection.
- Frontend unit checks passed. Production build and ESLint passed.
- The local server was restarted on the same testing address with judging and
  live Qloo still enabled. HTTP checks confirmed three whitespace cases return
  422 and spend no Qloo request.
- Browser verification confirmed the final blank-audience message and focus
  on the audience field before a request starts. Evidence is saved in
  `artifacts/validation/judge-input-validation.png`.
- Existing FastAPI startup deprecation and map bundle warnings remain.

The robust outcome for sparse or unsupported ideas is a clear limitation and
a next step, not a guaranteed direction. Prepared examples remain the first
demo path when a fresh upstream request cannot complete.
