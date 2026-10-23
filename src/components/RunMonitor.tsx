import { useEffect, useRef, useState } from 'react'
import { ArrowRight, Check, X } from 'lucide-react'
import type { GenerateResponse, ProjectRequest } from '../contracts'
import type { ClarificationAsk, ResearchRun } from '../api'

/**
 * A research run that keeps going when the reader looks at something else.
 *
 * The run lives on the server; this follows it from outside the workspace
 * screen, so a judge who opens a demo while an exploration is still being
 * researched does not lose it. It says what the agent is really doing (the
 * latest real step and its detail), and when the answer lands it offers to
 * open it rather than pulling the reader off the screen they chose.
 */
type Phase = 'running' | 'ready' | 'clarify' | 'failed'

export function RunMonitor({ runId, project, earlier, onOpen, onReady, onClarify, onWatch, onDismiss }: {
  runId: string
  project: ProjectRequest
  /** True for a run that was set aside when a newer one started. */
  earlier?: boolean
  onReady?: (result: GenerateResponse) => void
  onOpen: (result: GenerateResponse) => void
  onClarify: (ask: ClarificationAsk) => void
  onWatch: () => void
  onDismiss: () => void
}) {
  const [run, setRun] = useState<ResearchRun | null>(null)
  const [phase, setPhase] = useState<Phase>('running')
  const [elapsed, setElapsed] = useState(0)
  const [lost, setLost] = useState(false)
  const result = useRef<GenerateResponse | null>(null)
  const ask = useRef<ClarificationAsk | null>(null)
  const readyCallback = useRef(onReady)
  readyCallback.current = onReady

  useEffect(() => {
    const started = Date.now()
    const tick = window.setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000)
    return () => window.clearInterval(tick)
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
        setRun(next)
        if (next.status === 'complete' && next.result) { result.current = next.result; setPhase('ready'); readyCallback.current?.(next.result); return }
        if (next.status === 'clarify' && next.clarification) { ask.current = next.clarification; setPhase('clarify'); return }
        if (next.status === 'failed') { setPhase('failed'); return }
      } catch {
        // The run is gone from the server (restart, expiry). Say so; do not poll forever.
        if (!cancelled && ++failures >= 3) { setLost(true); setPhase('failed'); return }
      }
      if (!cancelled) timer = window.setTimeout(poll, 900)
    }
    poll()
    return () => { cancelled = true; if (timer) window.clearTimeout(timer) }
  }, [runId])

  const events = run?.events ?? []
  const latest = events[events.length - 1]
  const where = project.location.split(',')[0]
  const title = `${project.businessType} · ${where}`
  const live = phase === 'running'

  return (
    <div className={`run-monitor is-${phase}`} role="status" aria-live="polite">
      <div className="run-monitor-head">
        <span className={`run-monitor-dot ${live ? 'pulse' : ''}`}>{phase === 'ready' && <Check size={11}/>}</span>
        <div>
          <strong>
            {live && (earlier ? 'Still analysing the earlier exploration' : 'Analysing your exploration')}
            {phase === 'ready' && 'Your exploration is ready'}
            {phase === 'clarify' && 'The agent has a question'}
            {phase === 'failed' && (lost ? 'That run is no longer available' : 'The run could not finish')}
          </strong>
          <small>{title}</small>
        </div>
        {!live && <button className="run-monitor-x" aria-label="Dismiss" onClick={onDismiss}><X size={14}/></button>}
      </div>
      {live && (
        <>
          <div className="run-monitor-bar" aria-hidden="true"><span/></div>
          <p className="run-monitor-step">
            {latest
              ? <><b>{latest.step.replace(/-/g, ' ')}</b>{latest.workflow ? ` · qloo ${latest.workflow}` : ''}{latest.detail ? ` — ${latest.detail}` : ''}</>
              : 'Starting the research run…'}
          </p>
          <p className="run-monitor-meta">
            {events.length} {events.length === 1 ? 'step' : 'steps'} so far · {elapsed}s · keep exploring, this continues in the background
          </p>
          {!earlier && <button className="text-link" onClick={onWatch}>Watch it live <ArrowRight size={13}/></button>}
        </>
      )}
      {phase === 'ready' && (
        <button className="run-monitor-primary" onClick={() => result.current && onOpen(result.current)}>Open the results <ArrowRight size={14}/></button>
      )}
      {phase === 'clarify' && (
        <button className="run-monitor-primary" onClick={() => ask.current && onClarify(ask.current)}>Answer it <ArrowRight size={14}/></button>
      )}
      {phase === 'failed' && !lost && <button className="run-monitor-primary" onClick={onWatch}>See what happened <ArrowRight size={14}/></button>}
    </div>
  )
}
