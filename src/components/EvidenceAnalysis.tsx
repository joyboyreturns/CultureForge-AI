import type { Concept, Evidence } from '../contracts'
import type { EvidenceAnalysisResult } from '../api'

const STEP_LABEL: Record<string, string> = {
  compare_audiences: 'Compare audiences', rank_anchors: 'Rank another anchor',
  remove_anchor: 'Remove an evidence anchor', investigate_direction: 'Investigate this direction',
  none: 'No next step selected',
}

export function EvidenceAnalysisPanel({ analysis, concepts, evidence, onInspect }: {
  analysis: EvidenceAnalysisResult
  concepts: Concept[]
  evidence: Evidence[]
  onInspect?: (evidenceId: string) => void
}) {
  const conceptById = new Map(concepts.map((concept) => [concept.id, concept]))
  const evidenceById = new Map(evidence.map((item) => [item.id, item]))
  const recommended = analysis.recommendedDirectionId ? conceptById.get(analysis.recommendedDirectionId) : undefined
  return <section className="evidence-analysis panel" aria-label="Evidence analysis">
    <header><div><span className="small-cap">MODEL INTERPRETATION · {analysis.model || 'the configured model'}{analysis.cached ? ' · HELD' : ''}</span>
      <h2>{recommended ? `Most defensible to investigate: ${recommended.name}` : 'No single direction is preferred'}</h2>
      <p>{analysis.recommendationRationale}</p></div></header>
    <p className="analysis-limit">{analysis.limitation}</p>
    <div className="analysis-directions">{analysis.directions.map((direction) => {
      const concept = conceptById.get(direction.directionId)
      const count = analysis.coverage[direction.directionId]
      const confidence = analysis.confidence[direction.directionId] ?? 'Unresolved'
      return <article key={direction.directionId} className="analysis-direction">
        <div className="analysis-direction-title"><span className={`analysis-verdict is-${confidence.toLowerCase()}`}>{confidence}</span><h3>{concept?.name ?? direction.directionId}</h3></div>
        <p><strong>Hypothesis</strong> {direction.hypothesis}</p>
        <div className="analysis-evidence-pair">
          <div><strong>Supports</strong>{direction.supportingEvidenceIds.length ? direction.supportingEvidenceIds.map((id) => <button key={id} onClick={() => onInspect?.(id)}>{evidenceById.get(id)?.label ?? id}</button>) : <span>None cited</span>}</div>
          <div><strong>Potential counterevidence</strong>{direction.challengingEvidenceIds.length ? direction.challengingEvidenceIds.map((id) => <button key={id} onClick={() => onInspect?.(id)}>{evidenceById.get(id)?.label ?? id}</button>) : <span>No potential counterevidence cited</span>}</div>
        </div>
        <p><strong>Assumptions to validate</strong> {direction.assumptions.length ? direction.assumptions.join(' · ') : 'None stated'}</p>
        <p><strong>Alternative explanation</strong> {direction.alternativeExplanation}</p>
        <p><strong>Next validation</strong> {STEP_LABEL[direction.nextStep]} — {direction.nextStepReason}</p>
        <p className="analysis-coverage"><strong>Cited decision coverage</strong> {count?.numerator ?? 0} of {count?.denominator ?? 0} composer decisions have evidence IDs. This measures citation attachment, not whether a claim is true.</p>
      </article>
    })}</div>
    <footer><strong>What could change this conclusion</strong><p>{analysis.whatWouldChangeTheConclusion}</p></footer>
  </section>
}
