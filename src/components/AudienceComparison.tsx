import { useEffect, useState } from 'react'
import type { AudienceComparisonResult } from '../api'
import type { Evidence, ProjectRequest } from '../contracts'

/**
 * Qloo's own A/B between two audiences.
 *
 * The app's scenario lab can shift a score locally, but that is a model, not a
 * measurement. This asks Qloo to compare the two groups of venues directly and
 * report the cultural tags they share, the comparison score, and how many
 * entities in each side carry each tag. It is the measured version of
 * "what changes when the audience changes".
 *
 * The result belongs to the inputs it was made from. When the alternative
 * audience is edited, the old comparison is not still the comparison of the
 * new one, so it is dropped rather than presented under new words.
 */
/** The family a Qloo tag URN names (urn:tag:genre:qloo:… → genre), for telling same-named tags apart. */
function familyOf(tagId?: string | null) { return tagId?.split(':')[2]?.replace(/_/g, ' ') ?? '' }

export function AudienceComparison({
  project, currentAudience, alternativeAudience, currentEvidence, onApply, busy,
}: {
  project: ProjectRequest
  currentAudience: string
  alternativeAudience: string
  currentEvidence: Evidence[]
  /** Apply the audience that was actually researched, with the answer it
   *  produced — not a second run of the same thing. */
  onApply: (audience: string, alternative: { concepts: unknown[]; evidence: Evidence[]; signals: unknown[]; trace: unknown[]; delivery: unknown; notice: string; resolvedTags: string[] }) => void
  busy?: boolean
}) {
  const [comparison, setComparison] = useState<AudienceComparisonResult | null>(null)
  const [held, setHeld] = useState<{ audience: string; alternative: Parameters<typeof onApply>[1] } | null>(null)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')

  // A comparison is about a specific pair of audiences. Edit the audience
  // and the comparison on screen is no longer the comparison of it.
  useEffect(() => {
    setComparison(null)
    setHeld(null)
    setError('')
  }, [alternativeAudience, currentAudience])

  async function run() {
    setWorking(true); setError('')
    try {
      const { compareAudience, compareAudiences } = await import('../api')
      // Research the alternative audience first, so Qloo has a real second
      // group of entities to compare against.
      const alternative = await compareAudience(project, alternativeAudience)
      const groupA = currentEvidence.filter((item) => item.kind === 'entity' && item.entityId).map((item) => item.entityId as string)
      const groupB = alternative.evidence.filter((item) => item.kind === 'entity' && item.entityId).map((item) => item.entityId as string)
      if (!groupA.length || !groupB.length) {
        setError('Qloo did not return venues for both audiences, so there is nothing to compare.')
        return
      }
      const shared = new Set(groupA.filter((id) => groupB.includes(id)))
      const result = await compareAudiences(groupA, groupB)
      setComparison(result)
      setHeld({ audience: alternativeAudience, alternative: alternative as unknown as Parameters<typeof onApply>[1] })
      if (shared.size) {
        setError('')
        setOverlap(shared.size)
      } else {
        setOverlap(0)
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'The comparison could not be completed.')
    } finally {
      // The controls come back whether the comparison worked or not.
      setWorking(false)
    }
  }

  const [overlap, setOverlap] = useState(0)
  const labelCounts = new Map<string | null, number>()
  for (const tag of comparison?.shared ?? []) labelCounts.set(tag.label, (labelCounts.get(tag.label) ?? 0) + 1)
  const repeated = new Set([...labelCounts].filter(([, count]) => count > 1).map(([label]) => label))

  return (
    <section className="audience-comparison">
      <span className="small-cap"><span className="orange-dot" /> QLOO'S OWN COMPARISON</span>
      <h3>What actually changes when the audience changes?</h3>
      <p className="audience-comparison-note">
        Qloo compares the venues behind “{currentAudience}” with the venues behind
        “{alternativeAudience}”, and reports the cultural tags the two groups share.
      </p>

      <button className="button button-secondary" onClick={run} disabled={working || busy}>
        {working ? 'Asking Qloo…' : 'Compare the two audiences with Qloo'}
      </button>

      {error && <p className="audience-comparison-error" role="alert">{error}</p>}

      {comparison && (
        <div className="audience-comparison-result">
          {overlap > 0 && (
            <p className="audience-comparison-note">
              {overlap} of the venues came back for <em>both</em> audiences. Qloo returned the
              same places for these two signals, so the comparison below is between two groups
              that overlap — it cannot show a difference the retrieval did not produce.
            </p>
          )}
          <div className="comparison-shared">
            {/* Two Qloo tags can share a label (a category and a genre both called "Restaurant"); their family tells them apart. */}
            <span className="small-cap">SHARED CULTURAL TAGS</span>
            {comparison.shared.length === 0 && <p className="audience-comparison-note">No shared tags were returned in this comparison.</p>}
            {comparison.shared.map((tag) => (
              <div className="comparison-tag" key={tag.tagId ?? tag.label}>
                <strong>{tag.label}{tag.label != null && repeated.has(tag.label) && familyOf(tag.tagId) && <small className="comparison-family"> · {familyOf(tag.tagId)}</small>}</strong>
                <span className="comparison-score">score {tag.score?.toFixed(4) ?? '—'}</span>
                <span className="comparison-hits" title={`${currentAudience}: ${tag.groupAHits ?? 'unknown'} · ${alternativeAudience}: ${tag.groupBHits ?? 'unknown'}`}>
                  Current {tag.groupAHits ?? 'unknown'} · Alternative {tag.groupBHits ?? 'unknown'}
                </span>
                <span className="comparison-bar"><i style={{ width: `${Math.min(100, (tag.score ?? 0) * 100)}%` }} /></span>
              </div>
            ))}
          </div>
          <div className="comparison-own">
            <span className="small-cap">WHAT MAKES EACH SIDE ITS OWN</span>
            <div>
              <strong>{currentAudience.slice(0, 26)}</strong>
              <p>{comparison.groupA.slice(0, 6).map((tag) => tag.label).join(', ') || 'No distinguishing tags were returned.'}</p>
            </div>
            <div>
              <strong>{alternativeAudience.slice(0, 26)}</strong>
              <p>{comparison.groupB.slice(0, 6).map((tag) => tag.label).join(', ') || 'No distinguishing tags were returned.'}</p>
            </div>
          </div>
          <button
            className="button button-primary"
            onClick={() => held && onApply(held.audience, held.alternative)}
            disabled={busy || !held}
          >
            Apply this audience
          </button>
        </div>
      )}
    </section>
  )
}
