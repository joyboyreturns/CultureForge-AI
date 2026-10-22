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

export function AgentTrace({ runId, onComplete, onClarify, onGiveUp, onProgress }: {
  runId: string
  onComplete: (result: NonNullable<ResearchRun['result']>) => void
  onClarify: (clarification: NonNullable<ResearchRun['clarification']>) => void
  onGiveUp?: () => void
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
      {run?.partialResult && <div className="research-partial"><span className="small-cap">INITIAL ANSWER · ANALYSIS PENDING</span><p>Real retrieved evidence and the initial rule composition. Optional bridge retrieval and model analysis have not finished.</p>{run.timings?.firstEvidenceMs != null && <p>First evidence: {(run.timings.firstEvidenceMs / 1000).toFixed(1)}s{run.timings.firstConceptMs != null ? ` · First concept: ${(run.timings.firstConceptMs / 1000).toFixed(1)}s` : ' · No category-relevant concept yet'}</p>}<EvidenceDecisionGraph result={run.partialResult}/></div>}
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
          <span className="orange-dot" /> Research continues. New evidence and the optional model analysis can take a few minutes. You can inspect the initial answer above as soon as it is ready.
        </div>
      )}

      {error && (
        <div className="agent-trace-error" role="alert">
          <strong>{run?.status === 'failed' ? 'The research run could not finish.' : 'The connection was interrupted.'}</strong>
          <span>{error}</span>
          {run?.status !== 'failed' && <button className="text-link" onClick={() => { setError(''); setAttempt(value => value + 1) }}>Reconnect to this run</button>}
          {onGiveUp && (
            <button className="text-link" onClick={onGiveUp}>Back to the brief <ArrowRight size={13}/></button>
          )}
        </div>
      )}

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
