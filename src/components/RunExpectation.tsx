import { useEffect, useState } from 'react'
import { Clock } from 'lucide-react'

/** What to expect from a research run, said before and while it runs. */
export const RUN_TIME_NOTE = 'A new idea is researched live: usually 2–3 minutes for a detailed report, and on rare occasions 5 minutes or more. Ideas whose evidence is already held open in seconds.'

function clock(seconds: number) {
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`
}

/**
 * The reader is told what a run costs in time, and where they are in it. The
 * bar is the typical range, not a progress claim: the steps below are what
 * actually happened.
 */
export function RunExpectation({ runId }: { runId?: string }) {
  const [seconds, setSeconds] = useState(0)
  useEffect(() => {
    setSeconds(0)
    const started = Date.now()
    const timer = window.setInterval(() => setSeconds(Math.floor((Date.now() - started) / 1000)), 1000)
    return () => window.clearInterval(timer)
  }, [runId])
  const typical = Math.min(seconds / 180, 1)
  const phase = seconds < 20 ? 'Gathering Qloo evidence for your idea…'
    : seconds < 180 ? 'Researching places, audience signals and cross-domain taste. This is the usual stretch.'
    : seconds < 300 ? 'Still working. A detailed report can take up to five minutes.'
    : 'This is one of the rare long runs. The research is still going; you can explore other examples meanwhile.'
  return (
    <div className="run-expectation" role="status">
      <div className="run-expectation-head"><Clock size={15} /><strong>Detailed research takes time. Stay with us.</strong><span>{clock(seconds)}</span></div>
      <div className="run-expectation-bar" aria-hidden="true"><span style={{ width: `${typical * 100}%` }} /></div>
      <div className="run-expectation-scale" aria-hidden="true"><small>0</small><small>2–3 min · typical</small><small>5+ min · rare</small></div>
      <p>{phase}</p>
      <p className="run-expectation-note">{RUN_TIME_NOTE} You can open another example while this continues; a card will bring you back when it is ready.</p>
    </div>
  )
}
