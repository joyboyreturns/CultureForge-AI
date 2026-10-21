import { useState } from 'react'
import type { Concept, Evidence, ProjectRequest } from '../contracts'
import { investigate, listFacets } from '../api'
import type { Facet, Investigation } from '../api'
import { GeoMap } from './GeoMap'

/**
 * Investigating a direction.
 *
 * The brief produced three directions. Each one rests on the venues Qloo
 * returned — but also on things nobody has checked: whether interest in that
 * kind of place actually concentrates where the venues are, whether the
 * venues share a cultural signature or only a postcode, who is indexed
 * against the reference place.
 *
 * This panel opens those questions one at a time. Each one is a named Qloo
 * workflow, the answer says which workflow produced it, and the report says
 * what it could not establish. The founder chooses; the agent does not go
 * wandering on its own.
 */
export function Investigation({
  concept, project, evidence, seedTagIds, testedAnchorLabel, onClose,
}: {
  concept: Concept
  project: ProjectRequest
  /** The evidence the direction rests on. The reference is resolved through
   *  it, because the concept cites evidence ids and the workflow needs the
   *  Qloo ids behind them. */
  evidence: Evidence[]
  seedTagIds?: string[]
  /** When the direction has been tested against a different place, that place
   *  is what the investigation has to follow. */
  testedAnchorLabel?: string | null
  onClose: () => void
}) {
  const [facets, setFacets] = useState<Facet[]>([])
  // The founder chooses. Two are offered by default because they answer the
  // biggest uncertainties, and the rest are one click away.
  const [chosen, setChosen] = useState<string[]>(['geography', 'tags'])
  const [report, setReport] = useState<Investigation | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  // The concept cites evidence ids ("ev-entity-5"). The workflow needs the
  // Qloo entity ids behind them. Looking for one inside the other finds
  // nothing, and the investigation then falls back to whichever place
  // happened to be first — which is not the place the direction is about.
  const places = evidence.filter((item) => item.kind === 'entity' && item.entityId)
  const cited = concept.evidenceIds
    .map((id) => places.find((item) => item.id === id))
    .filter((item): item is Evidence => Boolean(item))
  const tested = testedAnchorLabel
    ? places.find((item) => item.label === testedAnchorLabel)
    : undefined
  const referencePlace = tested ?? cited[0] ?? places[0]
  const referenceId = referencePlace?.entityId ?? undefined
  const referenceLabel = referencePlace?.label ?? null
  // The investigation follows *this* direction's places, not every place the
  // brief returned. Asking about venues the direction was not built on
  // answers a different question.
  const entityIds = (cited.length ? cited : places).map((item) => item.entityId as string)

  async function openFacets() {
    try {
      const list = await listFacets()
      setFacets(list.facets)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The questions could not be loaded.')
    }
  }

  function toggle(id: string) {
    setChosen((current) => current.includes(id)
      ? current.filter((value) => value !== id)
      : [...current, id])
  }

  async function run() {
    if (!facets.length) return
    setBusy(true); setError('')
    try {
      const result = await investigate({
        project,
        directionId: concept.id,
        entityIds,
        reference: referenceId,
        within: project.location,
        facets: chosen,
        seedTagIds,
      })
      setReport(result)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The investigation could not finish.')
    }
    setBusy(false)
  }

  return <div className="investigation" role="dialog" aria-label={`Investigate ${concept.name}`}>
    <header className="investigation-head">
      <div>
        <span className="small-cap"><span className="orange-dot"/> INVESTIGATE THIS DIRECTION</span>
        <h3>{concept.name}</h3>
        <p>{concept.tagline}</p>
        {referenceLabel && (
          <p className="investigation-reference">
            Investigating <b>{referenceLabel}</b>
            {tested ? ' — the alternative anchor this direction was last tested against.' : ' — the place this direction is built around.'}
          </p>
        )}
      </div>
      <button className="icon-button" onClick={onClose} aria-label="Close the investigation">✕</button>
    </header>

    {!facets.length && !report && !entityIds.length && (
      <div className="investigation-intro">
        <p>
          This direction does not rest on a place Qloo returned, so there is nothing to
          investigate yet. Run the research again, or close this and pick another direction.
        </p>
      </div>
    )}

    {!facets.length && !report && entityIds.length > 0 && (
      <div className="investigation-intro">
        <p>
          This direction rests on the venues Qloo returned. Three things about it
          have not been checked yet. Open the ones you want answered.
        </p>
        <button className="button button-primary" onClick={openFacets}>Show the open questions</button>
      </div>
    )}

    {facets.length > 0 && !report && (
      <div className="investigation-questions">
        {facets.map((facet) => <label key={facet.id} className={`investigation-facet${chosen.includes(facet.id) ? ' is-on' : ''}`}>
          <input type="checkbox" checked={chosen.includes(facet.id)} onChange={() => toggle(facet.id)}/>
          <span>
            <b>{facet.workflow}</b>
            {facet.question}
          </span>
        </label>)}
        <div className="investigation-actions">
          <button className="button button-primary" onClick={run} disabled={busy || !chosen.length}>
            {busy ? 'Investigating…' : `Investigate ${chosen.length} question${chosen.length === 1 ? '' : 's'}`}
          </button>
          {busy && <span className="scenario-busy">Calling Qloo. The first look takes a few seconds; a second costs nothing.</span>}
        </div>
      </div>
    )}

    {error && <p className="investigation-error" role="alert">{error}</p>}

    {report && <>
      <section className="investigation-report">
        <span className="small-cap">WHAT THE AGENT DID</span>
        <ul className="investigation-tools">
          {report.tools.map((tool) => <li key={tool.facet} className={`is-${tool.status}`}>
            <span className="investigation-tool-workflow">qloo {tool.workflow}</span>
            <span className="investigation-tool-detail">{tool.detail ?? tool.question}</span>
            <span className="investigation-tool-meta">
              {tool.status === 'error' ? 'failed'
                : tool.cached ? 'reused held evidence'
                  : `${tool.resultCount} results · ${tool.durationMs != null ? `${(tool.durationMs / 1000).toFixed(1)}s` : ''}`}
            </span>
          </li>)}
        </ul>
      </section>

      {report.geography && <GeoMap layer={report.geography} label="Where this reference concentrates" />}

      {report.tags && report.tags.length > 0 && (
        <section className="investigation-section">
          <span className="small-cap">THE CULTURAL SIGNATURE</span>
          <div className="investigation-tags">
            {report.tags.map((tag) => <span key={tag.id}>
              <b>{tag.name}</b>
              {tag.affinity != null && <i>affinity {tag.affinity.toFixed(3)}</i>}
            </span>)}
          </div>
          <p className="investigation-note">These concepts characterise the venues Qloo returned for this direction.</p>
        </section>
      )}

      {report.demographics && report.demographics.age && Object.keys(report.demographics.age).length > 0 && (
        <section className="investigation-section">
          <span className="small-cap">DEMOGRAPHIC INDEX FOR THE REFERENCE PLACE</span>
          <div className="investigation-demographics">
            {Object.entries(report.demographics.age).map(([band, value]) => (
              <span key={band} className={Number(value) < 0 ? 'is-under' : 'is-over'}>
                <b>{band.replace(/_/g, ' ')}</b>
                <i>{Number(value) > 0 ? '+' : ''}{Number(value).toFixed(2)}</i>
              </span>
            ))}
          </div>
          <p className="investigation-note">{report.demographics.note} This is an index for one entity, not the composition of your audience.</p>
        </section>
      )}

      {report.findings.length > 0 && (
        <section className="investigation-section">
          <span className="small-cap">WHAT THIS ADDS</span>
          <ul className="investigation-findings">{report.findings.map((finding) => <li key={finding}>{finding}</li>)}</ul>
        </section>
      )}

      {report.limitations.length > 0 && (
        <section className="investigation-section">
          <span className="small-cap">WHAT IT DOES NOT ESTABLISH</span>
          <ul className="investigation-limitations">{report.limitations.map((line) => <li key={line}>{line}</li>)}</ul>
        </section>
      )}

      <footer className="investigation-foot">
        <span>{report.transportRequests} upstream request{report.transportRequests === 1 ? '' : 's'} · {report.investigatedAt.slice(0, 19).replace('T', ' ')}</span>
        <button className="button button-secondary" onClick={() => { setReport(null) }}>Ask something else</button>
      </footer>
    </>}
  </div>
}
