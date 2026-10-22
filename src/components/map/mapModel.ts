/**
 * The pure rules behind the Cultural Opportunity Explorer.
 *
 * Nothing here touches the DOM or MapLibre, so scripts/test_unit.mjs can pin
 * it. Two facts shape every function:
 *
 *  - Qloo interest cells (`where_popular`) are geographic cells of affinity
 *    for one entity. They are never venues.
 *  - Qloo places carry an address and no coordinate. A venue is drawn only
 *    when the server geocoded that address inside the requested city
 *    (status `plotted`), or the evidence already carries a verified
 *    coordinate. Everything else is listed, with the reason.
 */
import type { Concept, Evidence, EvidenceClass, VenueGeocode, VenueGeocodeStatus } from '../../contracts'

export type VenueKind = 'direct' | 'indirect' | 'attraction'
export type LatLon = { lat: number; lon: number }
export type Bounds = { west: number; south: number; east: number; north: number }

/** The classes a venue reference can have and still be drawn as a venue. */
export const PLOTTABLE_CLASSES: EvidenceClass[] = ['direct_business', 'indirect_business', 'cultural_attraction', 'unverified_geography']

export const CLASS_WORDS: Record<EvidenceClass, string> = {
  direct_business: 'A business like the one in the brief',
  indirect_business: 'An adjacent business (an indirect anchor)',
  cultural_attraction: 'A cultural attraction nearby in the evidence',
  audience_affinity: 'A place the audience likes, not a venue reference',
  unverified_geography: 'A business like the brief’s, location unconfirmed by Qloo',
  unrelated: 'Unrelated to this brief',
}

export const KIND_WORDS: Record<VenueKind, string> = {
  direct: 'Direct match',
  indirect: 'Indirect anchor',
  attraction: 'Cultural attraction',
}

export function kindOf(cls: EvidenceClass | null | undefined): VenueKind | null {
  if (cls === 'direct_business' || cls === 'unverified_geography') return 'direct'
  if (cls === 'indirect_business') return 'indirect'
  if (cls === 'cultural_attraction') return 'attraction'
  return null
}

export interface VenueCandidate {
  venue: Evidence
  cls: EvidenceClass | null
  kind: VenueKind | null
  /** Whether it may be sent to the geocoder at all. */
  eligible: boolean
  /** Why not, when it is not. */
  reason?: string
}

/** Every returned place, with whether it can be drawn as a venue. */
export function venueCandidates(evidence: Evidence[]): VenueCandidate[] {
  return evidence.filter((item) => item.kind === 'entity').map((venue) => {
    const cls = venue.relevance?.evidenceClass ?? null
    const kind = kindOf(cls)
    if (!cls) return { venue, cls, kind, eligible: false, reason: 'CultureForge’s relevance rule did not classify this place, so it is not drawn as a venue.' }
    if (!kind) return { venue, cls, kind, eligible: false, reason: `Classified as “${CLASS_WORDS[cls].toLowerCase()}”, so it is not drawn as a venue.` }
    return { venue, cls, kind, eligible: true }
  })
}

