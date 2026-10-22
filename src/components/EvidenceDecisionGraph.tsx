import { useState } from 'react'
import type { GenerateResponse } from '../contracts'

/** Edges come only from stored decision citations, never inferred affinities. */
export function EvidenceDecisionGraph({ result, onInspect, onRemove }: {
  result: GenerateResponse
  onInspect?: (id: string) => void
  onRemove?: () => void
}) {
  const [directionId, setDirectionId] = useState('')
  const [sourceId, setSourceId] = useState('')
  const direction = result.concepts.find(c => c.id === directionId) ?? result.concepts[0]
  const decisions = direction?.decisions ?? []
  const cited = new Set(decisions.flatMap(d => d.evidenceIds))
  const sources = result.evidence.filter(e => cited.has(e.id))
  const selected = result.evidence.find(e => e.id === sourceId) ?? sources[0]
  const height = Math.max(230, sources.length * 48 + 60, decisions.length * 68 + 60)
  const sourceY = (i: number) => 50 + i * 48
  const decisionY = (i: number) => 65 + i * 68
  const places = result.evidence.filter(e => e.kind === 'entity')
  const eligible = places.filter(e => e.relevance?.anchorEligible)
  return <section className="evidence-graph panel" aria-label="Source to decision evidence graph">
    <header><span className="small-cap">SOURCE → PROPOSAL → DIRECTION</span><h2>What is this answer built on?</h2>
      <p>Qloo returned the sources. CultureForge proposed the decisions. Lines show attached citations, not proof that a proposal is true.</p></header>
    <div className="evidence-graph-directions">{result.concepts.map(c => <button key={c.id} aria-pressed={direction?.id === c.id} onClick={() => { setDirectionId(c.id); setSourceId('') }}>{c.name}</button>)}</div>
    {direction && <p className="graph-scroll-note">Scroll across to follow the citations through to the proposed direction →</p>}
    {direction ? <div className="evidence-graph-scroll" tabIndex={0} role="region" aria-label="Scrollable citation graph"><svg viewBox={`0 0 940 ${height}`} role="group" aria-label={`Citations for ${direction.name}`}>
      <text x="15" y="20" className="graph-column">RETURNED QLOO SOURCES</text><text x="380" y="20" className="graph-column">CULTUREFORGE PROPOSALS</text>
      {decisions.flatMap((d, di) => sources.filter(s => d.evidenceIds.includes(s.id)).map(s => <path key={`${d.id}-${s.id}`} d={`M 285 ${sourceY(sources.indexOf(s))} C 335 ${sourceY(sources.indexOf(s))}, 330 ${decisionY(di)}, 375 ${decisionY(di)}`} className={`graph-citation${s.id === selected?.id ? ' selected' : ''}`} />))}
      {decisions.map((d, i) => <path key={d.id} d={`M 650 ${decisionY(i)} C 700 ${decisionY(i)}, 680 ${height / 2}, 730 ${height / 2}`} className="graph-interpretation" />)}
      {sources.map((s, i) => <g key={s.id} role="button" tabIndex={0} aria-label={`Inspect ${s.label}`} onClick={() => setSourceId(s.id)} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setSourceId(s.id) } }} className={`graph-source${selected?.id === s.id ? ' selected' : ''}`}>
        <title>{s.label} · {s.relevance?.relationship ?? s.kind}</title><rect x="10" y={sourceY(i) - 17} width="275" height="35" rx="8" /><text x="22" y={sourceY(i) + 4}>{s.label.length > 31 ? s.label.slice(0, 30) + '…' : s.label}</text></g>)}
      {decisions.map((d, i) => <g key={d.id} className="graph-decision"><title>{d.proposal}</title><rect x="375" y={decisionY(i) - 22} width="275" height="44" rx="8" /><text x="388" y={decisionY(i) + 4}>{d.field}</text></g>)}
      <g className="graph-concept"><title>{direction.name}</title><rect x="730" y={height / 2 - 35} width="200" height="70" rx="10"/><text x="744" y={height / 2 - 4}>PROPOSED DIRECTION</text><text x="744" y={height / 2 + 18}>{direction.name.length > 21 ? direction.name.slice(0, 20) + '…' : direction.name}</text></g>
    </svg></div> : <p className="graph-abstention">No category-relevant direction emerged. The retrieved associations remain available below. Specify the business idea or revise the audience or city to try again.</p>}
    {selected && <div className="graph-source-detail" aria-live="polite"><strong>{selected.label}</strong><span>{selected.entityId ?? selected.tagId}</span><p>{selected.description || 'Qloo returned no description for this source.'}</p>{selected.relevance && <><b>{selected.relevance.relationship.toUpperCase()} · CultureForge rule assessment</b><ul>{selected.relevance.reasons.map(reason => <li key={reason}>{reason}</li>)}</ul></>}
      {onInspect && <button className="text-link" onClick={() => onInspect(selected.id)}>Inspect request and provenance →</button>}
      {!onInspect && <details><summary>Retrieval provenance</summary><p>Trace: {selected.traceId ?? 'not recorded'}</p><pre>{JSON.stringify(result.trace.find(event => event.id === selected.traceId)?.request ?? {}, null, 2)}</pre><p>Evidence acquired: {result.delivery?.acquiredAt ?? 'not recorded'}</p></details>}
      <div className="graph-dependent-proposals">{decisions.filter(d => d.evidenceIds.includes(selected.id)).map(d => <p key={d.id}><b>{d.field}:</b> {d.proposal}</p>)}</div></div>}
    <details className="graph-relevance"><summary>Reference relevance · {eligible.length} eligible / {places.length} returned places</summary><p>Category matches use returned text. They do not establish opening hours, suitability or demand. Indirect associations remain inspectable.</p>{places.map(e => <button key={e.id} onClick={() => setSourceId(e.id)}><strong>{e.label}</strong><span>{e.relevance?.relationship ?? 'Not assessed in this saved answer'}{e.relevance?.anchorEligible ? ' · anchor eligible' : ''}</span></button>)}</details>
    {onRemove && <footer><p>Test whether the answer depends on its sources. A removal rebuilds the directions from held evidence.</p><button className="text-link" onClick={onRemove}>Remove a source and compare →</button></footer>}
  </section>
}
