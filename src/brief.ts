import type { Concept, GenerateResponse } from './contracts'
import type { ChallengeResult } from './api'
import { citationCoverage } from './evidenceSummary'

/** A portable decision record. Facts and interpretations keep their labels. */
export function renderBrief(result: GenerateResponse, entries: Concept[], challenge?: ChallengeResult | null): string {
  const evidence = new Map(result.evidence.map((item) => [item.id, item]))
  const verdicts = new Map((challenge?.directions ?? []).map((item) => [item.directionId, item]))
  const lines = [
    '# CultureForge — Exploration brief', '',
    `Project: ${result.projectId}`, `Audience: ${result.project.audience}`,
    `Business idea: ${result.project.businessIdea || result.project.businessType}`,
    `Location: ${result.project.location}`, `Planning budget: ${result.project.budget}`,
    `Objectives: ${result.project.objectives.join(', ') || 'None specified'}`, '',
    'Qloo supplies cultural evidence. CultureForge proposes business interpretations. The budget is a planning assumption; launch costs have not been estimated.',
    'Scope: anchor fit within the retrieved sample. This is not evidence of demand, competition, rent, profitability or willingness to pay.', '',
    '## Evidence delivery',
    `Delivery: ${result.delivery?.kind ?? 'not recorded'}${result.delivery?.cachedIn ? ` (${result.delivery.cachedIn})` : ''}`,
    `Evidence acquired: ${result.delivery?.acquiredAt ?? 'not recorded'}`,
    `New upstream requests for this delivery: ${result.delivery?.transportRequests ?? 'not recorded'}`, '',
  ]
  for (const concept of entries) {
    const verdict = verdicts.get(concept.id)
    const coverage = citationCoverage(concept, result.evidence)
    const sourceIds = [...new Set([...concept.evidenceIds, ...concept.decisions.flatMap((item) => item.evidenceIds)])]
    lines.push(`## ${concept.name}`, concept.tagline, '', concept.description, '',
      `CultureForge planning band: ${concept.investment}`, `Cultural themes: ${concept.signals.join(', ')}`, '',
      '### Evidence and decisions',
      `Citation attachment: ${coverage.numerator} / ${coverage.denominator} decisions. This is not a correctness score.`)
    for (const decision of concept.decisions) {
      lines.push(`- **${decision.field}:** ${decision.proposal}`,
        `  CultureForge rule: ${decision.ruleId}; source IDs: ${decision.evidenceIds.join(', ') || 'none cited'}`)
    }
    lines.push('', '### Cited Qloo sources')
    for (const id of sourceIds) {
      const item = evidence.get(id)
      if (!item) { lines.push(`- ${id}: unavailable in this evidence set; do not treat as verified.`); continue }
      lines.push(`- **${item.label}** — evidence ID: ${id}`,
        `  Qloo identifier: ${item.entityId ?? item.tagId ?? 'not recorded'}; trace: ${item.traceId ?? 'not recorded'}`)
      if (item.location) lines.push(`  Returned location: ${item.location}`)
      if (item.description) lines.push(`  Qloo description: ${item.description}`)
    }
    lines.push('', '### Evidence test')
    if (verdict) {
      lines.push(`Verdict: ${verdict.verdict}`, `Scope: ${verdict.scope}`, `Reason: ${verdict.reason}`,
        `Claim: ${verdict.claim}`, `Falsifier: ${verdict.falsifier}`, `Unproven when: ${verdict.unprovenIf}`,
        `Tested anchor: ${verdict.anchor?.label ?? 'none'}`, `Policy: ${challenge?.policyVersion ?? 'not recorded'}`)
      if (verdict.isCounterfactual) lines.push(`Alternative anchor tested; original reference: ${verdict.originalAnchor?.label ?? 'not recorded'}. The concept was not recomposed.`)
      for (const check of verdict.checks) lines.push(`- ${check.name}: ${check.result} — ${check.detail}`)
    } else lines.push('No verdict has been recorded for this direction.')
    lines.push('', '### Remaining limitations', ...concept.limitations.map((item) => `- ${item}`), '',
      '### Proposed field validation',
      'Ask prospective visitors whether this experience fits a routine they already have. Record reasons to reject the idea before committing to a launch. This is a suggested next experiment, not a Qloo finding.', '')
  }
  lines.push('## Retrieval trace', 'Cached steps report their reuse; timings are not claims about a new upstream request.')
  for (const event of result.trace) {
    lines.push(`- ${event.step}: ${event.status}; workflow: ${event.workflow ?? 'internal step'}; duration: ${event.durationMs == null ? 'not recorded' : `${event.durationMs}ms`}`)
    if (event.correlationId) lines.push(`  Correlation: ${event.correlationId}`)
    if (event.detail) lines.push(`  ${event.detail}`)
  }
  lines.push('', '## Evidence limits', result.notice)
  return lines.join('\n')
}
