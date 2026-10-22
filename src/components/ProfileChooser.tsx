import type { ProfileProposal } from '../api'

/**
 * The demographic profile the evidence test ranks against, shown before it
 * runs. When the brief names no demographic, the profile is a default and
 * says so; either way it can be changed. A silent default is a hidden
 * assumption, and the verdict depends on it.
 */
export function ProfileChooser({ proposal, chosen, onChoose, testedWith }: {
  proposal: ProfileProposal | null
  chosen: string
  onChoose: (demographic: string) => void
  /** The profile the verdicts on screen were produced for, if a test has run. */
  testedWith?: string | null
}) {
  if (!proposal) return null
  const note = chosen !== proposal.demographic
    ? 'Chosen by you. The proposal from the brief was “' + proposal.demographic + '”.'
    : proposal.named
      ? 'Proposed by CultureForge from a demographic the brief names.'
      : 'A default: the brief names no demographic. Change it if it is wrong.'
  return <div className="profile-chooser" data-tour="profile">
    <label>
      <span className="small-cap">EVIDENCE TEST PROFILE</span>
      <select value={chosen} onChange={(event) => onChoose(event.target.value)}>
        {proposal.choices.map((choice) => <option key={choice} value={choice}>{choice}</option>)}
      </select>
    </label>
    <p>{note} Qloo ranks the retrieved places against this demographic, not against the audience’s cultural tags. Policy {proposal.policyVersion}.</p>
    {testedWith && testedWith !== chosen && <p className="profile-stale" role="status">The verdicts below were produced for “{testedWith}”, not “{chosen}”. Choose <b>Test the evidence</b> again to rank for “{chosen}”.</p>}
  </div>
}
