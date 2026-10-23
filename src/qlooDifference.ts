import type { AgentReport, Concept, Evidence, GenerateResponse } from './contracts'
import type { ChallengeResult } from './api'
import { citationCoverage } from './evidenceSummary'

/**
 * What Qloo contributed to the lead direction, read off the exploration on screen.
 *
 * Nothing here is a claim about how a different model would have answered: it
 * lists what this answer rests on that a model without Qloo could not have
 * cited (returned places and audience signals), the extra Qloo workflows the
 * agent chose, and whether anything pushed back on the lead direction. Each
 * line says whether a rule or a model produced it.
 */
export interface QlooStep {
  index: number
  tool: string
  question: string
  returned: number
  source: 'held' | 'fetched'
}

export interface QlooDifference {
  cited: { numerator: number; denominator: number }
  places: number
  signals: number
  steps: QlooStep[]
  notRun: number
  agent: { by: 'model' | 'rules'; model?: string | null; claims: number; rejected: number; stopped: string } | null
  pushback: { kind: 'contested' | 'unproven' | 'reordered' | 'agent-differs' | 'none'; text: string }
}

const TOOL_LABEL: Record<string, string> = {
  find_tags: 'Find tags', recommend: 'Recommend', rank: 'Rank', compare_audiences: 'Compare audiences',
  entity_tags: 'Entity tags', where_popular: 'Where popular', audience_demographics: 'Audience demographics',
  trends: 'Trends', describe: 'Describe', remove_anchor: 'Remove anchor',
}

export const toolLabel = (tool: string) => TOOL_LABEL[tool] ?? tool.replace(/_/g, ' ')

export function qlooDifference(result: GenerateResponse, ordered: Concept[], challenge?: ChallengeResult | null): QlooDifference | null {
  const lead = ordered[0]
  if (!lead) return null
  const evidence: Evidence[] = result.evidence
  const report: AgentReport | null | undefined = result.agent
  const steps = (report?.steps ?? []).filter((step) => step.tool !== 'finish' && step.status === 'ok')
    .map((step): QlooStep => ({ index: step.index, tool: step.tool, question: step.question || step.reason, returned: step.resultCount,
      source: report?.cached || step.cached ? 'held' : 'fetched' }))
  const cover = citationCoverage(lead, evidence)
  const verdict = challenge?.directions.find((entry) => entry.directionId === lead.id)
  const recommended = report?.analysis?.recommendedDirectionId
  const named = (id?: string | null) => ordered.find((concept) => concept.id === id)?.name
  let pushback: QlooDifference['pushback'] = { kind: 'none', text: 'No check has pushed back on the lead direction yet. Run the evidence test to let it.' }
  if (verdict?.verdict === 'contested') pushback = { kind: 'contested', text: `The evidence test contested the lead direction: ${verdict.reason}` }
  else if (verdict?.verdict === 'unproven') pushback = { kind: 'unproven', text: `The evidence test could not prove the lead direction: ${verdict.reason}` }
  else if (result.concepts[0] && result.concepts[0].id !== lead.id) pushback = { kind: 'reordered', text: `The evidence test changed the order: ${lead.name} now leads instead of ${result.concepts[0].name}.` }
  else if (recommended && recommended !== lead.id && named(recommended)) pushback = { kind: 'agent-differs', text: `The agent's cited analysis leans toward ${named(recommended)}, not the lead direction.` }
  else if (verdict) pushback = { kind: 'none', text: 'The evidence test supported the lead direction within the retrieved sample.' }
  // A verdict and a changed order can both be true: say the order moved whatever the verdict was.
  const first = result.concepts[0]
  if (first && first.id !== lead.id && pushback.kind !== 'reordered') pushback = { ...pushback, text: `${pushback.text} The test also changed the order: ${first.name} led before it ran.` }
  return {
    cited: { numerator: cover.numerator, denominator: cover.denominator },
    places: evidence.filter((item) => item.kind === 'entity').length,
    signals: evidence.filter((item) => item.kind === 'tag').length,
    steps,
    notRun: (report?.steps ?? []).filter((step) => step.tool !== 'finish' && step.status !== 'ok').length,
    agent: report ? {
      by: report.mode === 'frontier_ai' ? 'model' : 'rules', model: report.model,
      claims: report.analysis?.claims.length ?? 0, rejected: report.rejectedClaims?.length ?? 0, stopped: report.stoppingReason,
    } : null,
    pushback,
  }
}
