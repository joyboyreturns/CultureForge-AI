# CultureForge implementation and judging review

Verified on 22 October 2026. Starting checkout and remote `main` were both
`141b33372dd798c3ec920567b70d39da9daf1290`; the working tree was clean.
Implementation commits are listed in the final chat and Git history. This is
an engineering assessment, not a guarantee of competition placement.

The relevance/composition change is `ba94f88`; the research/graph/reliability
change is `b2b7331`. The following export-and-documentation commit contains
this review, evidence artifacts and the continuation prompt. The three
implementation commits through `026f3d1` were pushed to `origin/main` on
22 October 2026 at the owner's explicit request. Release verification still
has three unresolved external/owner gates; pushing code does not resolve
deployment or attestations. A portable Git bundle is supplied separately.

## Priority audit and improvements

| Losing risk | Judging impact / implementation risk | Implemented response |
| --- | --- | --- |
| Museums and hotels becoming bakery anchors | Critical / moderate | Separate business-idea input, exact returned category-tag resolution, documented Qloo category filter, inspectable relevance decisions. Indirect evidence stays visible and cannot anchor a direction. |
| Generic recipes and unjustified model preferences | Critical / moderate | Removed broad-business-category recipe fallback and artisan/premium/culture triggers for design-led. Added collection and craft-discovery bakery hypotheses. Query seeds are not measured preferences; comparison guard withholds a model winner without a completed comparison. |
| Long blank wait and decorative progress | High / low | Publish deterministic `partialResult` before bridge/naming/controller work, with measured milestone timings. Removed timer-driven completion and synthetic percentage. Reconnect/reload the same process's run. |
| A challenge or removal that always appears positive/consequential | High / moderate | Policy anchor-fit-5 requires a usable ranking sample, filters duplicate/unrequested rank rows, and exposes per-check completion. Removal excludes optional naming differences, preserves confirmed seeds and earlier removals, and clears stale agent claims and metadata. |
| Unexecuted production build and PDF assumptions | Critical / moderate | Built and ran the container on Ubuntu 24.04.4. Actual PDF rendering exposed a CJK-only-font blank-page bug; Latin primary plus CJK fallback fixes it. |

The changes reuse the existing bounded controller, cache, polling, removal,
verdict and export paths. No additional paid service or model provider was
introduced. Existing Vercel-only transport and budgets remain in place. The
local environment was already in `judging`; validation did not switch profiles
or raise limits. Subsequent browser/HTTP/container checks disabled live Qloo
and model calls.

## Recommendation quality

The initial live category-label attempt returned `needs_input` in 2.129 s:
“Bakery” matched several Qloo tag families. This was recorded as a failure,
not a positive result. A separate bounded tag lookup returned real taxonomy
IDs. The final query used the returned cuisine category ID, with audience
signals and the same Tokyo location, through the existing cache and quota
path. No undocumented query fields were added.

The real response contains ten places, of which six pass the text relevance
rule, including Garden House Crafts Daikanyama, Sawamura Bakery & Restaurant,
The Little BAKERY Tokyo and City Bakery. Four references remain indirect.
The final two proposals differ in customer occasion and offer:

- **Morning collection:** a focused takeaway/preorder hypothesis for the
  commuters described by the founder. Takeaway references are returned;
  preordering, opening hours, access and demand remain unverified.
- **Craft discovery:** a small bread range with a proposed visible process
  and tasting. Bakery references are returned; demonstration appeal remains
  unverified.

Both name their references and audience seeds. A generic design-led third
proposal is no longer padded into the bakery answer. Bridge entities remain
available in the audience panel, without automatic links to every direction.

All eight earlier recipes were audited: independent-craft, slow-ritual,
design-led, community-table, live-programme, everyday-value, experience-led
and quiet-hub remain conditional on matching query tags and category-relevant
references. Their offering/ritual text remains a proposal, not a Qloo factual
claim. Other sectors still need richer composition and field validation.

Additional authentic held-data journeys: Brooklyn food/design returns one
direction; a Brooklyn record-shop audience and a Brooklyn wellness audience
abstain because the returned sample lacks relevant references. An uncached
London brief with live retrieval disabled returns a stated recovery error.
These were actual held Qloo responses, not mock-provider output. Unit-policy
fixtures are separately synthetic and cannot reach external services.

## Measured performance and its limits

| Journey | First evidence / concept | Completion | Conditions |
| --- | --- | --- | --- |
| Previous Tokyo journey | Not independently measured | ~286 s reported by the user | Original run, not a controlled baseline benchmark |
| Category-filtered live request | Milestones not separately instrumented on this direct route | 11.102 s | One new Qloo recommendation workflow, held seeds/bridges, real Vercel naming; preliminary three-proposal build before removal of the generic design trigger |
| Bounded research validation | 8 / 10 ms | 40.267 s | Held evidence, two-step controller ceiling, real naming and two controller/model requests; zero new Qloo requests |
| Final real-model observation | 6 / 8 ms | 62.284 s | Held evidence, two-step ceiling, three model requests including one malformed-output retry; zero new Qloo requests |

