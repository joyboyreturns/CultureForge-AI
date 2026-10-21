import { useEffect, useRef, useState } from 'react'
import { ArrowRight } from 'lucide-react'
import type { ResearchRun } from '../api'

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

    async function poll() {
      try {
        const { fetchResearchRun } = await import('../api')
        const next = await fetchResearchRun(runId)
        if (cancelled) return
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
        return
      }
      if (!cancelled) timer = window.setTimeout(poll, 700)
    }

    poll()
    return () => {
      cancelled = true
      if (timer) window.clearTimeout(timer)
    }
  }, [runId, onComplete, onClarify, onProgress])

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

      {slow && !error && run?.status === 'running' && (
        <div className="agent-trace-waiting" role="status">
          <span className="orange-dot" /> Still processing. The answer is being cooked: new evidence and the AI analysis can take a minute or two.
        </div>
      )}

      {error && (
        <div className="agent-trace-error" role="alert">
          <strong>The research run could not finish.</strong>
          <span>{error}</span>
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
              ? 'Every piece of evidence was already held, so the quota was not touched.'
              : 'Only what was missing had to be fetched.'}
          </em>
        </div>
      )}
    </div>
  )
}
