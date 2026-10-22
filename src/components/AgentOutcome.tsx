import type { AgentReport, Concept } from '../contracts'

/**
 * What the research agent did after the rules answered.
 *
 * The loop's steps are listed as they ran: the tool the model chose, why,
 * and what Qloo returned (or why the step was not run). The analysis shows
 * only claims whose every citation is a Qloo entity ID or tag URN observed
 * in this run, with the ones the validator rejected listed beneath, so the
 * reader can see what the check took out.
 */
export function AgentOutcome({ report, concepts }: { report?: AgentReport | null; concepts: Concept[] }) {
  if (!report) return null
  const model = report.model || 'the configured model'
  const steps = report.steps ?? []
  const nameOf = (id?: string | null) => concepts.find((item) => item.id === id)?.name
  // An exploration saved before the loop existed carries the one-step shape.
  if (!steps.length && report.plan) return <LegacyOutcome report={report} concepts={concepts}/>
  const recommended = nameOf(report.analysis?.recommendedDirectionId)
  const ran = steps.filter((step) => step.tool !== 'finish' && step.status === 'ok').length
  return <section className={`agent-outcome panel is-${report.status}`} aria-label="Research agent outcome">
    <header>
      <span className="small-cap">{report.mode === 'frontier_ai' ? `RESEARCH AGENT · ${model}` : 'RESEARCH AGENT · RULES ANSWER STANDS'}{report.cached ? ' · HELD' : ''}</span>
      <h2>{report.mode === 'frontier_ai'
        ? `${ran} evidence step${ran === 1 ? '' : 's'} run, then a cited analysis.`
        : report.status === 'skipped' ? 'The evidence run is ready.' : 'The agent did not change the answer.'}</h2>
      <p>{report.stoppingReason}</p>
    </header>
    {steps.length > 0 && <ol className="agent-steps">
      {steps.map((step) => <li key={step.index} className={`is-${step.status}`}>
        <span className="small-cap">STEP {step.index} · {step.tool.replace('_', ' ').toUpperCase()} · {step.status.toUpperCase()}{step.tool !== 'finish' && step.tool !== 'remove_anchor' ? ` · ${step.cached ? 'HELD' : `${step.upstreamRequests} QLOO REQUEST${step.upstreamRequests === 1 ? '' : 'S'}`}` : ''}</span>
        {step.question && <strong>{step.question}</strong>}
        <p>{step.detail}</p>
        <small>{step.reason}</small>
      </li>)}
    </ol>}
    {report.analysis && <div className="agent-outcome-reflection">
      <span className="small-cap">ANALYSIS · {report.modelCalls} MODEL REQUEST{report.modelCalls === 1 ? '' : 'S'} · EVERY CLAIM CITES QLOO IDS FROM THIS RUN</span>
      <p><strong>{recommended ? `Most defensible to investigate: ${recommended}. ` : ''}</strong>{report.analysis.summary}</p>
      <ul className="agent-claims">
        {report.analysis.claims.map((claim, index) => <li key={index}>
          {claim.statement}
          <span className="agent-citations">{claim.citations.map((citation) => <code key={citation.id} title={citation.id}>{citation.label}</code>)}</span>
        </li>)}
      </ul>
      <small>What could change this: {report.analysis.whatWouldChangeTheConclusion}</small>
    </div>}
    {(report.rejectedClaims?.length ?? 0) > 0 && <details className="agent-rejected">
      <summary>{report.rejectedClaims!.length} claim{report.rejectedClaims!.length === 1 ? '' : 's'} rejected by the citation check</summary>
      <ul>{report.rejectedClaims!.map((claim, index) => <li key={index}><s>{claim.statement}</s> — {claim.reason}</li>)}</ul>
    </details>}
  </section>
}

function LegacyOutcome({ report, concepts }: { report: AgentReport; concepts: Concept[] }) {
  const recommendation = concepts.find((item) => item.id === report.reflection?.recommendedDirectionId)
  return <section className={`agent-outcome panel is-${report.status}`} aria-label="Research agent outcome">
    <header>
      <span className="small-cap">RESEARCH AGENT · {report.model || 'the configured model'} · SAVED BEFORE THE AGENT LOOP</span>
      <h2>{report.plan?.operation === 'finish' ? 'The agent chose to stop.' : 'The agent tested its own direction.'}</h2>
      <p>{report.stoppingReason}</p>
    </header>
    {report.observation && <div className="agent-outcome-observation"><p>{report.observation.detail}</p></div>}
    {report.reflection && <div className="agent-outcome-reflection">
      <p><strong>{recommendation ? `Most defensible to investigate: ${recommendation.name}. ` : ''}</strong>{report.reflection.recommendationRationale}</p>
    </div>}
  </section>
}
