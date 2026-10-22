import type { Evidence } from '../contracts'

const CLASSES: { id: string; label: string; note: string; color: string }[] = [
  { id: 'direct_business', label: 'Same kind of business', note: 'Returned text matches the requested category', color: 'var(--mix-direct, #2f7d5b)' },
  { id: 'indirect_business', label: 'Related business', note: 'Adjacent category; cannot anchor a direction', color: 'var(--mix-indirect, #8aa84a)' },
  { id: 'cultural_attraction', label: 'Cultural attraction', note: 'Context only; not a competitor', color: 'var(--mix-attraction, #8a6fb3)' },
  { id: 'unverified_geography', label: 'Another location', note: 'Matches the category but not the requested city', color: 'var(--mix-geo, #d19a3a)' },
  { id: 'audience_affinity', label: 'Audience affinity', note: 'What this audience likes elsewhere; not local', color: 'var(--mix-affinity, #4f8fb8)' },
  { id: 'unrelated', label: 'Unrelated', note: 'Kept visible, never used as a reference', color: 'var(--mix-unrelated, #9a9a9a)' },
]

/** One bar: how the returned evidence sorts by relevance. Counts only, from the rules' own classification. */
export function EvidenceMix({ evidence }: { evidence: Evidence[] }) {
  const counts = new Map<string, number>()
  for (const item of evidence) {
    if (item.kind !== 'entity' && item.kind !== 'crossdomain') continue
    const cls = item.relevance?.evidenceClass
    if (cls) counts.set(cls, (counts.get(cls) ?? 0) + 1)
  }
  const total = [...counts.values()].reduce((a, b) => a + b, 0)
  if (!total) return null
  const rows = CLASSES.filter(c => counts.get(c.id))
  const summary = rows.map(c => `${counts.get(c.id)} ${c.label.toLowerCase()}`).join(', ')
  return (
    <section className="evidence-mix panel" aria-label="What the returned evidence is">
      <header><strong>What Qloo returned, sorted by relevance</strong><small>{total} results · classified by CultureForge’s rules, not scored</small></header>
      <svg role="img" aria-label={`Evidence mix: ${summary}`} viewBox="0 0 100 6" preserveAspectRatio="none" className="evidence-mix-bar">
        {(() => { let x = 0; return rows.map(c => { const w = (counts.get(c.id)! / total) * 100; const rect = <rect key={c.id} x={x} y={0} width={w} height={6} fill={c.color}><title>{`${c.label}: ${counts.get(c.id)}`}</title></rect>; x += w; return rect }) })()}
      </svg>
      <ul>{rows.map(c => <li key={c.id}><i style={{ background: c.color }} aria-hidden="true"/><span><b>{counts.get(c.id)}</b> {c.label}<small>{c.note}</small></span></li>)}</ul>
    </section>
  )
}
