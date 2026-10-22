# Cultural Opportunity Explorer (map)

**What it is.** A real street map (OpenFreeMap vector tiles, own dark/light style, no key) with Qloo interest cells,
clustered venue pins, a direction picker, a venue panel, and "What happens without this evidence?" wired to the existing
removal/recomposition workflow.

**Data honesty.** Qloo places carry an address, not coordinates; only interest cells have coordinates. Pins come from
`POST /api/geo/venues` (`backend/geocode.py`): the returned address (cleaned of non-Latin building names) is geocoded with
OpenStreetMap Nominatim; if that fails, a name search is accepted only when the returned name matches Qloo's name, sits
inside the requested city and is point-level. Neighbourhood-level, ambiguous, other-city and not-found answers are listed
as "not plotted" with a reason. Pins are address/name matches, not surveyed points. Cells are never shown as venues.

**Cost/limits.** All free. Nominatim policy: 1 request/second, identifying User-Agent (`GEOCODING_USER_AGENT`), cached on
disk (`~/.cache/cultureforge/geocode_cache.json`, saved per venue). `GEOCODING_ENABLED=false` serves held results only.
OpenFreeMap has no key or quota but no SLA; tile failure falls back to the grid view. Alternatives: self-hosted tiles,
a paid geocoder.

**Run.** `RUN_PROFILE=judging QLOO_LIVE_ENABLED=false` backend + `npx vite --port 5179`; run a held example, open
"Interest map". Cells need one live where-popular call per place (held ones are reused).

**Verified (22 Oct 2026).** pytest 329, tsc, eslint, build, unit checks, contracts/endpoints (71)/walkthrough (61).
In the browser: Tokyo bakery (held) 9 of 10 venues placed, Paris ice cream 5 of 9 placed, clusters, panel, direction
switching, removal with a changed result and apply/undo, 375 px layout, tile-failure fallback.

**Not verified.** An "unchanged" or "unresolved" removal outcome (data never produced one), WebGL-failure and offline
states, screen readers, Bengaluru (no held brief; would need a live run), concurrent users.

**Known issues.** Some venues are classified oddly by text rules (Fuglen Asakusa as "cultural attraction"). Saved
explorations from before the address field show "no address". Audience comparison is not offered: cells are per place.

**90-second walkthrough.** (0-15 s) Open the held Tokyo bakery brief: a real street map, venues clustered, cells glowing
where Qloo reports affinity. (15-35 s) Pick "The Morning Bread Counter": its three cited venues light up, others dim, the
side panel says which are direct matches. (35-55 s) Click a pin: why it matters, what is missing, which directions cite it.
(55-80 s) "What happens without this evidence?": the answer rebuilds from held evidence, changed/unchanged shown per
direction, no new Qloo request; Undo. (80-90 s) Note the honest bits: one venue not plotted and why.
