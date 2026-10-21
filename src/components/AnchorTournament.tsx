import { useState } from 'react'
import type { AnchorRanking } from '../api'
import type { Evidence } from '../contracts'

/**
 * The anchor tournament.
 *
 * Qloo returned several real places for this brief. Which one should the
 * business actually be built around? That is a ranking question, so it is
 * asked of Qloo rather than guessed at: the `rank` workflow compares the
 * places against a documented demographic signal near the brief's location,
 * and returns an affinity for each.
 *
 * The demographic phrase is turned into Qloo's own age and gender signals by
 * Qloo. Those converted signals are shown afterwards, taken from the request
 * Qloo actually sent, so the founder can see the measurement rather than
 * trust a paraphrase.
 */

interface Choice {
  label: string
  demographic: string
  note: string
}

/** The demographics Qloo's documented mapping understands. */
const CHOICES: Choice[] = [
  { label: 'Gen Z', demographic: 'gen z', note: '24 and younger' },
  { label: 'Young adults', demographic: 'young adults', note: '24 to 29' },
  { label: 'Millennials', demographic: 'millennials', note: '30 to 44' },
  { label: 'Men 25–34', demographic: 'men 25-34', note: 'male, 25 to 34' },
  { label: 'Women 25–34', demographic: 'women 25-34', note: 'female, 25 to 34' },
  { label: 'Seniors', demographic: 'seniors', note: '55 and older' },
]

/**
 * CultureForge's reading of the founder's own words, used only to preselect a
 * demographic. Qloo does the actual conversion, and the converted signal is
 * what gets shown.
 */
function guessDemographic(audience: string): string {
  const text = audience.toLowerCase()
  if (/\bgen[\s-]?z\b|teen/.test(text)) return 'gen z'
  if (/\bmillennial/.test(text)) return 'millennials'
  if (/\bwomen\b|\bfemale\b/.test(text)) return /\b(3\d|4\d)\b/.test(text) ? 'women 35-44' : 'women 25-34'
  if (/\bmen\b|\bmale\b/.test(text)) return /\b(3\d|4\d)\b/.test(text) ? 'men 35-44' : 'men 25-34'
  if (/\byoung\b/.test(text)) return 'young adults'
  if (/\bsenior|elderly|retire/.test(text)) return 'seniors'
  return 'millennials'
}

export function AnchorTournament({
  evidence, audience, location,
}: {
  evidence: Evidence[]
  audience: string
  location: string
}) {
  const venues = evidence.filter((item) => item.kind === 'entity' && item.entityId)
  const options = venues.map((item) => item.entityId as string)

  const guess = guessDemographic(audience)
  const [choice, setChoice] = useState(() => CHOICES.find((entry) => entry.demographic === guess)?.demographic ?? 'millennials')
  const [ranking, setRanking] = useState<AnchorRanking | null>(null)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')

  async function run() {
    if (!options.length) return
    setWorking(true); setError('')
    try {
      const { rankAnchors } = await import('../api')
      const result = await rankAnchors(options, location, choice)
      setRanking(result)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'The ranking could not be completed.')
    }
    setWorking(false)
  }

  if (!options.length) {
    return (
      <div className="anchor-tournament is-empty">
        <p>No places were returned for this brief, so there is nothing to rank.</p>
      </div>
    )
  }

  const chosen = CHOICES.find((entry) => entry.demographic === choice)
  const signals = ranking?.signalsUsed ?? {}

  return (
    <section className="anchor-tournament">
      <span className="small-cap"><span className="orange-dot" /> THE ANCHOR TOURNAMENT</span>
      <h3>Which of these places ranks highest for that profile?</h3>
      <p className="anchor-note">
        Qloo returned {options.length} places for this brief. Its own <code>rank</code> workflow
        orders them for one demographic profile near {location} — an ordering under those inputs,
        not a decision about which one you should build around.
      </p>

      <div className="anchor-choices" role="radiogroup" aria-label="Audience demographic">
        {CHOICES.map((entry) => (
          <button
            key={entry.demographic}
            type="button"
            role="radio"
            aria-checked={entry.demographic === choice}
            className={`anchor-choice${entry.demographic === choice ? ' is-on' : ''}`}
            onClick={() => { setChoice(entry.demographic); setRanking(null) }}
          >
            <b>{entry.label}</b>
            <i>{entry.note}</i>
          </button>
        ))}
      </div>

      <button className="button button-primary" onClick={run} disabled={working}>
        {working ? 'Asking Qloo…' : 'Rank the anchors with Qloo'}
      </button>

      {error && <p className="anchor-error" role="alert">{error}</p>}

      {ranking && (
        <div className="anchor-result">
          <ol className="anchor-list">
            {ranking.ranked.map((row) => (
              <li key={row.entityId ?? row.position}>
                <span className="anchor-position">{row.position}</span>
                <div className="anchor-body">
                  <strong>{row.label ?? 'Unnamed place'}</strong>
                  <span className="anchor-bar">
                    <i style={{ width: `${Math.min(100, (row.affinity ?? 0) * 100)}%` }} />
                  </span>
                  <span className="anchor-metrics">
                    affinity {row.affinity?.toFixed(4) ?? '—'}
                    {row.popularity != null && <> · popularity {row.popularity.toFixed(4)}</>}
                  </span>
                </div>
              </li>
            ))}
          </ol>

          <div className="anchor-signals">
            <span className="small-cap">THE SIGNAL QLOO ACTUALLY SENT</span>
            <pre>{JSON.stringify(signals, null, 2)}</pre>
            <p>
              “{chosen?.label}” was converted by Qloo into {chosen?.note.toLowerCase()}.
              {ranking.trace.durationMs != null && <> The call took {(ranking.trace.durationMs / 1000).toFixed(1)}s.</>}
            </p>
          </div>
        </div>
      )}
    </section>
  )
}