The default production controller still allows up to eight steps. The final
recorded model response was revalidated under agent-loop-3 without another API
call: four cited statements remain, one unsupported comparative statement was
withheld, and the comparative winner became null. Original statements,
execution timestamps and durations are retained in separately named source
files. This is explicitly post-response validation, not a newly executed run.

These measurements prove early delivery and authentic replay, not a claimed
speedup for arbitrary cold briefs. Fresh seeds, category resolution, Qloo
latency, model pacing and retries can still make complete analysis take minutes.

## First 15, 30 and 90 seconds

At 15 seconds, the headline explains an idea that must answer to evidence,
with a business-brief action and an explicit Qloo/source distinction. At
30 seconds, the recorded replay opens immediately with acquisition time and
composer version; a live journey shows only operations actually completed.
Once retrieval finishes, the initial graph is usable while optional work
continues. By 90 seconds on the recorded path, a judge can inspect a source,
see its relevance reasons and run removal/recomposition using held evidence.
No equivalent cold-run timing is promised.

Browser verification exercised actual source selection and all ten one-place
removals. Morning collection: **7 unchanged, 2 source-only changes, 1 answer
change**. Craft direction: **6 unchanged, 2 source-only changes, 2 answer
changes**. Applying removal of The Little BAKERY rebuilt descriptions,
photographs, anchors and citations; stale model claims disappeared. Optional
names/taglines are excluded from dependence comparisons. Keyboard focus,
Escape dismissal and narrow-window scrolling were exercised. Full mobile
and multiple-browser coverage remain incomplete.

## Verification record

See the logs and authentic results in `artifacts/validation/`.

- macOS backend: **288 tests pass, 81% coverage** (`pytest.log`).
- Frontend: TypeScript/Vite build, ESLint and unit checks pass.
- HTTP contracts pass; walkthrough **61/61** and endpoints **71/71** pass.
- Production image built and booted in an isolated Docker VM running
  **Ubuntu 24.04.4 LTS**; the application image uses Debian Bookworm and
  Python 3.12. The packaged Qloo harness imports successfully.
- Container smoke passes with actual held evidence and zero new API calls.
  This was repeated in a clean final production image, without development
  test tools installed: image
  `sha256:75cb5d3a0f6600b7c97571abe90236d77dc053cdfe7e496540c18e09d4d27c12`.
- Container suite uses the repository's development dependencies, public
  source/document fixtures and writable temporary coverage output:
  **288 tests pass, 81% coverage** (`docker-pytest.log`). These test tools
  are not installed in the production image.
- The first actual Linux Unicode render exposed nearly blank Latin text
  with the Droid CJK-only font. DejaVu primary plus Droid fallback now renders
  readable English and 東京 together on all four visually inspected pages.
- No hosted Render deployment or public URL has been verified. Release
  eligibility and asset-rights confirmations remain the owner's attestations.
- Dependency audit reports **9 development-tool advisories: 6 high and
  3 moderate**, with no critical advisories (`npm-audit.json`). These remain
  unresolved; suggested fixes include major Tailwind/Vite upgrades and need
  a separate compatibility review. The runtime image serves compiled static
  assets without these frontend development dependencies. This does not
  establish that every runtime dependency is vulnerability-free.

## Verified competition and comparison

