import { ArrowRight, Loader2, ShieldCheck } from 'lucide-react'
import type { Concept, GenerateResponse } from '../contracts'
import type { ChallengeResult } from '../api'
import { citationCoverage } from '../evidenceSummary'
import { VerdictBadge } from './Challenge'

/**
 * The answer first, the workbench on request.
 *
 * Everything here is read off the exploration on screen: the directions the
 * rules composed, the places Qloo returned, and the evidence test when it has
 * been run. There is no score. A concept fit number would be one Qloo did not
 * return, and affinity does not measure business fit, so the brief says how
 * well each claim is *cited* and what the test said, and nothing more.
 */
export function ExecutiveBrief({ result, ordered, challenge, challenging, onInspect, onChallenge, onOpenWorkbench }: {
  result: GenerateResponse
  ordered: Concept[]
  challenge?: ChallengeResult | null
  challenging?: boolean
  onInspect?: (evidenceId: string) => void
  onChallenge?: () => void
  onOpenWorkbench: () => void
}) {
  const top = ordered[0]
  if (!top) return null
  const verdictOf = (id: string) => challenge?.directions.find((entry) => entry.directionId === id)
  const anchorOf = (concept: Concept) => concept.evidenceIds.map((id) => result.evidence.find((item) => item.id === id)).find((item) => item?.kind === 'entity')
  const anchors = ordered.slice(0, 3).map((concept) => ({ concept, place: anchorOf(concept) }))
  const lead = anchors.find((entry) => entry.place)?.place
  const cover = citationCoverage(top, result.evidence)
  const topVerdict = verdictOf(top.id)
  const audience = challenge?.profile.demographic
  const tagCount = result.evidence.filter((item) => item.kind === 'tag').length
  const placeCount = result.evidence.filter((item) => item.kind === 'entity').length

  return (
    <section className="exec-brief panel" aria-label="Executive decision brief" data-tour="exec-brief">
      <div className="exec-lead">
        <span className="small-cap">EXECUTIVE DECISION BRIEF · {result.project.businessType.toUpperCase()} · {result.project.location.toUpperCase()}</span>
        <h2>{top.name}</h2>
        <p>{top.tagline}</p>
        <div className="exec-status">
          {topVerdict ? <VerdictBadge verdict={topVerdict.verdict} /> : <span className="exec-untested">Not yet tested against the evidence</span>}
          <span className="exec-cover">{cover.denominator ? `${cover.numerator} of ${cover.denominator} decisions cite returned evidence` : 'No decisions to cite'}</span>
        </div>
        {!challenge && onChallenge && (
          <button className="button button-primary" onClick={onChallenge} disabled={challenging}>
            {challenging ? <><Loader2 size={15} className="spin" /> Testing…</> : <><ShieldCheck size={15} /> Test this against the evidence</>}
          </button>
        )}
      </div>
      <div className="exec-grid">
        <div>
          <span className="tiny-cap">TOP {anchors.length === 1 ? 'ANCHOR' : `${anchors.length} CULTURAL ANCHORS`}</span>
          <ol className="exec-anchors">
            {anchors.map(({ concept, place }) => (
              <li key={concept.id}>
                <strong>{place?.label ?? concept.name}</strong>
                <small>{concept.name}</small>
                {place && onInspect && <button className="evidence-chip" onClick={() => onInspect(place.id)} aria-label={`Open evidence ${place.id}`}>[{place.id}]</button>}
                {verdictOf(concept.id) && <VerdictBadge verdict={verdictOf(concept.id)!.verdict} />}
              </li>
            ))}
          </ol>
        </div>
        <div>
          <span className="tiny-cap">WHO IT IS FOR</span>
          <p className="exec-fact">{result.project.audience}</p>
          {audience && <small>Tested against the profile “{audience}”.</small>}
          <span className="tiny-cap">LEAD PLACE QLOO RETURNED</span>
          <p className="exec-fact">{lead ? lead.label : 'None returned'}</p>
          {lead?.location && <small>{lead.location}</small>}
        </div>
      </div>
      <footer>
        <small>{placeCount} places and {tagCount} audience signals returned by Qloo. Scope: anchor fit within the retrieved sample, not demand, competition or willingness to pay.</small>
        <button className="text-link" onClick={onOpenWorkbench}>Open the evidence workbench <ArrowRight size={14} /></button>
      </footer>
    </section>
  )
}
