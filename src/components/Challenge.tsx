import { useState } from 'react'
import type { ChallengeResult, ChallengedDirection, Verdict } from '../api'

/**
 * The verdict.
 *
 * A direction that came out of the composer is a hypothesis. This is where it
 * meets the evidence again: the audience's pull toward the place it is built
 * on, and whether that place brings a cultural signal the neighbourhood does
 * not already have.
 *
 * The vocabulary is deliberately narrow. The verdict says whether the
 * *audience–anchor fit* holds, and it says so next to the badge: it does not
 * measure demand, profitability, footfall, or commercial viability, and it
 * says nothing about the business as a business. It is a consistency check
 * against the same retrieved evidence, not an independent validation of it.
 *
 * Every direction states its claim, what would contradict it, and what would
 * leave it unproven, before the verdict is read. And the anchor can be
 * changed: the same direction, held to a different place, is a different
 * claim, and the answer follows. A verdict that changes when its assumption
 * changes is showing its sensitivity, not proving itself right.
 */

const VERDICT_WORDS: Record<Verdict, string> = {
  supported: 'Anchor fit supported',
  contested: 'Anchor fit contested',
  unproven: 'Unproven',
}

const VERDICT_NOTES: Record<Verdict, string> = {
  supported: 'It passes the checks that could be run, within the evidence that was retrieved.',
  contested: 'The evidence contradicts a specific premise, and the premise is named.',
  unproven: 'There was not enough retrieved evidence to say either way.',
}

const BOUNDARY = 'Local cultural fit only — not demand, profitability, footfall, or commercial viability.'

/** What a direction looked like before the anchor was changed. */
export interface VerdictStep {
  anchor: string | null
  verdict: Verdict
  rank: number
  at: string
}

export function VerdictBadge({ verdict }: { verdict: Verdict }) {
  return <span className={`verdict-badge is-${verdict}`} title={VERDICT_NOTES[verdict]}>
    <span className="verdict-dot" />{VERDICT_WORDS[verdict]}
  </span>
}

export function ChallengePanel({ challenge, onReanchor, onClose, history, savedAt }: {
  challenge: ChallengeResult
  /** Hold a direction to a different anchor and re-run the check. */
  onReanchor?: (directionId: string, anchorEntityId: string) => void
  onClose: () => void
  /** What each direction looked like before its anchor was changed. */
  history?: Record<string, VerdictStep[]>
  /** Set when this is a saved result rather than a fresh test. */
  savedAt?: string | null
}) {
  const [open, setOpen] = useState<string | null>(challenge.directions[0]?.directionId ?? null)
  const contested = challenge.directions.filter((entry) => entry.verdict === 'contested')

  return (
    <section className="challenge-panel">
      <div className="challenge-head">
        <div>
          <span className="small-cap"><span className="orange-dot" /> TESTED AGAINST THE EVIDENCE</span>
          <h3>{challenge.summary}</h3>
          <p className="challenge-what">{challenge.whatThisIs}</p>
          <p className="challenge-policy">
            Policy <code>{challenge.policyVersion}</code> · scope: {challenge.scope}
            {savedAt ? <> · saved result from {savedAt}</> : null}
          </p>
        </div>
        <button className="icon-button" onClick={onClose} aria-label="Close the evidence test">
          <X />
        </button>
      </div>

      {contested.length > 0 && (
        <div className="challenge-reversal">
          <strong>The evidence moved {contested.length === 1 ? 'one direction' : `${contested.length} directions`}.</strong>
          <p>
            {contested.map((entry) => entry.name).join(', ')} did not survive the test, so the
            order below is the one the evidence leaves — not the one the first pass produced.
          </p>
        </div>
      )}

      <ul className="challenge-list">
        {challenge.directions.map((entry, index) => (
          <li key={entry.directionId} className={`challenge-item is-${entry.verdict}`}>
            <button className="challenge-item-head" onClick={() => setOpen(open === entry.directionId ? null : entry.directionId)}
              aria-expanded={open === entry.directionId}>
              <span className="challenge-rank">{String(index + 1).padStart(2, '0')}</span>
              <span className="challenge-name">{entry.name}</span>
              <VerdictBadge verdict={entry.verdict} />
            </button>
            <p className="challenge-reason">{entry.reason}</p>
            <p className="challenge-boundary">{BOUNDARY}</p>

            {(history?.[entry.directionId]?.length ?? 0) > 0 && (
              <p className="challenge-history">
                {(history?.[entry.directionId] ?? []).map((step) =>
                  `${step.anchor} — ${step.verdict} (${step.rank}${step.rank === 1 ? 'st' : step.rank === 2 ? 'nd' : 'rd'})`).join('  →  ')}
                {'  →  '}
                <strong>{entry.anchor?.label} — {entry.verdict} ({index + 1}{index === 0 ? 'st' : index === 1 ? 'nd' : 'rd'})</strong>
              </p>
            )}

            {entry.alternatives.length > 0 && (
              <div className="challenge-alternatives">
                <span>TEST AGAINST ANOTHER PLACE</span>
                <div>
                  {entry.alternatives.map((alternative) => (
                    <button key={alternative.entityId ?? ''} onClick={() =>
                      onReanchor?.(entry.directionId, alternative.entityId ?? '')}
                      title="Re-run the same claim against this place">
                      {alternative.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {open === entry.directionId && (
              <div className="challenge-detail">
                <div className="challenge-claim">
                  <span>THE CLAIM</span>
                  <p>{entry.claim}</p>
                  <span>IT WOULD BE CONTRADICTED IF</span>
                  <p>{entry.falsifier}</p>
                  <span>IT WOULD BE UNPROVEN IF</span>
                  <p>{entry.unprovenIf}</p>
                </div>
                {entry.checks.map((check) => (
                  <div key={check.name} className={`challenge-check is-${check.result}`}>
                    <span className="challenge-check-result">{check.result === 'pass' ? 'PASS' : check.result === 'fail' ? 'FAIL' : 'MIXED'}</span>
                    <div>
                      <strong>{check.name}</strong>
                      <p>{check.detail}</p>
                    </div>
                  </div>
                ))}
                <p className="challenge-coverage">
                  {entry.coverage.note}
                  {entry.coverage.howSignalsWereCounted ? ' ' + entry.coverage.howSignalsWereCounted : ''}
                </p>
                <p className="challenge-coverage">
                  Judged on {entry.coverage.venuesRetrieved} places Qloo returned, {entry.coverage.venuesCited} of
                  which this direction cites, against {entry.coverage.tagsUsed} cultural signals and the
                  “{challenge.profile.demographic}” profile near {challenge.profile.location}.
                </p>
              </div>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}

/** A small X, so this file does not need the whole icon set. */
function X() {
  return <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
    <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.4" />
  </svg>
}
