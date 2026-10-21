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
