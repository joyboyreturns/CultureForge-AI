import { useState } from 'react'
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
 */
export function AudienceComparison({
  project, currentAudience, alternativeAudience, currentEvidence, onApply, busy,
}: {
  project: ProjectRequest
  currentAudience: string
  alternativeAudience: string
  currentEvidence: Evidence[]
  onApply: (audience: string) => void
  busy?: boolean
}) {
  const [comparison, setComparison] = useState<AudienceComparisonResult | null>(null)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')

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
      const result = await compareAudiences(groupA, groupB)
      setComparison(result)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'The comparison could not be completed.')
    }
    setWorking(false)
  }

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
          <div className="comparison-shared">
            <span className="small-cap">SHARED CULTURAL TAGS</span>
            {comparison.shared.length === 0 && <p className="audience-comparison-note">Qloo found no cultural tag the two groups share.</p>}
            {comparison.shared.map((tag) => (
              <div className="comparison-tag" key={tag.tagId ?? tag.label}>
                <strong>{tag.label}</strong>
                <span className="comparison-score">score {tag.score?.toFixed(4) ?? '—'}</span>
                <span className="comparison-hits">
                  {currentAudience.slice(0, 14)}… {tag.groupAHits ?? 0} · {alternativeAudience.slice(0, 14)}… {tag.groupBHits ?? 0}
                </span>
                <span className="comparison-bar"><i style={{ width: `${Math.min(100, (tag.score ?? 0) * 100)}%` }} /></span>
              </div>
            ))}
          </div>
          <div className="comparison-own">
            <span className="small-cap">WHAT MAKES EACH SIDE ITS OWN</span>
            <div>
              <strong>{currentAudience.slice(0, 26)}</strong>
              <p>{comparison.groupA.slice(0, 6).map((tag) => tag.label).join(', ')}</p>
            </div>
            <div>
              <strong>{alternativeAudience.slice(0, 26)}</strong>
              <p>{comparison.groupB.slice(0, 6).map((tag) => tag.label).join(', ')}</p>
            </div>
          </div>
          <button className="button button-primary" onClick={() => onApply(alternativeAudience)} disabled={busy}>
            Apply this audience
          </button>
        </div>
      )}
    </section>
  )
}
