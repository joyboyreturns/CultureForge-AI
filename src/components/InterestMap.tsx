import { useEffect, useState } from 'react'
import { LoaderCircle, MapPin } from 'lucide-react'
import type { Concept, Evidence } from '../contracts'
import { fetchInterestCells } from '../api'
import type { InterestLayer } from '../api'
import { GeoMap } from './GeoMap'

/**
 * Where a returned place's audience concentrates, as Qloo interest cells.
 *
 * Qloo's `where_popular` returns latitude/longitude cells where one entity
 * has strong query-relative affinity. They are **interest cells, not venue
 * pins**: Qloo's geocode for a place is an address, not a coordinate, so a
 * place is plotted only when a verified coordinate came back with it. Drawing a cell costs one Qloo request
 * the first time and nothing after, and the button says which.
 */
export function InterestMap({ evidence, concepts, selectedId, location }: {
  evidence: Evidence[]
  concepts: Concept[]
  selectedId: string
  location: string
}) {
  const places = evidence.filter((item) => item.kind === 'entity' && item.entityId)
  const selected = concepts.find((concept) => concept.id === selectedId)
  const anchorId = places.find((place) => selected?.evidenceIds.includes(place.id))?.entityId ?? places[0]?.entityId ?? ''
  const [entityId, setEntityId] = useState(anchorId)
  const [layer, setLayer] = useState<InterestLayer | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  // A different direction brings a different anchor; the map follows it
  // rather than keep showing a place the reader did not choose.
  useEffect(() => { setEntityId(anchorId); setLayer(null); setError('') }, [anchorId])

  async function draw() {
    if (!entityId) return
    setBusy(true); setError('')
    try { setLayer(await fetchInterestCells(entityId, location)) } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Qloo did not return interest cells for this place.')
    }
    setBusy(false)
  }

  if (!places.length) return <p className="source-panel-note">No returned place carries a Qloo entity ID, so there is nothing to map.</p>
  const place = places.find((item) => item.entityId === entityId)
  return <div className="interest-map">
    <p className="source-panel-note">Interest cells, not venue pins: each dot is a geographic cell where Qloo reports strong affinity for the chosen place, inside {location}. Qloo gives places an address rather than a coordinate, and CultureForge does not geocode, so a place is drawn only when a verified coordinate came back with it.</p>
    <div className="interest-map-controls">
      <label><MapPin size={14}/><span>Place</span>
        <select value={entityId} onChange={(event) => { setEntityId(event.target.value); setLayer(null) }}>
          {places.map((item) => <option key={item.entityId} value={item.entityId ?? ''}>{item.label}{item.entityId === anchorId ? ' (this direction’s anchor)' : ''}</option>)}
        </select>
      </label>
      <button type="button" className="button button-secondary" onClick={draw} disabled={busy || !entityId}>
        {busy ? <><LoaderCircle size={14} className="spin"/> Asking Qloo…</> : 'Map interest cells'}
      </button>
    </div>
    {error && <div className="api-error" role="alert">{error}</div>}
    {layer && layer.entityId === entityId && <>
      <p className="interest-map-cost">{layer.cached ? 'Held Qloo evidence: no new request.' : `${layer.transportRequests} new Qloo request.`} {place?.label}, within {layer.within}.</p>
      <GeoMap layer={{ entityId: layer.entityId, within: layer.within, points: layer.points, bounds: layer.bounds, note: layer.note }} label={`Where interest in ${place?.label ?? 'this place'} concentrates`}
        context={{ evidence, concepts, selectedId, entityId, anchorEntityId: anchorId || undefined }}/>
    </>}
  </div>
}
