import { RUN_TIME_NOTE } from './RunExpectation'
import type { TasteSeed } from '../api'

/**
 * Confirmed taste seeds.
 *
 * Before any research runs, the founder sees exactly which Qloo cultural
 * signals their audience description resolved to, and can drop any of them.
 * The research then queries what they confirmed, not what the app guessed.
 */
export function TasteSeeds({
  candidates, audience, selected, onChange, onConfirm, onCancel, busy,
}: {
  candidates: TasteSeed[]
  audience: string
  /** The founder's current choice. It lives outside this component, so a
      clarification that sends them back to the brief does not wipe it. */
  selected: string[]
  onChange: (tagIds: string[]) => void
  onConfirm: (tagIds: string[]) => void
  onCancel: () => void
  busy?: boolean
}) {
  function toggle(tagId: string) {
    onChange(selected.includes(tagId)
      ? selected.filter((id) => id !== tagId)
      : [...selected, tagId])
  }

  return (
    <div className="taste-seeds">
      <span className="small-cap"><span className="orange-dot" /> THE AUDIENCE QLOO RESOLVED</span>
      <h3>{candidates.length ? 'These are the cultural signals we will query.' : 'Your audience did not resolve into signals.'}</h3>
      <p className="taste-seeds-note">
        {candidates.length
          ? `“${audience}” resolved to ${candidates.length} Qloo ${candidates.length === 1 ? 'signal' : 'signals'}. Drop anything that is not really your audience.`
          : `Qloo did not match “${audience}” to a cultural signal. Describe the audience by what they do or care about — or let the agent resolve it from the brief and the neighborhood.`}
      </p>

      {candidates.length === 0 && (
        <div className="taste-seed-empty">
          <p>
            The research agent can still run: it resolves the audience from the brief and the
            places Qloo returns for the location, and says what it found.
          </p>
        </div>
      )}

      <ul className="taste-seed-list">
        {candidates.map((candidate) => {
          const on = selected.includes(candidate.tagId)
          return (
            <li key={candidate.tagId}>
              <button
                type="button"
                className={`taste-seed${on ? ' is-on' : ''}`}
                aria-pressed={on}
                onClick={() => toggle(candidate.tagId)}
              >
                <b>{candidate.label}</b>
                {candidate.popularity != null && (
                  <i>popularity {candidate.popularity.toFixed(3)}</i>
                )}
                <code>{candidate.tagId}</code>
              </button>
            </li>
          )
        })}
      </ul>

      <p className="taste-seed-time">{RUN_TIME_NOTE}</p>
      <div className="taste-seed-actions">
        <button className="button button-secondary" onClick={onCancel} disabled={busy}>Back</button>
        <button
          className="button button-primary"
          onClick={() => onConfirm(selected)}
          disabled={busy || (candidates.length > 0 && selected.length === 0)}
        >
          {busy
            ? 'Researching…'
            : candidates.length === 0
              ? 'Let the agent resolve it'
              : `Research with ${selected.length} ${selected.length === 1 ? 'signal' : 'signals'}`}
        </button>
      </div>
    </div>
  )
}