The [official rules](https://qloo.devpost.com/rules) give four equally weighted
criteria, **25% each**: Technological Implementation, Design, Potential Impact
and Quality of the Idea. Submission closes **30 October 2026 at 11:45 pm EDT**,
or **31 October at 9:15 am IST**. Current rules state judging November 2–5,
with winners around November 5. The [event page](https://qloo.devpost.com/)
requires a working public demo, public repository and open-source license;
a video is optional. Recheck rules before submission.

The named comparison projects are from the previous 2025 Qloo LLM Hackathon,
not verified entrants in this year's Agentic competition. The
[official earlier gallery](https://qloo-hackathon.devpost.com/project-gallery)
identifies GeoTaste as grand-prize winner and Alloy, Resonance AI and Zesty
as honorable mentions; Culturo appears without a winner label.

| Project | Verified author-described positioning | CultureForge implication |
| --- | --- | --- |
| [GeoTaste](https://devpost.com/software/geotaste-your-agentic-qloo-taste-business-consultant) | Location/business consulting and visual market exploration | A Qloo business consultant alone is not differentiated. Show evidence removal changing the actual answer. |
| [Alloy](https://devpost.com/software/axiom-2bn391) | Cultural M&A diligence, agent orchestration, chat and PDF | Agent loops and reports are established patterns. Narrow, falsifiable scope matters more than breadth. |
| [Resonance AI](https://devpost.com/software/resonance-ai-1hjbf0) | Political campaign intelligence and generated assets | A specific customer workflow strengthens impact; generated output is not validation of effectiveness. |
| [Zesty](https://devpost.com/software/zesty) | Taste onboarding and contrasting recommendations/challenges | A memorable interaction is stronger than another dashboard panel. |
| [Culturo](https://devpost.com/software/culturo-5quxkb) | Broad cultural discovery; submission warns of backend warm-up | Credible replay and progressive results address practical judging friction. |

Submission descriptions, available README material and directory listings
were inspected. Actual implementation-file retrieval failed for these
competitors; none is claimed source-audited or live-tested. Marketing claims
about effectiveness, financial-grade scoring or exact benefits were not
independently validated.

Qloo category filters and tag operators are documented in the primary
[Insights API reference](https://github.com/qloo/docs-public/blob/main/reference/insights-api-deep-dive.md).
The installed official harness source was inspected for `include_tags`
resolution and `filter.tags`; actual live output confirmed the request.

## Remaining weaknesses, ranked

1. **Public demo and submission eligibility remain outstanding.** Render's
   configured persistent-disk plan is paid; no new service was purchased or
   deployed. `submission.json` contains no public URL and owner confirmations
   remain false. Code/build success does not satisfy this gate.
2. **Recommendation relevance is still heuristic.** Recognized categories,
   exact labels and source descriptions can miss nuance. Geographic text
   checks do not measure proximity, opening hours or commercial demand.
3. **Citation validation is not full semantic entailment.** The comparison
   guard fixes the observed winner error, but cannot prove every interpretation.
4. **Arbitrary cold journeys can still take minutes or hit Qloo limits.**
   Only one prepared brief was fully held locally at final smoke; inspect and
   deliberately prewarm selected scenarios before judging.
5. **In-flight jobs are single-process memory.** Browser reload can resume;
   process restarts cannot. No server-side cancellation or multi-instance job
   store was introduced. Mobile and browser-matrix validation are incomplete.
6. **Development dependency advisories remain.** Upgrade the affected build
   tooling in a separate tested change before treating the dependency audit
   as a passing release gate.

Before public submission: provision approved hosting, retain its persistent
disk, configure server-only secrets, deliberately prewarm a selected brief,
verify the public URL in a private browser, record it in `submission.json`,
and complete the owner's eligibility/asset-rights review. Do not treat those
external actions as already complete.


## Business intent and tag resolution: what is proven and what is not

**Proven offline (scripted Qloo, `backend/tests/test_intent.py`, `test_research.py`):** hybrids keep both
businesses; specialisations are carried and disclosed; a specific phrase falls back to at most one broader
search string and says so; no matching tag is `UNSUPPORTED_CATEGORY` and never a substitution; provider
failures (429, timeout, 401, malformed) are never read as an unsupported category and never cached; a
verified-empty `recommend` expires on its own TTL; identical concurrent requests make one upstream call; the
model reading is validated, one call at most, and cannot name a tag.

**Proven with real held evidence (artifacts):** `artifacts/validation/bakery-tag-resolution.json` is a real
`find_tags("bakery")` answer; it contains no `category:place:bakery` row, so a bakery brief resolves through a
`cuisine`/`industry` family tag. Three prepared briefs (Tokyo bakery, Paris ice cream, Melbourne coffee)
replay from the evidence store at zero upstream requests after this change, so their cache keys are unchanged.

**Not proven (needs live Qloo; predictions only):**

| Question | Smallest live check | Requests |
|---|---|---|
| Does `find_tags("bubble tea shop")` return a tag that places carry? | 1 `find_tags`, then 1 `recommend` for Los Angeles | 2 |
| Does `find_tags("vintage sneaker store")` / `"sneaker store"` return any matching tag? | 2 `find_tags` | 2 |
| Does `find_tags("board game café")` match, or does `arcade` carry the fallback? | 1–2 `find_tags` | 1–2 |
| Do `bookstore` and `coworking space` resolve to tags places carry in Paris / a second city? | 2 `find_tags`, 2 `recommend` | 4 |
| Does a hybrid cost the stated budget (<= 2 extra workflows)? | one cold Paris "bakery and bookstore" brief, counting `transportRequests` | about 5 |

About 14 requests in total; stop on the first sustained 429 (the key has answered 429 for more than ten minutes
after about seven workflows in 90 seconds). None of these were run for this change, so none of the Qloo
behaviours in the table is claimed.

**UI checks run:** the studio was driven in the in-app browser against a throwaway synthetic Qloo (every place
named SYNTHETIC, no network, scratch cache) to exercise the hybrid panel, the unsupported-category and
category-without-places clarification cards, the typed rate-limit failure and its working Try again, and a
375px viewport (no horizontal overflow). That shows the UI states render and their buttons work; it is not
evidence about Qloo.
