import type { AgentReport, Concept } from '../contracts'

export function AgentOutcome({ report, concepts }: { report?: AgentReport | null; concepts: Concept[] }) {
  if (!report) return null
  const selected = report.plan?.directionId
    ? concepts.find((item) => item.id === report.plan?.directionId)
    : undefined
  const recommendation = report.reflection?.recommendedDirectionId
    ? concepts.find((item) => item.id === report.reflection?.recommendedDirectionId)
    : undefined
  const result = report.observation?.result ?? {}
  const before = result.before as { name?: string } | undefined
  const after = result.after as { name?: string } | null | undefined
  const model = report.model || 'the configured model'
  return <section className={`agent-outcome panel is-${report.status}`} aria-label="Research agent outcome">
    <header>
      <span className="small-cap">{report.mode === 'frontier_ai' ? `RESEARCH AGENT · ${model}` : 'BOUNDED RESEARCH FALLBACK'}</span>
      <h2>{report.mode === 'frontier_ai'
        ? report.plan?.operation === 'finish' ? 'The agent chose to stop.' : 'The agent tested its own direction.'
        : 'The evidence run is ready.'}</h2>
      <p>{report.mode === 'frontier_ai'
        ? 'It selected one evidence test, ran it against this research run’s held Qloo evidence, and reflected on the result.'
        : report.stoppingReason}</p>
    </header>
    {report.plan && <div className="agent-outcome-plan">
      <span className="small-cap">PLAN · {report.plan.operation.replace('_', ' ').toUpperCase()}</span>
      {selected && <strong>{selected.name}</strong>}
      {report.plan.question && <p>{report.plan.question}</p>}
      <small>{report.plan.reason}</small>
    </div>}
    {report.observation && <div className="agent-outcome-observation">
      <span className="small-cap">TOOL RESULT · {report.observation.upstreamRequests} NEW QLOO REQUESTS</span>
      <p>{report.observation.detail}</p>
      {report.observation.operation === 'remove_anchor' && <small>
        {before?.name ?? selected?.name} → {after?.name ?? 'Direction disappeared'} · held-evidence recomposition; baseline remains unchanged.
      </small>}
    </div>}
    {report.reflection && <div className="agent-outcome-reflection">
      <span className="small-cap">REFLECTION · {report.modelCalls} MODEL REQUEST{report.modelCalls === 1 ? '' : 'S'} · {report.reflection.cached ? `HELD · ${model}` : model}</span>
      <p><strong>{recommendation ? `Most defensible to investigate: ${recommendation.name}. ` : ''}</strong>{report.reflection.recommendationRationale}</p>
      {report.reflection.whatWouldChangeTheConclusion && <small>What could change this: {report.reflection.whatWouldChangeTheConclusion}</small>}
    </div>}
    {report.mode === 'frontier_ai' && <footer>{report.stoppingReason}</footer>}
  </section>
}
