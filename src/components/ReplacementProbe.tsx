import { useState } from 'react'
import type { Concept, Evidence, ProjectRequest } from '../contracts'
import type { ReplacementProbeResult } from '../api'

export function ReplacementProbe({ project, directionId, concepts, evidence, resolvedTags }: {
  project: ProjectRequest
  directionId: string
  concepts: Concept[]
  evidence: Evidence[]
  resolvedTags: string[]
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<ReplacementProbeResult | null>(null)

  async function run() {
    setBusy(true); setError(''); setResult(null)
    try {
      const { challengeReplacementProbe } = await import('../api')
      const next = await challengeReplacementProbe(project, directionId, { concepts, evidence, resolvedTags })
      setResult(next)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'The replacement probe could not be completed.')
    } finally { setBusy(false) }
  }

  return <section className="replacement-probe panel" aria-label="Challenge this direction">
    <div className="replacement-probe-heading">
      <div><span className="small-cap">ONE BOUNDED QLOO PROBE</span><h3>What would change my mind?</h3>
        <p>Exclude this direction’s primary cited place, then ask Qloo for replacements under the same audience seeds and location.</p></div>
      <button type="button" onClick={run} disabled={busy || !directionId}>
        {busy ? 'Running probe…' : result ? 'Run again' : 'Challenge this direction'}
      </button>
    </div>
    {error && <div className="replacement-probe-error" role="alert">{error} The current direction and its evidence verdict are unchanged. You can retry.</div>}
    {result && <div className="replacement-probe-result">
      <div className="replacement-probe-meta"><strong>UNRESOLVED</strong><span>{result.cached ? 'Cached Qloo evidence' : 'Fresh Qloo evidence'}</span><span>{result.transportRequests} upstream {result.transportRequests === 1 ? 'request' : 'requests'}</span></div>
      <p><b>Hypothesis:</b> {result.hypothesis}</p>
      <p><b>Observation:</b> {result.observation}</p>
      <p><b>What would challenge it:</b> {result.falsifier}</p>
      <p><b>Excluded place:</b> {result.anchor.label} · {result.anchor.entityId}</p>
      <p><b>Query scope:</b> {result.scope}</p>
      {result.replacements.length > 0
        ? <ul>{result.replacements.map((place) => <li key={place.entityId}>{place.label}{place.entityId ? ` · ${place.entityId}` : ''}</li>)}</ul>
        : <p>No replacement was returned in this bounded response. That does not prove none exist.</p>}
      <p className="replacement-probe-limit">{result.limitations} The concept was not recomposed, and the existing anchor-fit verdict was not changed.</p>
      <details><summary>Qloo request provenance · {result.policyVersion}</summary><pre>{JSON.stringify(result.query, null, 2)}</pre></details>
    </div>}
  </section>
}
