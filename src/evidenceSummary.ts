import type { Concept, Evidence } from './contracts'

/** Counts citations against the evidence on screen; it does not rate truth. */
export function citationCoverage(concept: Concept, evidence: Evidence[]) {
  const available = new Set(evidence.map((item) => item.id))
  const decisions = concept.decisions ?? []
  const cited = new Set(decisions.flatMap((decision) => decision.evidenceIds).filter((id) => available.has(id)))
  return {
    numerator: decisions.filter((decision) => decision.evidenceIds.some((id) => available.has(id))).length,
    denominator: decisions.length,
    decisionEvidenceIds: [...cited],
  }
}

/** The Qloo entity type of a bridged item: `urn:entity:artist` -> `artist`. */
export function bridgeDomain(item: Evidence): string {
  return (item.entityType ?? '').split(':').pop()?.replace('_', ' ') || 'entity'
}

/** What a piece of evidence is, in words the reader can check. */
export function evidenceKindLabel(item: Evidence): string {
  if (item.kind === 'tag') return 'Audience seed'
  if (item.kind === 'crossdomain') return `Qloo ${bridgeDomain(item)} · audience tags, no location`
  return 'Qloo place'
}
