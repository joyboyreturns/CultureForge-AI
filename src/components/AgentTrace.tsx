import { useEffect, useRef, useState } from 'react'
import type { ResearchRun } from '../api'

/**
 * The live research workspace.
 *
 * This is not an animation of progress. It polls a real run and renders the
 * events the agent actually produced, with the durations and correlation ids
 * the Qloo harness reported. If the agent needs to ask the founder something,
 * the question appears here.
 */
export function AgentTrace({ runId, onComplete, onClarify }: {
  runId: string
  onComplete: (result: NonNullable<ResearchRun['result']>) => void
  onClarify: (clarification: NonNullable<ResearchRun['clarification']>) => void
}) {
  const [run, setRun] = useState<ResearchRun | null>(null)
  const [error, setError] = useState('')
  const settled = useRef(false)

  useEffect(() => {
    let cancelled = false
    let timer: number | undefined

    async function poll() {
      try {
        const { fetchResearchRun } = await import('../api')
        const next = await fetchResearchRun(runId)
        if (cancelled) return
        setRun(next)
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
        return
      }
      if (!cancelled) timer = window.setTimeout(poll, 700)
    }

    poll()
    return () => {
      cancelled = true
      if (timer) window.clearTimeout(timer)
    }
  }, [runId, onComplete, onClarify])

  const events = run?.events ?? []

  return (
    <div className="agent-trace">
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

      {error && <div className="agent-trace-error" role="alert">{error}</div>}

      {run && !error && (
        <div className="agent-trace-foot">
          <span>
            {run.transportRequests} upstream {run.transportRequests === 1 ? 'request' : 'requests'} ·{' '}
            {run.workflowCalls} {run.workflowCalls === 1 ? 'workflow' : 'workflows'}
          </span>
          <em>
            {run.transportRequests === 0
              ? 'Every piece of evidence was already held, so the quota was not touched.'
              : 'Only what was missing had to be fetched.'}
          </em>
        </div>
      )}
    </div>
  )
}
