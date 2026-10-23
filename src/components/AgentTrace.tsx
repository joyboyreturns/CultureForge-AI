import { useEffect, useRef, useState } from 'react'
import { ArrowRight } from 'lucide-react'
import type { ResearchRun } from '../api'
import { EvidenceDecisionGraph } from './EvidenceDecisionGraph'

/**
 * The live research workspace.
 *
 * This is not an animation of progress. It polls a real run and renders the
 * events the agent actually produced, with the durations and correlation ids
 * the Qloo harness reported. If the agent needs to ask the founder something,
 * the question appears here.
 */
const SLOW_RUN_MS = 30_000

/**
 * A failed run says what kind of failure it was, because the right next step differs: a rate limit or a
 * timeout is the provider being unavailable (the idea and the place are not at fault), a configuration
 * error is not the founder's to fix, and none of them is a statement that a category is unsupported.
 */
const FAILURE: Record<string, { title: string; body: string; retry: boolean }> = {
  RATE_LIMITED: { title: 'Qloo is rate-limiting this key for a moment.', body: 'This is a temporary provider limit, not a finding about your idea or the city. Held evidence is unaffected; a retry after a short wait usually works.', retry: true },
  ALLOWANCE_EXHAUSTED: { title: 'This run used up its request allowance.', body: 'The studio caps how many Qloo requests one run may spend. Nothing was lost; try again or simplify the idea.', retry: true },
  QUOTA_EXHAUSTED: { title: 'The local Qloo allowance is used up for now.', body: 'Ideas whose evidence is already held still open instantly. Others can be tried again when the allowance resets.', retry: true },
  UPSTREAM_TIMEOUT: { title: 'Qloo did not answer in time.', body: 'A timeout says nothing about whether Qloo covers this business or place. Trying again may work.', retry: true },
  RUN_TIMEOUT: { title: 'The run took too long and was stopped.', body: 'Nothing was concluded. Trying again reuses whatever was already fetched.', retry: true },
  PROVIDER_UNAVAILABLE: { title: 'Qloo is not reachable right now.', body: 'Nothing was concluded about your idea. Held evidence is still available; trying again may work.', retry: true },
  UPSTREAM_MALFORMED: { title: 'Qloo sent an answer the studio could not read.', body: 'Nothing was invented to fill the gap. Trying again may work.', retry: true },
  UPSTREAM_UNAUTHENTICATED: { title: 'The studio could not authenticate with Qloo.', body: 'This is a service configuration problem on the server, not something about your idea. It needs the operator.', retry: false },
  UPSTREAM_REJECTED: { title: 'Qloo refused the request.', body: 'This is a service problem rather than a finding about your idea.', retry: false },
  LIVE_DISABLED: { title: 'Live Qloo requests are switched off on this server.', body: 'Only ideas whose evidence is already held can be opened.', retry: false },
  BUDGET_UNAVAILABLE: { title: 'The request allowance could not be read.', body: 'No Qloo request was sent. This is a server problem.', retry: true },
}