export function validCoordinate(value: { lat?: unknown; lon?: unknown } | null | undefined): LatLon | null {
  if (!value) return null
  const lat = typeof value.lat === 'number' ? value.lat : NaN
  const lon = typeof value.lon === 'number' ? value.lon : NaN
  if (!Number.isFinite(lat) || !Number.isFinite(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) return null
  if (lat === 0 && lon === 0) return null
  return { lat, lon }
}

const STATUSES: VenueGeocodeStatus[] = ['plotted', 'not_found', 'outside_city', 'ambiguous', 'no_address', 'unavailable']

/** Read one server answer defensively. A `plotted` answer without a usable
 *  coordinate is not plotted. */
export function normaliseGeocode(raw: unknown): VenueGeocode | null {
  if (!raw || typeof raw !== 'object') return null
  const row = raw as Record<string, unknown>
  if (typeof row.id !== 'string' || !row.id) return null
  const status = STATUSES.includes(row.status as VenueGeocodeStatus) ? row.status as VenueGeocodeStatus : 'unavailable'
  const text = (key: string) => (typeof row[key] === 'string' ? row[key] as string : null)
  if (status === 'plotted') {
    const at = validCoordinate({ lat: row.lat, lon: row.lon })
    if (!at) return { id: row.id, status: 'not_found', reason: 'The geocoder returned no usable coordinates.' }
    return { id: row.id, status, lat: at.lat, lon: at.lon, matched: text('matched'), source: text('source'), precision: text('precision'), reason: null, cached: Boolean(row.cached) }
  }
  return { id: row.id, status, reason: text('reason') ?? 'Not plotted.', cached: Boolean(row.cached) }
}

/** Whether a geocode answer is definitive and may be held for this exploration. */
export function isDefinitive(result: VenueGeocode) {
  return result.status !== 'unavailable'
}

export type Placement =
  | { state: 'plotted'; at: LatLon; source: string; precision: string; matched?: string | null }
  | { state: 'pending' }
  | { state: 'not_plotted'; status: VenueGeocodeStatus | 'not_eligible'; reason: string }

/** Where a candidate stands. */
export function placementOf(candidate: VenueCandidate, geocode: VenueGeocode | undefined): Placement {
  if (!candidate.eligible) return { state: 'not_plotted', status: 'not_eligible', reason: candidate.reason ?? 'Not a venue reference.' }
  const own = validCoordinate(candidate.venue.coordinates)
  if (own) return { state: 'plotted', at: own, source: candidate.venue.coordinates?.source || 'A verified coordinate carried by the evidence', precision: 'address match, not a surveyed venue point' }
  if (!candidate.venue.address?.trim()) return { state: 'not_plotted', status: 'no_address', reason: 'Qloo returned no address for this venue.' }
  if (!geocode) return { state: 'pending' }
  if (geocode.status === 'plotted') {
    const at = validCoordinate(geocode)
    if (at) return { state: 'plotted', at, source: geocode.source || 'Server geocode of the address Qloo returned', precision: geocode.precision || 'address match, not a surveyed venue point', matched: geocode.matched }
  }
  return { state: 'not_plotted', status: geocode.status, reason: geocode.reason || 'Not plotted.' }
}

/** The geocode requests still to make, in batches the server accepts. */
export function geocodeBatches(candidates: VenueCandidate[], city: string, held: (id: string, address: string) => boolean, size = 3) {
  const wanted = candidates
    .filter((c) => c.eligible && !validCoordinate(c.venue.coordinates) && c.venue.address?.trim())
    .filter((c) => !held(c.venue.id, c.venue.address!.trim()))
    .map((c) => ({ id: c.venue.id, address: c.venue.address!.trim(), city, name: c.venue.label }))
  const batches: typeof wanted[] = []
  for (let i = 0; i < wanted.length; i += size) batches.push(wanted.slice(i, i + size))
  return batches
}

export function geocodeKey(city: string, id: string, address: string) {
  return `${city.trim().toLowerCase()}|${id}|${address.trim().toLowerCase()}`
}

/** The entity evidence a direction cites. */
export function citedVenueIds(concept: Concept | undefined, evidence: Evidence[]): Set<string> {
  if (!concept) return new Set()
  const places = new Set(evidence.filter((item) => item.kind === 'entity').map((item) => item.id))
  return new Set(concept.evidenceIds.filter((id) => places.has(id)))
}

export function directionsCiting(venueId: string, concepts: Concept[]) {
  return concepts.filter((concept) => concept.evidenceIds.includes(venueId))
}

export interface PlottedVenue { venue: Evidence; kind: VenueKind; at: LatLon }

/** The clustered venue layer. `cited` and `dim` follow the chosen direction. */
export function venueFeatures(plotted: PlottedVenue[], cited: Set<string>, focus: boolean): GeoJSON.FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: plotted.map(({ venue, kind, at }) => ({
      type: 'Feature',
      properties: { id: venue.id, kind, label: venue.label, cited: cited.has(venue.id) ? 1 : 0, dim: focus && cited.size && !cited.has(venue.id) ? 1 : 0 },
      geometry: { type: 'Point', coordinates: [at.lon, at.lat] },
    })),
  }
}

export function pointFeatures(points: LatLon[], properties: Record<string, unknown>[] = []): GeoJSON.FeatureCollection {
  return { type: 'FeatureCollection', features: points.map((p, i) => ({ type: 'Feature', properties: properties[i] ?? {}, geometry: { type: 'Point', coordinates: [p.lon, p.lat] } })) }
}

export interface CellPoint { lat: number; lon: number; geohash?: string | null; affinity?: number | null; popularity?: number | null }

/**
 * How the cells are coloured. Affinity is the metric that matters, but
 * inside one area it is often almost identical across every cell; encoding a
 * spread under 0.005 would imply a comparison the data does not support, so
 * popularity is used instead and the legend says which.
 */
