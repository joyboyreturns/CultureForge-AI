import { useState } from 'react'
import type { TasteSeed } from '../api'

/**
 * Confirmed taste seeds.
 *
 * Before any research runs, the founder sees exactly which Qloo cultural
 * signals their audience description resolved to, and can drop any of them.
 * The research then queries what they confirmed, not what the app guessed.
 */
export function TasteSeeds({
  candidates, audience, onConfirm, onCancel, busy,
}: {
  candidates: TasteSeed[]
  audience: string
  onConfirm: (tagIds: string[]) => void
  onCancel: () => void
  busy?: boolean
}) {
  const [selected, setSelected] = useState<string[]>(candidates.map((candidate) => candidate.tagId))

  function toggle(tagId: string) {
    setSelected((current) =>
      current.includes(tagId) ? current.filter((id) => id !== tagId) : [...current, tagId])
  }

  return (
    <div className="taste-seeds">
      <span className="small-cap"><span className="orange-dot" /> THE AUDIENCE QLOO RESOLVED</span>
      <h3>These are the cultural signals we will query.</h3>
      <p className="taste-seeds-note">
        “{audience}” resolved to {candidates.length} Qloo {candidates.length === 1 ? 'signal' : 'signals'}.
        Drop anything that is not really your audience.
      </p>

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

      <div className="taste-seed-actions">
        <button className="button button-secondary" onClick={onCancel} disabled={busy}>Back</button>
        <button
          className="button button-primary"
          onClick={() => onConfirm(selected)}
          disabled={busy || selected.length === 0}
        >
          {busy ? 'Researching…' : `Research with ${selected.length} ${selected.length === 1 ? 'signal' : 'signals'}`}
        </button>
      </div>
    </div>
  )
}
