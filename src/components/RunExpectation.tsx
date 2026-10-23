import { useEffect, useState } from 'react'
import { Clock } from 'lucide-react'

/** What to expect from a research run, said before and while it runs. */
export const RUN_TIME_NOTE = 'First evidence opens automatically when available. Research continues in the background, with real progress in a floating card. The preview updates when the full report is ready. Held evidence avoids a new Qloo request.'

function clock(seconds: number) {
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`
}

/**
 * The clock reports elapsed time; actual steps are shown in the trace.
 * No elapsed-time estimate is presented as completed work.
 */
export function RunExpectation({ runId }: { runId?: string }) {
  const [seconds, setSeconds] = useState(0)
  useEffect(() => {
    setSeconds(0)
    const started = Date.now()
    const timer = window.setInterval(() => setSeconds(Math.floor((Date.now() - started) / 1000)), 1000)
    return () => window.clearInterval(timer)
  }, [runId])
  return (
    <div className="run-expectation" role="status">
      <div className="run-expectation-head"><Clock size={15} /><strong>Live research · evidence appears as it arrives</strong><span>{clock(seconds)}</span></div>
      <p className="run-expectation-note">{RUN_TIME_NOTE} You can open another example while this continues; a card will bring you back when it is ready.</p>
    </div>
  )
}
