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
- Held evidence expires (24 hours in dev, 14 days in judging), after which a
  brief is fetched again.
- The PDF's built-in fonts are Latin-1. Other characters print as "?"; the
  JSON export keeps them.
- The Qloo transport is the official harness CLI, run per request. A native
  HTTP client was not built.
- The anonymous studio is one shared demo workspace. Use non-confidential
  briefs.