export function cellMetric(points: CellPoint[]) {
  const affinities = points.map((p) => p.affinity).filter((a): a is number => typeof a === 'number')
  const popularities = points.map((p) => p.popularity).filter((a): a is number => typeof a === 'number')
  const spread = affinities.length ? Math.max(...affinities) - Math.min(...affinities) : 0
  const useAffinity = spread > 0.005
  const values = useAffinity ? affinities : popularities
  const top = values.length ? Math.max(...values) : 1
  const bottom = values.length ? Math.min(...values) : 0
  const span = Math.max(0.0001, top - bottom)
  const of = (point: CellPoint) => (useAffinity ? point.affinity : point.popularity)
  const heat = (point: CellPoint) => { const v = of(point); return typeof v === 'number' ? (v - bottom) / span : 0 }
  const order = points.map((_, i) => i).sort((a, b) => (of(points[b]) ?? -Infinity) - (of(points[a]) ?? -Infinity))
  const rank = new Map(order.map((index, position) => [index, position + 1]))
  return { name: (useAffinity ? 'affinity' : 'popularity') as 'affinity' | 'popularity', useAffinity, of, heat, order, rank }
}

export function cellFeatures(points: CellPoint[]): GeoJSON.FeatureCollection {
  const metric = cellMetric(points)
  return pointFeatures(points, points.map((p, index) => ({ index, heat: metric.heat(p) })))
}

export function boundsOf(points: LatLon[]): Bounds | null {
  if (!points.length) return null
  const lats = points.map((p) => p.lat)
  const lons = points.map((p) => p.lon)
  return { west: Math.min(...lons), east: Math.max(...lons), south: Math.min(...lats), north: Math.max(...lats) }
}

export function distanceKm(a: LatLon, b: LatLon) {
  const rad = Math.PI / 180
  const dLat = (b.lat - a.lat) * rad
  const dLon = (b.lon - a.lon) * rad
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dLon / 2) ** 2
  return 6371 * 2 * Math.asin(Math.sqrt(h))
}

/** Whether a view is near this exploration's evidence. A shared view of
 *  another city must not be restored over this one's data. */
export function nearBounds(center: LatLon, bounds: Bounds | null, km = 60) {
  if (!bounds) return false
  const clamped = { lat: Math.min(Math.max(center.lat, bounds.south), bounds.north), lon: Math.min(Math.max(center.lon, bounds.west), bounds.east) }
  return distanceKm(center, clamped) <= km
}

export interface MapView { lat: number; lon: number; zoom: number }

export function encodeMapHash(view: MapView) {
  return `#map=${view.lat.toFixed(5)},${view.lon.toFixed(5)},${Math.round(view.zoom * 100) / 100}`
}

export function decodeMapHash(hash: string): MapView | null {
  const match = /^#?map=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?),(\d+(?:\.\d+)?)$/.exec(hash.trim())
  if (!match) return null
  const lat = Number(match[1]), lon = Number(match[2]), zoom = Number(match[3])
  if (!validCoordinate({ lat, lon }) || zoom < 0 || zoom > 22) return null
  return { lat, lon, zoom }
}

export type SearchTarget = { kind: 'area' | 'venue' | 'direction'; id: string; label: string }

/** Find a target the data supports. No match means no match: nothing is
 *  looked up elsewhere. */
export function matchSearch(query: string, targets: SearchTarget[]): SearchTarget | null {
  const needle = query.trim().toLowerCase()
  if (!needle) return null
  return targets.find((t) => t.label.toLowerCase() === needle)
    ?? targets.find((t) => t.label.toLowerCase().startsWith(needle))
    ?? targets.find((t) => t.label.toLowerCase().includes(needle))
    ?? null
}

/** What the venue panel lists as missing or uncertain. Each entry is a fact
 *  about what was, or was not, returned. */
export function uncertainties(venue: Evidence, placement: Placement): string[] {
  const out: string[] = []
  if (placement.state === 'plotted') out.push('The pin is an address match, not a surveyed venue point. It does not prove the business trades there today.')
  if (placement.state === 'not_plotted') out.push(`Not on the map: ${placement.reason}`)
  if (!venue.address) out.push('Qloo returned no street address.')
  if (venue.affinity == null) out.push('Qloo returned no affinity for this place.')
  if (!venue.description) out.push('Qloo returned no description.')
  if (venue.relevance?.evidenceClass === 'unverified_geography') out.push('Qloo did not confirm this place’s location against the brief’s city.')
  if (venue.relevance?.confidence && /low|unknown/i.test(venue.relevance.confidence)) out.push(`CultureForge’s relevance rule rates its confidence as ${venue.relevance.confidence}.`)
  out.push('Foot traffic, demand, rent and willingness to pay: Qloo does not return them.')
  return out
}
