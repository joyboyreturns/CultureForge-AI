# Evidence policy: anchor-fit-4

CultureForge's evidence test (`POST /api/projects/challenge`, implemented in
[`backend/challenge.py`](../backend/challenge.py)) gives each business direction
one of three verdicts: **supported**, **contested** or **unproven**. This page
is the rule that produces them. The policy version is returned with every
result (`policyVersion`), and it changes whenever the rule or its wording does.

## What it is about

Each verdict is about **anchor fit within the retrieved sample**: the place
a direction is built around (its *anchor*) and how it sits among the other
places Qloo returned for the same brief. It is **not demand**, competition,
rent, footfall, profitability or willingness to pay. Nothing in this policy
measures any of those, and no result should be read as if it did.

The policy produces **no score**. Every number it reports is a rank position,
a count of places or tags, or a value Qloo returned.

## Inputs

| Input | Source | Notes |
| --- | --- | --- |
| Retrieved places | `recommend` for the brief's audience tags and location, at most 10 (`BRIEF_PLACE_LIMIT`) | Ten is the most Qloo's `rank` and `compare_audiences` accept in one list. |
| Anchor | The first place the direction cites | Can be changed in the UI. The concept is then *not* rebuilt, and the screen says so. |
| Demographic profile | Proposed by CultureForge from the brief's words, shown before the test runs, changeable | One of: gen z, millennials, young adults, women 25-34, women 35-44, men 25-34, men 35-44, seniors. When the brief names none, the default is millennials, and it is labelled as a default. Qloo converts the phrase into its own age and gender signals. |
| Rank | One `rank` call: all retrieved places, the profile, the location | It does **not** use the audience's cultural tags; Qloo's `rank` returns nothing for a location and tags alone. |
| Anchor tags | One `compare_audiences` call: the anchor against every other retrieved place, cited or not | A tag counts as *cultural* by its Qloo family (cuisine, ambience, good_for, activities, interests, lifestyle and others). Type and operational families (genre, category, service_type, amenities…) and any family the policy does not know do not count. |

## The rule

Let `n` be the number of places Qloo ranked and `p` the anchor's position (1 is first).

1. **Minimum sample.** If fewer than `MINIMUM_VENUES = 3` places were
   retrieved, there is no verdict. The result is *unproven*, with confidence
   `none`.
2. **Rank check.** Let `k = max(1, total // 3)` with `total = n`.
   - `p ≤ k`: **pass** (top band)
   - `p > n − k`: **fail** (bottom band)
   - otherwise: **mixed**

   With 3 to 5 places this is first passes and last fails, which is what
   anchor-fit-3 did. With 10 places it is positions 1–3 and 8–10.
3. **Tag check.** **Pass** if Qloo returned at least one qualifying cultural
   tag for the anchor in the comparison, otherwise **mixed**. A tag absent
   from the response is never treated as proof the other places lack it,
   because the response is a bounded list. A tag returned for both sides is
   never called exclusive.
4. **Verdict.**
   - **contested** if the rank check fails
   - **supported** only if the rank check and the tag check both pass
   - **unproven** otherwise. One passing check and one missing check is half an answer.

## Confidence

| Label | When |
| --- | --- |
| `none` | Fewer than 3 places were ranked. |
| `low` | Fewer than 6 places were ranked (`MODERATE_SAMPLE`), **or** removing any single other place changes the rank check (see below). |
| `moderate` | 6 or more places were ranked and no single removal changes the rank check. |

There is no `high`. The sample is at most ten places, ranked against one demographic profile.

## Sensitivity

Both checks below are computed from the **same ranking**, with no new Qloo request:

- **leave-one-out.** Each other ranked place is removed in turn, and the rank
  rule is re-applied to the anchor's new position among `n − 1`. The result
  lists every removal that changes the rank check. If any does, confidence
  is `low`.
- **Alternative anchors.** The rank rule is applied to every other ranked
  place as if it were the anchor. This previews how the claim would fare
  with a different reference. Only the rank check is recomputed; the tag
  check needs its own comparison, which the *test against another place*
  action runs.

Each direction returns this as `index`:
`rankCheck`, `tagCheck`, `qualifyingTags`, `sampleSize`, `minimumSample`,
`confidence`, `confidenceReason` and `sensitivity` (`stable`,
`changesWhenRemoved`, `alternativeAnchors`).

## Limits

- The profile is a demographic phrase CultureForge proposed, not the
  audience's cultural profile, and not something Qloo inferred.
- The ranking and the comparison are Qloo's aggregate signals for the
  retrieved places. They are not observations of a market.
- A verdict can change when the anchor, the profile, the location or the
  retrieved sample changes. That sensitivity is the point of showing it.
- *Supported* means the two checks that could be run passed within this
  sample. It is a reason to run a field test, not a substitute for one.
