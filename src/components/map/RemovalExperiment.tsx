import { useEffect, useRef, useState } from 'react'
import { ArrowRight, FlaskConical, LoaderCircle } from 'lucide-react'
import type { Concept, Evidence, ProjectRequest } from '../../contracts'
import { recompose } from '../../api'
import type { RecomposeResult } from '../../api'
import { CELL_STATE_LABELS, REMOVAL_BOUNDARY, compareDirection, recipeKey } from '../../evidenceDependence'
import type { CellState } from '../../evidenceDependence'

/**
 * "What happens without this evidence?"
 *
 * The same removal the provenance drawer and the dependence test run: the
 * held evidence is recomposed on the server with this one venue taken out,
 * and each direction is compared with `compareDirection`. Nothing is applied
 * until the reader chooses to; nothing here changes a verdict.
 */
type Outcome = 'unchanged' | 'changed' | 'unresolved'
const OUTCOME: Record<CellState, Outcome> = { unchanged: 'unchanged', sources: 'changed', changed: 'changed', disappeared: 'changed', unknown: 'unresolved' }
const OUTCOME_WORDS: Record<Outcome, string> = { unchanged: 'Unchanged', changed: 'Changed', unresolved: 'Unresolved' }

export function RemovalExperiment({ venue, concepts, evidence, project, unsupported, onApply, onRan }: {
  venue: Evidence
  concepts: Concept[]
  evidence: Evidence[]
  project: ProjectRequest
  /** Why the removal cannot run on this answer, when it cannot. */
  unsupported: string | null
  onApply?: (rebuild: RecomposeResult, venueLabel: string) => void
  onRan?: () => void
}) {
  const [state, setState] = useState<'idle' | 'running' | 'done' | 'error'>('idle')
  const [rebuild, setRebuild] = useState<RecomposeResult | null>(null)
  const [error, setError] = useState('')
  const alive = useRef(true)
  useEffect(() => { alive.current = true; return () => { alive.current = false } }, [])
  // A different venue, or a different answer, is a different experiment.
  useEffect(() => { setState('idle'); setRebuild(null); setError('') }, [venue.id, evidence])

  const citing = concepts.filter((concept) => concept.evidenceIds.includes(venue.id))
  const reason = unsupported
    ?? (!venue.entityId ? 'This venue carries no Qloo entity ID, so the recomposition has nothing to exclude.' : null)
    ?? (!citing.length ? 'No generated direction cites this venue, so removing it cannot change a direction. Pick a cited venue (highlighted when a direction is chosen).' : null)

  async function run() {
    if (reason || state === 'running' || !venue.entityId) return
    setState('running'); setError('')
    try {
      const result = await recompose(project, [venue.entityId], [], { evidence })
      if (!alive.current) return
      setRebuild(result); setState('done'); onRan?.()
    } catch (caught) {
      if (!alive.current) return
      // A failure is a failure, never an empty success.
      setRebuild(null); setState('error')
      setError(caught instanceof Error ? caught.message : 'The recomposition failed.')
    }
  }

  const rows = rebuild ? concepts.map((concept) => {
    const cell = compareDirection(concept, rebuild, evidence)
    const after = rebuild.concepts.find((candidate) => recipeKey(candidate) === recipeKey(concept))
    return { concept, cell, outcome: OUTCOME[cell], after }
  }) : []
  const originalKeys = new Set(concepts.map((concept) => recipeKey(concept)))
  const appeared = rebuild ? rebuild.concepts.filter((concept) => !originalKeys.has(recipeKey(concept))) : []
  const upstream = rebuild?.delivery?.transportRequests
  const held = rebuild && (upstream == null || upstream === 0)

  return <section className="ox-removal" aria-labelledby={`ox-removal-${venue.id}`}>
    <h4 id={`ox-removal-${venue.id}`}><FlaskConical size={13} aria-hidden="true"/> What happens without this evidence?</h4>
    {reason ? <p className="ox-dim">{reason}</p> : <>
      <p>Remove <b>{venue.label}</b> and rebuild the directions from what is left. It is cited by {citing.length} direction{citing.length === 1 ? '' : 's'}.</p>
      <button type="button" className="button button-primary" onClick={run} disabled={state === 'running'}>
        {state === 'running' ? <><LoaderCircle size={14} className="spin" aria-hidden="true"/> Recomposing…</> : state === 'done' ? 'Run it again' : 'What happens without this evidence?'}
      </button>
    </>}
    {state === 'error' && <p className="ox-error" role="alert">{error}</p>}
    {rebuild && <div className="ox-removal-result" role="status">
      <p className="ox-tiny">REMOVED: {venue.label.toUpperCase()}</p>
      <ul className="ox-before-after">{rows.map(({ concept, cell, outcome, after }) => <li key={concept.id} className={`is-${outcome}`}>
        <span className="ox-outcome">{OUTCOME_WORDS[outcome]}</span>
        <span className="ox-ba"><b>{concept.name}</b><ArrowRight size={12} aria-label="becomes"/>{after ? <b>{after.name}</b> : <i>no supported direction</i>}</span>
        <small>{CELL_STATE_LABELS[cell]}</small>
      </li>)}
      {appeared.map((concept) => <li key={concept.id} className="is-changed"><span className="ox-outcome">New</span><span className="ox-ba"><i>none</i><ArrowRight size={12} aria-label="becomes"/><b>{concept.name}</b></span><small>A direction that was not in the original answer</small></li>)}
      </ul>
      <p className="ox-tiny">{rebuild.concepts.length} of {concepts.length} directions remain supported.</p>
      <div className="ox-boundary">
        <p><b>What it demonstrates.</b> Whether CultureForge’s rules compose these directions differently without this one venue, from the same sample.</p>
        <p><b>What it cannot establish.</b> Demand, footfall, rent, or whether the business would work there; or what Qloo would return if asked again.{held ? ' Held evidence, no new Qloo request — not a fresh experiment.' : ''}</p>
        <p className="ox-dim">{REMOVAL_BOUNDARY}</p>
        <p className="ox-dim">{rebuild.notice}{upstream != null ? ` New upstream requests: ${upstream}.` : ''}</p>
      </div>
      {onApply && <>
        <button type="button" className="button button-secondary" onClick={() => onApply(rebuild, venue.label)}>Apply this rebuilt answer <ArrowRight size={14} aria-hidden="true"/></button>
        <p className="ox-dim">Applying replaces the directions on screen. The current evidence test is cleared rather than re-scored, because a verdict belongs to the directions it judged. You can undo it here.</p>
      </>}
    </div>}
  </section>
}
