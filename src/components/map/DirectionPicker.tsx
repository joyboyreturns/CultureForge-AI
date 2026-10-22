import { useId } from 'react'
import { ArrowUpRight, Crosshair } from 'lucide-react'
import type { Concept } from '../../contracts'

/**
 * Choose a direction: its cited venues stay lit and the rest dim. The
 * selection is the studio's own, so the cards and the graph follow it.
 */
export function DirectionPicker({ concepts, selectedId, onSelect, focus, setFocus, summary, onFit, onOpen }: {
  concepts: Concept[]
  selectedId: string
  onSelect: (id: string) => void
  focus: boolean
  setFocus: (on: boolean) => void
  summary: { cited: number; plotted: number; tags: number; total: number }
  onFit: () => void
  onOpen?: () => void
}) {
  const id = useId()
  if (!concepts.length) return <div className="ox-direction"><p className="ox-dim">No direction was supported by this evidence, so there is nothing to highlight. The venues are still shown.</p></div>
  return <div className="ox-direction">
    <label htmlFor={`${id}-pick`} className="ox-tiny">DIRECTION</label>
    <div className="ox-direction-row">
      <select id={`${id}-pick`} value={selectedId} onChange={(event) => { onSelect(event.target.value); setFocus(true) }}>
        {concepts.map((concept) => <option key={concept.id} value={concept.id}>{concept.name}</option>)}
      </select>
      <button type="button" className={`ox-chip${focus ? ' is-on' : ''}`} aria-pressed={focus} onClick={() => setFocus(!focus)}>
        {focus ? 'Highlighting its venues' : 'Highlight its venues'}
      </button>
    </div>
    <p className="ox-direction-summary">
      Cites {summary.total} piece{summary.total === 1 ? '' : 's'} of Qloo evidence: {summary.cited} venue{summary.cited === 1 ? '' : 's'} ({summary.plotted} on the map) and {summary.tags} audience seed{summary.tags === 1 ? '' : 's'}.
    </p>
    <div className="ox-direction-row">
      <button type="button" className="text-link" onClick={onFit} disabled={!summary.plotted}><Crosshair size={13} aria-hidden="true"/> Frame its venues</button>
      {onOpen && <button type="button" className="text-link" onClick={onOpen}>Open the full direction <ArrowUpRight size={13} aria-hidden="true"/></button>}
    </div>
  </div>
}
