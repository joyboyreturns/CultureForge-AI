import { useEffect, useRef } from 'react'
import type { ReactNode } from 'react'
import { ArrowUpRight, X } from 'lucide-react'
import type { Concept, Evidence } from '../../contracts'
import { CLASS_WORDS, KIND_WORDS, uncertainties } from './mapModel'
import type { Placement, VenueKind } from './mapModel'

/**
 * One venue, as Qloo returned it, and what the map does and does not know
 * about where it is. A side panel on wide screens, a bottom sheet on phones.
 */
export function VenuePanel({ venue, kind, placement, citing, selectedId, onSelectDirection, onInspect, onClose, children }: {
  venue: Evidence
  kind: VenueKind | null
  placement: Placement
  citing: Concept[]
  selectedId: string
  onSelectDirection: (id: string) => void
  onInspect?: (evidenceId: string) => void
  onClose: () => void
  children?: ReactNode
}) {
  const heading = useRef<HTMLHeadingElement>(null)
  // Move focus into the panel when a venue opens, and let Escape close it.
  useEffect(() => { heading.current?.focus() }, [venue.id])
  const cls = venue.relevance?.evidenceClass ?? null
  const excerpt = venue.presentation?.excerpt || venue.description || ''
  const signals: [string, string][] = []
  if (venue.affinity != null) signals.push(['Affinity', venue.affinity.toFixed(4)])
  if (venue.popularity != null) signals.push(['Popularity', venue.popularity.toFixed(4)])
  if (venue.rating != null) signals.push(['Local rating', String(Math.round(venue.rating * 10) / 10)])
  if (venue.priceLevel != null) signals.push(['Price level', String(venue.priceLevel)])

  return <section className="ox-venue" aria-labelledby={`ox-venue-${venue.id}`} onKeyDown={(event) => { if (event.key === 'Escape') { event.stopPropagation(); onClose() } }}>
    <header className="ox-venue-head">
      <div>
        <span className={`ox-kind is-${kind ?? 'none'}`}>{kind ? KIND_WORDS[kind] : 'Not a venue reference'}</span>
        <h3 id={`ox-venue-${venue.id}`} ref={heading} tabIndex={-1}>{venue.label}</h3>
        <p className="ox-dim">{cls ? CLASS_WORDS[cls] : 'Not classified by the relevance rule'}{venue.relevance?.category ? ` · ${venue.relevance.category}` : ''}</p>
      </div>
      <button type="button" className="icon-button" onClick={onClose} aria-label="Close venue detail"><X size={16}/></button>
    </header>

    <h4>Address, as Qloo returned it</h4>
    <p>{venue.address || 'Qloo returned no street address.'}{venue.location ? <span className="ox-dim"> · {venue.location}</span> : null}</p>
    {placement.state === 'plotted'
      ? <p className="ox-caveat">Pinned from the address Qloo returned: {placement.precision}. Source: {placement.source}.{placement.matched ? ` Matched as: ${placement.matched}.` : ''}</p>
      : placement.state === 'pending'
        ? <p className="ox-caveat" role="status">Locating this address on the server…</p>
        : <p className="ox-caveat">Not plotted: {placement.reason}</p>}

    {(signals.length > 0 || excerpt) && <>
      <h4>Qloo signals</h4>
      {signals.length > 0 && <dl className="ox-values">{signals.map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>}
      {excerpt && <p className="ox-excerpt">{excerpt}</p>}
    </>}

    {venue.relevance?.reasons?.length ? <>
      <h4>Why it is connected to the audience</h4>
      <ul>{venue.relevance.reasons.slice(0, 3).map((reason) => <li key={reason}>{reason}</li>)}</ul>
      <p className="ox-dim">CultureForge’s relevance rule, read from Qloo’s evidence.</p>
    </> : null}

    <h4>Directions that cite it</h4>
    {citing.length
      ? <ul className="ox-cites">{citing.map((concept) => <li key={concept.id}>
        <button type="button" className="text-link" aria-pressed={concept.id === selectedId} onClick={() => onSelectDirection(concept.id)}>{concept.name}</button>
        {concept.id === selectedId && <span className="ox-dim"> · selected</span>}
      </li>)}</ul>
      : <p className="ox-dim">No generated direction cites this venue.</p>}

    {onInspect && <button type="button" className="button button-secondary ox-provenance" onClick={() => onInspect(venue.id)}>
      Open provenance <ArrowUpRight size={14} aria-hidden="true"/>
    </button>}

    {children}

    <h4>Missing or uncertain</h4>
    <ul className="ox-unknowns">{uncertainties(venue, placement).map((u) => <li key={u}>{u}</li>)}</ul>
  </section>
}
