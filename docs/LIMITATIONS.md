# Limitations and non-claims

## What the product does not claim

- **No demand, revenue, footfall, rent, competition or willingness to pay.**
  Qloo affinity and popularity describe cultural association, and every
  verdict is scoped to *anchor fit within the retrieved sample*.
- **No invented numbers.** Every number on screen is one Qloo returned, or a
  count or position of what it returned. The model may not state numbers;
  claims and answers that do are withheld.
- **No customer validation.** No traction, conversion or competitive
  advantage has been measured. [BUSINESS.md](BUSINESS.md) lists the
  commercial case as assumptions.
- **Not a validated business plan.** A *supported* direction passed the
  checks that could be run, within the sample. It is a reason to run a field
  test.

## Limits of the evidence

- **Small samples.** At most ten places per brief, because Qloo's `rank` and
  `compare_audiences` accept at most ten entities per list. The confidence
  label is never higher than *moderate*.
- **One demographic profile.** The evidence test ranks against a
  demographic phrase proposed by CultureForge (shown and changeable), not
  against the audience's cultural tags, because `rank` returns nothing for a
  location and tags alone. The profile is not inferred by Qloo.
- **Absence is not proof.** A tag missing from a bounded comparison
  response does not show that other places lack it, and no tag is called
  exclusive.
- **Locations are queries.** A returned place answered a location query.
  Its own location is shown as Qloo returned it, and is not verified.
  Neighbourhood-level locations (for example "Greenpoint, Brooklyn") have
  returned no places in testing; city-level ones work better.
- **Interest cells are not venues.** The map shows where affinity for a
  place is strong. Qloo gives places addresses, not coordinates, so places
  are never plotted.
- **The audience bridge has no location.** Artists, films and brands are
  returned for the audience tags alone, and are cited as audience-level,
  not direction-specific.

## Limits of the model layer

- It is optional, and off by default. With it off, the rule composer
  answers, the agent card says so, and *Ask the evidence* returns a stated
  503.
- **The model gateway route in use allows 5 requests a minute** for this
  team (observed on 22 October 2026 from its `X-Ratelimit-Limit-Requests`
  header). Requests are paced to it (`LLM_REQUESTS_PER_MINUTE`) and a 429 is
  waited out once, so the agent loop (up to ten requests) takes a few minutes
  and *Ask the evidence* takes tens of seconds, and several people using the
  model features at once share that rate. A route with a higher limit is the
  fix.
- The agent loop is bounded: eight steps and the run deadline in every
  profile. In dev it is also bounded by the run's Qloo allowance and the
  daily analysis allowance (10), so a single cold run can use most of a
  day's dev model allowance.
- The validator checks that every citation was observed and that no number
  is stated. It cannot check that a claim's reasoning is sound. The cited
  IDs are shown so a reader can check that.

## Limits of the deployment

- One process and one instance. Research runs and in-flight
  de-duplication are held in memory; the call ledgers and held evidence are
  durable.
- Removing the local budgets (`RUN_PROFILE=judging`) does not remove Qloo's
  own quota, which is unpublished. Prewarming and the kill switch are the
  mitigations.
- **Observed, not confirmed:** on 22 October 2026, after about seven workflow
  calls in roughly ninety seconds (a cold "bakery in Tokyo" brief), the
  hackathon key answered `429` on `rank` and kept doing so for more than ten
  minutes, while `find_tags` still worked. A cold brief costs about nine
  workflows (seeds, places, three bridge domains, and the evidence test's
  `rank` and three comparisons, plus any the agent chooses). So a judge's
  first click on a brief that is not held can meet a stated rate-limit message,
  and the prepared, held briefs are the dependable path.
- **Also observed:** Qloo answered `QLOO_RATE_LIMIT` to one specific
  comparison (the anchor "The Ritz-Carlton, Tokyo" against the other nine
  places) on every attempt over about an hour, including a direct call, while
  a comparison for another anchor and other workflows succeeded. That looks
  request-specific, not a key-wide limit, so one such answer does not pause
  other requests (two in a row do, for 60 seconds). The evidence test then
  shows that direction's tag check as "could not be run", and the direction as
  unproven, with Qloo's code.
- Held evidence expires (24 hours in dev, 30 days in judging), after which a
  brief is fetched again.
- PDF font coverage is bounded by installed fonts. The Docker image installs DejaVu for Latin and Droid as a CJK fallback; Ubuntu-hosted container rendering was checked with English and 東京 together. A CJK font that lacks Latin glyphs is never used as the sole font. Unsupported characters still require an appropriate font.
- Reference relevance is a conservative text rule, not a calibrated semantic model. It can miss suitable references or misread a description. Its reasons are inspectable; geographic text matches are not a geofence.
- The eight general recipes now require matching audience tags and relevant anchors. Two bakery hypotheses distinguish collection from craft discovery. Other domains still need richer, validated composition rules; abstention can be frequent.
- A query-resolved audience tag is an interpretation of the brief, not independent preference evidence. Comparison guards withhold an unsupported winner, but citation and pattern checks do not establish general semantic entailment.
- Default controller bounds remain eight steps and the run deadline. The recorded timing experiment narrowed the controller to two steps and served held evidence; it does not establish cold-run latency for arbitrary briefs.
