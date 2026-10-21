import type { Concept, Evidence } from './contracts'

export type CellState = 'unchanged' | 'sources' | 'changed' | 'disappeared' | 'unknown'
export function recipeKey(concept: Concept) {
  const rules = [...new Set(concept.decisions.map((decision) => decision.ruleId).filter(Boolean))].sort()
  return rules.length ? rules.join('|') : null
}
function sourceKey(concept: Concept, evidence: Evidence[]) {
  const byId = new Map(evidence.map((item) => [item.id, item]))
  return concept.evidenceIds.map((id) => {
    const item = byId.get(id)
    return item ? `${item.kind}:${item.entityId ?? item.tagId ?? item.id}` : `missing:${id}`
  }).sort().join('|')
}
function compositionKey(concept: Concept) {
  return JSON.stringify({ name: concept.name, tagline: concept.tagline, description: concept.description,
    signals: [...concept.signals].sort(),
    decisions: concept.decisions.map(({ field, proposal, ruleId }) => ({ field, proposal, ruleId })).sort((a, b) => a.field.localeCompare(b.field)),
    image: concept.image, imageAlt: concept.imageAlt })
}
export function compareDirection(original: Concept, rebuilt: { concepts: Concept[]; evidence: Evidence[] }, originalEvidence: Evidence[]): CellState {
  const key = recipeKey(original)
  if (!key) return 'unknown'
  const matching = rebuilt.concepts.find((concept) => recipeKey(concept) === key)
  if (!matching) return 'disappeared'
  // A changed citation must not hide a changed description, photo or proposal.
  if (compositionKey(original) !== compositionKey(matching)) return 'changed'
  if (sourceKey(original, originalEvidence) !== sourceKey(matching, rebuilt.evidence)) return 'sources'
  return 'unchanged'
}
