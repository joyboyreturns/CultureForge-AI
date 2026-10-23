# Live run matrix, 23 October 2026

Real Qloo (hackathon host, judging profile) and the configured model (`minimax/minimax-m3.1-flash` through the
Vercel AI Gateway), one brief at a time through the studio's research-run path
(`scripts/brief_probe.py`). No mock provider, no raised limits. The server's evidence store already held
the earlier prepared briefs, so some rows are replays; the cost column is what the *run* spent.

"Requests" are upstream Qloo requests reported by the run. "Model" is the agent loop's own requests
(planning steps plus up to two analysis attempts), not naming or idea-reading requests. The Qloo counter on
`/api/health` moved from 85 to 164 over the whole session (it counts workflow calls, including the failed
and repeated runs below).

## What was run

| # | Brief (business · idea · audience · city) | Outcome | Time | Requests / model | What it showed |
|---|---|---|---|---|---|
| 1 | Food & beverage · Artisan bakery · morning commuters · **Tokyo** (prepared, held) | Replay: 2 directions | **1.0 s** | 0 / 0 | The held agent report was a lone `LIVE_DISABLED` step from an offline validation run (defect, fixed). |
| 1b | same, after the fix | 2 directions; evidence test: *contested* + *unproven* | 89 s | 6 / 9 | 8 agent steps (3 refused or skipped, labelled), 8 cited claims. Partial answer at 1 s. |
| 2 | Food & beverage · Ice cream parlour · **Paris** (prepared, held) | 1 direction; *unproven* | 143 s, then 117 s | 7 / 10, then 2 / 9 | First run: analysis failed twice (summary > 800 characters), rules answer stood and said so. Second run passed. |
| 3 | Food & beverage · Specialty coffee shop · **Melbourne** (prepared, held) | 1 direction; *unproven* | 147 s, then 154 s | 7 / 10, then 3 / 10 | Same analysis failure on the first run; second passed after one invalid attempt. |
| 4 | Food & beverage · *no idea* · Brooklyn (prepared, "more briefs") | 1 direction anchored on a comedy and pizza venue | 132 s, then 132 s | 6 / 10 each | Place list included Manhattan's Union Square Park and the Whitney. **Not fixed**: see limits. |
| 5 | Wellness · **bouldering gym** (unfamiliar) · beginner climbers · **Denver** | Before: 0 directions after 124 s and 11 requests. After: 0 directions in **1 s**, 0 requests | 124 s → 1 s | 11 / 9 → 0 / 0 | Qloo resolved "Bouldering Gym" exactly but returned a **Chicago** gym and Denver parks. Correctly refused; now names the place and its city. The agent no longer runs on an empty answer. |
| 6 | Retail · **bookshop cafe** (hybrid) · translated fiction + natural wine · **Mexico City** | Before: **0 directions** though 4 relevant Mexico City bookshops were returned. After: 1 direction, *unproven* | 135 s → 111 s | 11 / 9 → 6 / 9 | Real relevance failure: the model-read category carried only the typed word. Fixed. 6 of the 10 returned places were in other cities (Morelia, New York, Montevideo, Guatemala, Buenos Aires, The Hague) and were correctly kept out of the anchors. |
| 7 | Food & beverage · **tea house** (sparse) · slow-living tea drinkers · **Boise** | Before: 2 directions anchored on **Dutch Bros** (drive-thru coffee) → *contested* and *unproven*. After: 1 direction anchored on Boise Boba | 130 s; recompose from held evidence 0.1 s | 13 / 9; 0 | Six of ten places were one chain; a Portland garden and a Portland café were also returned. The agent itself noticed the contradiction and removed the anchor. Menu-word matches no longer count as a tea house. |
| 8 | Retail · **film camera shop** (unsupported) · hobbyists · **Singapore** | Clarification `UNSUPPORTED_CATEGORY` | **5.1 s** | 2 / 0 | Qloo had no matching tag; nothing substituted. Previously offered no way out; now offers "camera shop". |

The brief "a place for people to hang out" (no category) was not run live; the rules ask for the main
business before spending a request, as the unit tests pin.

## Cold versus held

| Path | First useful content | Complete |
|---|---|---|
| Held prepared demo, agent report held | ~1 s (executive brief, map, evidence) | ~1 s |
| Held evidence, agent report not held | ~1 s (initial directions, openable at once) | 90–155 s (model pacing: 5 requests a minute) |
| Cold brief, directions supported | 6–8 s (first Qloo evidence and an openable initial answer) | 110–135 s |
| Cold brief, nothing supported | 6–8 s | ~21 s observed before the change up to the composition step, and the agent is now skipped (was 124–135 s in total) |
| Unsupported category | 5 s | 5 s |
| Evidence test (held ranking) | 0–3 s | 7–9 s when it makes one live ranking |
| PDF | n/a | 0.5 s, 5 pages |
| Venue geocoding (Nominatim, cold) | n/a | 6 s for 4 venues; held after |

## Where the answer differs from a generic model's

These are observations from the runs above, not a controlled comparison with another model.

- **It named real places in the right city and could say when there were none.** Denver and Boise show Qloo's
  own filter returning other cities and chains; the system refused to build on them and said why. A model
  that never retrieves places has nothing to refuse.
- **It argued with itself.** In Boise the agent, using the returned entity tags, judged that both directions
  rested on a loud drive-thru chain, removed the anchor and recomposed. The evidence test then returned
  *contested* for the lead direction. The verdict is scoped to anchor fit within the retrieved sample.
- **It could be wrong in a way you can see.** Of seven directions that reached the evidence test, five were
  *unproven* and two *contested*; none was *supported*.

## Observed defects and what changed

See [CHANGELOG.md](../CHANGELOG.md). Each has a test that fails without its fix.

## Not run, and why

- No stress test of many cold briefs: each costs about nine Qloo requests and Qloo's limit is unpublished.
  The fair-use guard is covered by tests and by eight concurrent held requests, not by a real cold flood.
- Qloo rate limiting and the model's 429 were not provoked live. Their handling is covered by the existing
  tests (`RATE_LIMITED` stops the loop, is never held, and the cool-down serves held evidence).
- Map tiles from OpenFreeMap were not taken offline in this session; the fallback to the grid is covered by
  the unit check.
