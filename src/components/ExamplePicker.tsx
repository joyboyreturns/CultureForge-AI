import { useEffect, useState } from 'react'
import { ArrowUpRight, MapPin } from 'lucide-react'
import type { ProjectRequest } from '../contracts'
import { fetchExamples } from '../api'
import type { ExampleBrief } from '../api'
import demoBriefs from '../../shared/demoBriefs.json'

const FEATURED = ['tokyo-morning-bakery', 'paris-ice-cream', 'melbourne-specialty-coffee']

/** The prepared briefs, before the server has said which of them it holds. */
const PREPARED: ExampleBrief[] = demoBriefs.briefs.map((brief) => ({ ...brief, project: brief.project as ProjectRequest, held: false }))

/**
 * The prepared example briefs.
 *
 * These are the briefs `scripts/prewarm.py` fetches ahead of time, so a held
 * one opens from the evidence store without waiting on Qloo. The label says
 * which are held, because a cold one is a real live lookup and can take
 * half a minute or meet a rate limit.
 */
export function ExamplePicker({ onRun }: { onRun: (project: ProjectRequest) => void }) {
  const [examples, setExamples] = useState<ExampleBrief[]>(PREPARED)
  const [known, setKnown] = useState(false)
  const [unchecked, setUnchecked] = useState(false)
  useEffect(() => {
    let live = true
    fetchExamples().then((rows) => { if (live && rows.length) { setExamples(rows); setKnown(true) } })
      // The list still works; it just cannot say what is held, and says so.
      .catch(() => { if (live) setUnchecked(true) })
    return () => { live = false }
  }, [])
  const featured = FEATURED.map((id) => examples.find((example) => example.id === id)).filter((example): example is ExampleBrief => Boolean(example))
  const trials = examples.filter((example) => !FEATURED.includes(example.id))
  const row = (example: ExampleBrief, index?: number) => <li key={example.id}>
    <button type="button" onClick={() => onRun(example.project)} aria-label={`Run the example: ${example.label}, ${example.project.location}`}>
      {index !== undefined && <span className="example-picker-kicker">DEMO {index + 1}</span>}
      <span className="example-picker-title">{example.label}</span>
      <span className="example-picker-meta"><MapPin size={11}/>{example.project.location} · {example.project.businessType}</span>
      {example.trialNote && <span className="example-picker-note">{example.trialNote}</span>}
      <span className={`example-picker-state${example.held ? ' is-held' : ''}`}>{!known ? 'Not checked' : example.held ? 'Qloo evidence held' : 'Live lookup'}</span>
      <ArrowUpRight size={14} aria-hidden="true"/>
    </button>
  </li>
  return <div className="example-picker panel">
    <span className="small-cap"><span className="orange-dot"/> TRY AN IDEA · REAL QLOO EVIDENCE</span>
    <p className="example-picker-note">Open one to see what Qloo returned, where the places are on the map, and what each direction rests on. Then try your own idea. {known ? '' : unchecked ? 'The service could not be reached, so which are held is unknown.' : 'Checking which are held…'}</p>
    <ul className="example-picker-featured">{featured.map((example, index) => row(example, index))}</ul>
    <details className="example-picker-more" open>
      <summary>Browse {trials.length} more trials · all five business categories</summary>
      <p className="example-picker-note">Compare different audiences, cities and business ideas. A supported, contested or unproven result describes the retrieved evidence, not the commercial prospects.</p>
      <ul aria-label="More trial ideas">{trials.map((example) => row(example))}</ul>
    </details>
  </div>
}
