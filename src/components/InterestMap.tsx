import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { LoaderCircle } from 'lucide-react'
import type { Concept, Evidence, ProjectRequest } from '../contracts'
import { fetchInterestCells } from '../api'
import type { InterestLayer, RecomposeResult } from '../api'

// The explorer, and MapLibre with it, load only when this tab is opened.
const OpportunityMap = lazy(() => import('./map/OpportunityMap').then((m) => ({ default: m.OpportunityMap })))

/**
 * The Cultural Opportunity Explorer's entry point.
 *
 * Venues are placed on a street map from the address Qloo returned, geocoded
 * on the server. Qloo's interest cells (`where_popular`) are a separate
 * layer, asked for one place at a time: the first request for a place costs
 * one Qloo call and is held after that; the control says which.
 */
const heldCells = new Map<string, InterestLayer>()

export function InterestMap({ evidence, concepts, selectedId, location, project, liveComposed, onSelect, onInspect, onOpenConcept, onApplyRebuild, undo }: {
  evidence: Evidence[]
  concepts: Concept[]
  selectedId: string
  location: string
  project?: ProjectRequest
  /** True when the answer is a live, evidence-composed one, the only kind a removal can rebuild. */
  liveComposed?: boolean
  onSelect?: (id: string) => void
  onInspect?: (evidenceId: string) => void
  onOpenConcept?: (concept: Concept) => void
  onApplyRebuild?: (rebuild: RecomposeResult, venueLabel: string) => void
  undo?: { label: string; run: () => void } | null
}) {
  const places = evidence.filter((item) => item.kind === 'entity' && item.entityId)
  const selected = concepts.find((concept) => concept.id === selectedId)
  const anchorId = places.find((place) => selected?.evidenceIds.includes(place.id))?.entityId ?? places[0]?.entityId ?? ''
  const [entityId, setEntityId] = useState(anchorId)
  const [layer, setLayer] = useState<InterestLayer | null>(() => heldCells.get(`${location}|${anchorId}`) ?? null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const alive = useRef(true)
  useEffect(() => { alive.current = true; return () => { alive.current = false } }, [])
  // A different direction brings a different anchor; the cells follow it,
  // from what is already held when they were drawn before.
  useEffect(() => { setEntityId(anchorId) }, [anchorId])
  useEffect(() => { setLayer(heldCells.get(`${location}|${entityId}`) ?? null); setError('') }, [entityId, location])

  async function draw() {
    if (!entityId || busy) return
    setBusy(true); setError('')
    try {
      const next = await fetchInterestCells(entityId, location)
      heldCells.set(`${location}|${entityId}`, next)
      if (alive.current) setLayer(next)
    } catch (caught) {
      if (alive.current) setError(caught instanceof Error ? caught.message : 'Qloo did not return interest cells for this place.')
    }
    if (alive.current) setBusy(false)
  }

  const place = places.find((item) => item.entityId === entityId)
  const cellsControl = places.length ? <div className="ox-cells-control">
    <label><span className="ox-tiny">CELLS FOR</span>
      <select value={entityId} onChange={(event) => setEntityId(event.target.value)}>
        {places.map((item) => <option key={item.entityId} value={item.entityId ?? ''}>{item.label}{item.entityId === anchorId ? ' (direction’s anchor)' : ''}</option>)}
      </select>
    </label>
    {layer ? <p className="ox-dim">{layer.cached ? 'Held Qloo evidence: no new request.' : `${layer.transportRequests} new Qloo request.`} {layer.points.length ? `${layer.points.length} cells within ${layer.within}.` : `Qloo returned no cells within ${layer.within}; none are estimated.`}</p>
      : <button type="button" className="button button-secondary" onClick={draw} disabled={busy || !entityId}>
        {busy ? <><LoaderCircle size={14} className="spin" aria-hidden="true"/> Asking Qloo…</> : 'Load interest cells'}
      </button>}
    {error && <p className="ox-error" role="alert">{error}</p>}
    <p className="ox-dim">Cells are where Qloo reports affinity for one place. They are never venues.</p>
  </div> : <p className="ox-dim">No returned place carries a Qloo entity ID, so there are no interest cells to ask for.</p>

  const brief: ProjectRequest = project ?? { businessType: 'Food & beverage', audience: '', location, budget: '', objectives: [] }
  const removalUnsupported = !project ? 'The brief behind this answer is not available here, so it cannot be recomposed.'
    : !liveComposed ? 'Removal rebuilds a live, evidence-composed answer from held Qloo evidence; this answer is not one, so it cannot be rebuilt.' : null

  return <div className="interest-map">
    <Suspense fallback={<div className="ox-skeleton is-static" role="status"><span/>Loading the street map…</div>}>
      <OpportunityMap evidence={evidence} concepts={concepts} selectedId={selectedId} onSelect={onSelect} project={brief}
        removalUnsupported={removalUnsupported} onInspect={onInspect} onOpenConcept={onOpenConcept} onApplyRebuild={onApplyRebuild} undo={undo}
        cells={layer && layer.entityId === entityId && layer.points.length ? { points: layer.points, within: layer.within, placeLabel: place?.label ?? 'the chosen place' } : null}
        cellsControl={cellsControl}/>
    </Suspense>
  </div>
}
