import type { Concept, Evidence } from './contracts'

export type CellState = 'unchanged' | 'sources' | 'changed' | 'disappeared' | 'unknown'
/** How a removal's effect on one direction is named, wherever it is shown. */
export const CELL_STATE_LABELS: Record<CellState, string> = {
  unchanged: 'No composition change',
  sources: 'Supporting sources changed',
  changed: 'Answer changed',
  disappeared: 'Direction disappeared',
  unknown: 'Identity unavailable',
}
/** What a one-venue removal is, and is not. Shown with every removal. */
export const REMOVAL_BOUNDARY = 'One venue removed at a time · no new Qloo calls · no model naming call. Answer changes include descriptions, proposals, themes or imagery; optional model names and taglines are excluded. A source-only change alters citations. This tests dependence within this sample, not business viability.'
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
  // Recomposition deliberately omits optional model naming. Comparing those
  // names to the original model wording made every removal look consequential.
  // Descriptions, proposals, themes and imagery still count as answer changes.
  return JSON.stringify({ description: concept.description,
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
