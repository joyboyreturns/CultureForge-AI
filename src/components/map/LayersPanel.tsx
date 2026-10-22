import { useId } from 'react'
import type { ReactNode } from 'react'
import { ChevronDown, Layers3 } from 'lucide-react'
import type { OverlayVisibility } from './layers'

/**
 * The layer switches, floating over the map. Collapsible, and every control
 * is a real checkbox, so it works with a keyboard and a screen reader.
 */
export function LayersPanel({ open, setOpen, visible, setVisible, counts, heatLegend, cellsControl, contextNote }: {
  open: boolean
  setOpen: (open: boolean) => void
  visible: OverlayVisibility
  setVisible: (next: OverlayVisibility) => void
  counts: { cells: number; direct: number; indirect: number; attraction: number }
  heatLegend: ReactNode
  cellsControl: ReactNode
  contextNote: string | null
}) {
  const id = useId()
  const venues = counts.direct + counts.indirect + counts.attraction
  const toggle = (key: keyof OverlayVisibility, on: boolean) => setVisible({ ...visible, [key]: on })
  return <section className={`ox-layers${open ? ' is-open' : ''}`} aria-label="Map layers">
    <button type="button" className="ox-layers-toggle" aria-expanded={open} aria-controls={`${id}-body`} onClick={() => setOpen(!open)}>
      <Layers3 size={14} aria-hidden="true"/> Layers <ChevronDown size={14} aria-hidden="true" className="ox-chevron"/>
    </button>
    <div id={`${id}-body`} className="ox-layers-body" hidden={!open}>
      <label className="ox-layer">
        <input type="checkbox" checked={visible.heat} disabled={!counts.cells} onChange={(e) => toggle('heat', e.target.checked)}/>
        <span><b>Cultural affinity heat</b> <i>{counts.cells} cells</i></span>
      </label>
      <div className="ox-layer-detail">{counts.cells ? heatLegend : null}{cellsControl}</div>

      <label className="ox-layer">
        <input type="checkbox" checked={visible.venues} disabled={!venues} onChange={(e) => toggle('venues', e.target.checked)}/>
        <span><b>Venues</b> <i>{venues} placed</i></span>
      </label>
      <ul className="ox-key">
        <li><i className="ox-dot is-direct" aria-hidden="true"/>Direct matches <b>{counts.direct}</b></li>
        <li><i className="ox-dot is-indirect" aria-hidden="true"/>Indirect anchors <b>{counts.indirect}</b></li>
        <li><i className="ox-dot is-attraction" aria-hidden="true"/>Cultural attractions <b>{counts.attraction}</b></li>
        <li><i className="ox-dot is-cluster" aria-hidden="true"/>Group of nearby venues — click to expand</li>
      </ul>

      <label className="ox-layer">
        <input type="checkbox" checked={visible.context} disabled={Boolean(contextNote)} onChange={(e) => toggle('context', e.target.checked)}/>
        <span><b>Selected-direction context</b></span>
      </label>
      <p className="ox-layer-detail ox-dim">{contextNote ?? 'A ring marks each venue the chosen direction cites; the others dim.'}</p>
    </div>
  </section>
}