export function AgentTrace({ runId, onComplete, onClarify, onGiveUp, onProgress, onRetry, onChangeLocation, onOpenPartial }: {
  runId: string
  onComplete: (result: NonNullable<ResearchRun['result']>) => void
  onClarify: (clarification: NonNullable<ResearchRun['clarification']>) => void
  onGiveUp?: () => void
  onRetry?: () => void
  onChangeLocation?: () => void
  /** Open the initial rule composition now; the run keeps going and offers the full results when it lands. */
  onOpenPartial?: (result: NonNullable<ResearchRun['partialResult']>) => void
  /** How many real steps the agent has taken, so the workspace can show them. */
  onProgress?: (steps: number) => void
}) {
  const [run, setRun] = useState<ResearchRun | null>(null)
  const [error, setError] = useState('')
  const [slow, setSlow] = useState(false)
  const [attempt, setAttempt] = useState(0)
  const settled = useRef(false)

  // Fresh evidence and the model analysis can take a minute or more; say so
  // once a run has been going for longer than half a minute.
  useEffect(() => {
    const timer = window.setTimeout(() => setSlow(true), SLOW_RUN_MS)
    return () => window.clearTimeout(timer)
  }, [runId])

  useEffect(() => {
    let cancelled = false
    let timer: number | undefined
    let failures = 0

    async function poll() {
      try {
        const { fetchResearchRun } = await import('../api')
        const next = await fetchResearchRun(runId)
        if (cancelled) return
        failures = 0
        setError('')
        setRun(next)
        // The steps the agent has really taken, so the workspace above shows
        // the same thing the trace does.
        onProgress?.(next.events?.length ?? 0)
        if (next.status === 'complete' && next.result && !settled.current) {
          settled.current = true
          onComplete(next.result)
          return
        }
        if (next.status === 'clarify' && next.clarification && !settled.current) {
          settled.current = true
          onClarify(next.clarification)
          return
        }
        if (next.status === 'failed' && !settled.current) {
          settled.current = true
          setError(next.error ?? 'The research run could not be completed.')
          return
        }
      } catch (pollError) {
        if (!cancelled) setError(pollError instanceof Error ? pollError.message : 'The research run could not be reached.')
        if (!cancelled && ++failures < 3) timer = window.setTimeout(poll, 2000 * failures)
        return
      }
      if (!cancelled) timer = window.setTimeout(poll, 700)
    }

    poll()
    return () => {
      cancelled = true
      if (timer) window.clearTimeout(timer)
    }
  }, [runId, onComplete, onClarify, onProgress, attempt])

  const events = run?.events ?? []

  return (
    <div className="agent-trace">
      {run?.partialResult && <div className="research-partial"><span className="small-cap">INITIAL ANSWER · ANALYSIS PENDING</span><p>Real retrieved evidence and the initial rule composition. Optional bridge retrieval and model analysis have not finished.</p>{run.timings?.firstEvidenceMs != null && <p>First evidence: {(run.timings.firstEvidenceMs / 1000).toFixed(1)}s{run.timings.firstConceptMs != null ? ` · First concept: ${(run.timings.firstConceptMs / 1000).toFixed(1)}s` : ' · No category-relevant concept yet'}</p>}{onOpenPartial && run.status === 'running' && run.partialResult.concepts.length > 0 && <button className="button button-primary" onClick={() => onOpenPartial(run.partialResult!)}>Open the initial answer now <ArrowRight size={15}/></button>}{run.status === 'running' && run.partialResult.concepts.length === 0 && <p>Qloo returned evidence, but no direction is supported by it so far. The run is checking what else it can learn.</p>}<EvidenceDecisionGraph result={run.partialResult}/></div>}
      {events.length === 0 && !error && (
        <div className="agent-trace-waiting">
          <span className="orange-dot" /> Starting the research run…
        </div>
      )}

      {events.map((event) => (
        <div className="agent-trace-row" key={event.id}>
          <span className={`trace-status is-${event.status}`} />
          <div className="agent-trace-body">
            <strong>{event.step.replace(/-/g, ' ')}</strong>
            <span className="agent-trace-meta">
              {event.workflow && <em>qloo {event.workflow}</em>}
              {event.durationMs != null && <em>{(event.durationMs / 1000).toFixed(1)}s</em>}
              {event.resultCount != null && <em>{event.resultCount} results</em>}
            </span>
            {event.detail && <span className="agent-trace-detail">{event.detail}</span>}
          </div>
        </div>
      ))}

      {slow && !error && run?.status === 'running' && (
        <div className="agent-trace-waiting" role="status">
          <span className="orange-dot" /> Research continues. New evidence and the optional model analysis can take a few minutes. When the initial answer appears above you can open it without waiting for the analysis.
        </div>
      )}

      {error && (() => {
        const kind = run?.status === 'failed' ? FAILURE[run.errorCode ?? ''] : undefined
        return <div className="agent-trace-error" role="alert" data-code={run?.errorCode ?? ''}>
          <strong>{kind?.title ?? (run?.status === 'failed' ? 'The research run could not finish.' : 'The connection was interrupted.')}</strong>
          <span>{kind?.body ?? error}</span>
          {run?.status !== 'failed' && <button className="text-link" onClick={() => { setError(''); setAttempt(value => value + 1) }}>Reconnect to this run</button>}
          {run?.status === 'failed' && (kind?.retry ?? true) && onRetry && <button className="text-link" onClick={onRetry}>Try again <ArrowRight size={13}/></button>}
          {run?.status === 'failed' && onChangeLocation && <button className="text-link" onClick={onChangeLocation}>Change the location <ArrowRight size={13}/></button>}
          {onGiveUp && (
            <button className="text-link" onClick={onGiveUp}>Edit the brief <ArrowRight size={13}/></button>
          )}
        </div>
      })()}

      {run && !error && (
        <div className="agent-trace-foot">
          <span>
            {run.transportRequests} upstream {run.transportRequests === 1 ? 'request' : 'requests'} ·{' '}
            {run.workflowCalls} {run.workflowCalls === 1 ? 'workflow' : 'workflows'}
          </span>
          <em>
            {run.transportRequests === 0
              ? 'No upstream requests recorded so far. Pending steps may require calls.'
              : 'Only what was missing had to be fetched.'}
          </em>
        </div>
      )}
    </div>
  )
}
