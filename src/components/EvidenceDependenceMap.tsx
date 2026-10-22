import { useEffect, useRef, useState } from 'react'
import { ArrowRight, Check, LoaderCircle, RotateCcw, X } from 'lucide-react'
import type { Evidence, GenerateResponse } from '../contracts'
import { recompose } from '../api'
import { compareDirection, recipeKey } from '../evidenceDependence'
import type { CellState } from '../evidenceDependence'

type Rebuild = Awaited<ReturnType<typeof recompose>>
type RemovalRow = { venue: Evidence; state: 'ready' | 'error'; rebuild?: Rebuild; error?: string }

const labels: Record<CellState, string> = {
  unchanged: 'No composition change',
  sources: 'Supporting sources changed',
  changed: 'Answer changed',
  disappeared: 'Direction disappeared',
  unknown: 'Identity unavailable',
}

export type DependenceSummary = Record<string, Record<CellState, number>>

export function EvidenceDependenceMap({ baseline: baselineProp, onClose, onUseRebuild, onRestoreBaseline, onSummary }: {
  baseline: GenerateResponse
  onClose: () => void
  onUseRebuild: (result: Rebuild, venueLabel: string) => void
  onRestoreBaseline: (result: GenerateResponse) => void
  onSummary?: (summary: DependenceSummary | null) => void
}) {
  // Keep the reference frozen while the founder previews or applies branches.
  const [baseline] = useState(baselineProp)
  const venues = baseline.evidence.filter((item) => item.kind === 'entity' && item.entityId)
  const [rows, setRows] = useState<RemovalRow[]>([])
  const [running, setRunning] = useState(false)
  const [completed, setCompleted] = useState(0)
  const [selected, setSelected] = useState<{ venueId: string; conceptKey: string } | null>(null)
  const dialog = useRef<HTMLElement>(null)
  const close = useRef(onClose)
  close.current = onClose
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    dialog.current?.focus()
    function keydown(event: KeyboardEvent) {
      if (event.key === 'Escape') { event.stopPropagation(); close.current() }
      if (event.key !== 'Tab') return
      const nodes = dialog.current?.querySelectorAll<HTMLElement>('button:not(:disabled),a[href]')
      if (!nodes?.length) return
      const first = nodes[0], last = nodes[nodes.length - 1]
      if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog.current)) { event.preventDefault(); last.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
    }
    document.addEventListener('keydown', keydown)
    return () => { document.body.style.overflow = overflow; document.removeEventListener('keydown', keydown); if (previous?.isConnected) previous.focus() }
  }, [])

  const run = async () => {
    if (running || !venues.length) return
    setRunning(true)
    setRows([])
    onSummary?.(null)
    setSelected(null)
    setCompleted(0)
    const completedRows: RemovalRow[] = []
    for (const venue of venues) {
      try {
        const rebuild = await recompose(baseline.project, venue.entityId ? [venue.entityId] : [], [], baseline)
        const row = { venue, state: 'ready' as const, rebuild }
        completedRows.push(row)
        setRows((current) => [...current, row])
      } catch (error) {
        const row = { venue, state: 'error' as const, error: error instanceof Error ? error.message : 'This removal could not be recomposed.' }
        completedRows.push(row)
        setRows((current) => [...current, row])
      }
      setCompleted((current) => current + 1)
    }
    setRunning(false)
    // Failed removals remain unknown; they are never silently counted as unchanged.
    const summary: DependenceSummary = {}
    for (const concept of baseline.concepts) {
      const key = recipeKey(concept) ?? concept.id
      summary[key] = { unchanged: 0, sources: 0, changed: 0, disappeared: 0, unknown: 0 }
      for (const row of completedRows) summary[key][row.rebuild ? compareDirection(concept, row.rebuild, baseline.evidence) : 'unknown'] += 1
    }
    onSummary?.(summary)
  }

  const selectedRow = rows.find((row) => row.venue.entityId === selected?.venueId)
  const selectedOriginal = selected && baseline.concepts.find((concept) => recipeKey(concept) === selected.conceptKey)
  const selectedRebuilt = selectedRow?.rebuild?.concepts.find((concept) => recipeKey(concept) === selected?.conceptKey)

  return <div className="dependence-backdrop" role="presentation" onClick={onClose}>
    <section ref={dialog} tabIndex={-1} className="dependence-dialog" role="dialog" aria-modal="true" aria-labelledby="dependence-title" onClick={(event) => event.stopPropagation()}>
      <header className="dependence-header">
        <div><span className="small-cap"><span className="orange-dot"/> COMPOSITION DEPENDENCE TEST</span><h2 id="dependence-title">Which place is carrying this answer?</h2><p>Remove each returned venue once, from the same held evidence, and compare what CultureForge recomposes.</p></div>
        <button className="icon-button" onClick={onClose} aria-label="Close evidence dependence test"><X size={18}/></button>
      </header>
      <div className="dependence-boundary"><Check size={15}/> One venue removed at a time · no new Qloo calls · no model naming call. Answer changes include descriptions, proposals, themes or imagery; optional model names and taglines are excluded. A source-only change alters citations. This tests dependence within this sample, not business viability.</div>
      <div className="dependence-actions">
        <button className="button button-primary" onClick={run} disabled={running || !venues.length}>{running ? <><LoaderCircle size={15} className="spin"/> Rebuilding {completed} / {venues.length}</> : rows.length ? 'Run again from original evidence' : 'Run the dependence test'} <ArrowRight size={15}/></button>
        <button className="button button-secondary" onClick={() => onRestoreBaseline(baseline)}><RotateCcw size={14}/> Restore original answer</button>
      </div>
      {!venues.length ? <p className="dependence-empty">No returned places are available to remove from this answer.</p> : !rows.length && !running ? <p className="dependence-empty">The test runs one local recomposition per returned venue. Your current answer stays unchanged until you choose a rebuilt version.</p> : null}
      {rows.length > 0 && <div className="dependence-table-wrap"><table className="dependence-table"><thead><tr><th>Place removed</th>{baseline.concepts.map((concept) => <th key={recipeKey(concept) ?? concept.id}>{concept.name}</th>)}</tr></thead><tbody>{rows.map((row) => <tr key={row.venue.entityId ?? row.venue.id}><th><span>{row.venue.label}</span><small>{row.state === 'error' ? 'Not recomposed' : 'One-place removal'}</small></th>{baseline.concepts.map((concept) => {
        const state = row.rebuild ? compareDirection(concept, row.rebuild, baseline.evidence) : 'unknown'
        const key = recipeKey(concept) ?? concept.id
        return <td key={key}><button disabled={!row.rebuild || state === 'unknown'} className={`dependence-cell is-${state} ${selected?.venueId === row.venue.entityId && selected?.conceptKey === key ? 'is-selected' : ''}`} onClick={() => row.venue.entityId && setSelected({ venueId: row.venue.entityId, conceptKey: key })} aria-label={`${row.venue.label} removed: ${labels[state]}`}><span>{row.state === 'error' ? 'Not evaluated' : labels[state]}</span></button>{row.error && <small className="dependence-error">{row.error}</small>}</td>
      })}</tr>)}</tbody></table></div>}
      {selected && selectedRow?.state === 'ready' && <div className="dependence-receipt">
        <div className="dependence-receipt-head"><span className="small-cap">ONE REMOVAL · BEFORE / AFTER</span><strong>Removed: {selectedRow.venue.label}</strong></div>
        {selectedOriginal && <div className="dependence-compare"><article><span>ORIGINAL DIRECTION</span><h3>{selectedOriginal.name}</h3><p>{selectedOriginal.description}</p><small>{selectedOriginal.evidenceIds.length} cited evidence items</small></article><ArrowRight size={18}/><article>{selectedRebuilt ? <><span>RECOMPOSED FROM WHAT REMAINS</span><h3>{selectedRebuilt.name}</h3><p>{selectedRebuilt.description}</p><small>{selectedRebuilt.evidenceIds.length} cited evidence items</small></> : <><span>RECOMPOSED RESULT</span><h3>Direction disappeared</h3><p>This recipe did not retain a supported direction after the selected venue was removed.</p><small>No matching recipe remains in this branch.</small></>}</article></div>}
        <p className="dependence-receipt-note">{selectedRow.rebuild?.notice}</p>
        {selectedRow.rebuild && <button className="button button-secondary" onClick={() => onUseRebuild(selectedRow.rebuild as Rebuild, selectedRow.venue.label)}>Use this rebuilt answer <ArrowRight size={14}/></button>}
      </div>}
      {running && <p className="dependence-progress" role="status">Recomposing from the held evidence only. The baseline remains frozen while each single-place branch is built.</p>}
    </section>
  </div>
}
