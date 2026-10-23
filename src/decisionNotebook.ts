import type { Concept, GenerateResponse } from './contracts'

export interface DecisionDraft {
  hypothesis: string
  method: 'interviews' | 'concept_test' | 'pop_up'
  success: string
  stop: string
  observations: string
  choice: 'investigate' | 'revise' | 'park'
  owner?: string
  reviewDate?: string
  spendingCap?: string
  savedAt?: string
}

/** Direction identity includes its evidence: notes never silently migrate to a rebuilt answer. */
export function notebookKey(result: GenerateResponse, concept: Concept) {
  return 'cultureforge-decision-v1:' + JSON.stringify([
    result.project.businessType, result.project.audience, result.project.location, result.project.budget,
    [...result.project.objectives].sort(), concept.id, concept.name, concept.description,
    concept.decisions.map((d) => [d.field, d.proposal, d.ruleId]),
    result.evidence.map((e) => [e.id, e.entityId ?? e.tagId, e.label, e.description ?? '']).sort((a, b) => String(a[0]).localeCompare(String(b[0]))),
  ])
}

export function defaultDecision(result: GenerateResponse, concept: Concept): DecisionDraft {
  return { hypothesis: `People in the audience “${result.project.audience}” would choose the experience proposed in “${concept.name}” in ${result.project.location}.`,
    method: 'interviews', success: '', stop: '', observations: '', choice: 'investigate' }
}

export function readDecision(key: string): DecisionDraft | null {
  try {
    const value = JSON.parse(localStorage.getItem(key) ?? 'null')
    if (!value || !['interviews', 'concept_test', 'pop_up'].includes(value.method) || !['investigate', 'revise', 'park'].includes(value.choice)) return null
    if (!['hypothesis', 'success', 'stop', 'observations'].every((field) => typeof value[field] === 'string')) return null
    if (['owner', 'reviewDate', 'spendingCap'].some((field) => value[field] !== undefined && typeof value[field] !== 'string')) return null
    return value as DecisionDraft
  } catch { return null }
}

export function renderDecision(draft: DecisionDraft): string {
  const method = { interviews: 'Audience interviews', concept_test: 'Concept walkthrough', pop_up: 'Small pop-up or prototype' }[draft.method]
  return ['## Founder decision notebook',
    'Founder-entered plan and observations. Not independently verified; not Qloo evidence. This record does not change the cultural verdict.', '',
    `Decision: ${draft.choice}`, `Hypothesis: ${draft.hypothesis}`, `Method: ${method}`,
    `Accountable owner: ${draft.owner?.trim() || 'Not assigned'}`,
    `Review date: ${draft.reviewDate || 'Not set'}`,
    `Experiment spending cap (team-entered, not a cost estimate): ${draft.spendingCap?.trim() || 'Not set'}`,
    `Proceed only if: ${draft.success || 'Not defined'}`, `Revise or stop if: ${draft.stop || 'Not defined'}`,
    `Recorded observations: ${draft.observations || 'None recorded; field validation has not been demonstrated.'}`,
    `Saved: ${draft.savedAt ?? 'Unsaved draft'}`, ''].join('\n')
}
