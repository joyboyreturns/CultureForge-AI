import { useEffect, useState } from 'react'
import type { Concept, Evidence, ProjectRequest, TraceEvent } from '../contracts'

/**
 * The provenance inspector.
 *
 * Click any piece of evidence and this shows the call that produced it: which
 * Qloo workflow ran, the exact request that was sent, how long it took, the
 * correlation id, and what came back. Everything here is what Qloo returned.
 * Raw subprocess output is never shown, because it can carry credentials.
 *
 * It also offers the strongest check the app can make: remove this piece of
 * evidence and recompose, with no new call, to see which decisions actually
 * depended on it.
 */
export function ProvenanceDrawer({
  evidence, concepts, trace, evidenceId, project, selection, onClose, onRecomposed,
}: {
  evidence: Evidence[]
  concepts: Concept[]
  trace: TraceEvent[]
  evidenceId: string | null
  project?: ProjectRequest
  /** Which of Qloo's own sentences the model chose to lead with, if it did. */
  selection?: Record<string, { sentences?: string[]; sentenceIds?: string[]; tagIds?: string[] }>
  onClose: () => void
  onRecomposed?: (result: { concepts: Concept[]; evidence: Evidence[]; dropped: number; notice: string }) => void
}) {
  const [removing, setRemoving] = useState(false)
  // A failure is a failure. It is kept in an error state and never reported
  // as a successful recomposition that happened to leave nothing behind.
  const [removalError, setRemovalError] = useState('')
  const [recomposed, setRecomposed] = useState<{ concepts: Concept[]; evidence: Evidence[]; dropped: number; notice: string } | null>(null)
  // The drawer keeps its own copy of the evidence it is showing, so a
  // recomposition that removes that evidence does not close the panel under
  // the reader's feet.
  const [shown, setShown] = useState<Evidence | null>(null)
  useEffect(() => {
    const found = evidence.find((candidate) => candidate.id === evidenceId)
    if (found) setShown(found)
  }, [evidence, evidenceId])
  const item = shown
  if (!evidenceId) return null
  if (!item) return null

  const event = trace.find((candidate) => candidate.id === item.traceId)
  const presentation = item.presentation ?? null
  // The model's choice, when there is one. It can only be a sentence Qloo
  // wrote, so the server's own text is rendered here.
  const chosen = selection?.[item.entityId ?? '']
  const chosenText = chosen?.sentences?.length ? chosen.sentences.join(' ') : ''
  const usedBy = concepts.filter((concept) => concept.evidenceIds.includes(evidenceId))
  const request = event?.request

  const removeAndRecompose = async () => {
    if (!project || !onRecomposed || item.kind !== 'entity') return
    setRemoving(true)
    setRemovalError('')
    try {
      const { recompose } = await import('../api')
      const result = await recompose(project, item.entityId ? [item.entityId] : [])
      setRecomposed(result)
      onRecomposed(result)
    } catch (error) {
      // A failure is a failure. It is not reported as a successful
      // recomposition that happened to leave nothing behind, and the
      // exploration on screen is left as it was.
      setRecomposed(null)
      setRemovalError(error instanceof Error ? error.message : 'The recomposition failed.')
    }
    setRemoving(false)
  }

  return (
    <div className="provenance-backdrop" onClick={onClose} role="presentation">
      <aside className="provenance-drawer" onClick={(event) => event.stopPropagation()} aria-label="Provenance">
        <header>
          <div>
            <span className="small-cap"><span className="orange-dot" /> PROVENANCE</span>
            <h3>{item.label}</h3>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close provenance">✕</button>
        </header>

        <div className="provenance-facts">
          <div><span>KIND</span><strong>{item.kind === 'tag' ? 'Audience seed' : 'Qloo place'}</strong></div>
          {item.entityId && <div><span>ENTITY ID</span><strong className="mono">{item.entityId}</strong></div>}
          {item.tagId && <div><span>TAG URN</span><strong className="mono">{item.tagId}</strong></div>}
          {item.affinity != null && <div><span>AFFINITY</span><strong>{item.affinity.toFixed(4)}</strong></div>}
          {item.popularity != null && <div><span>POPULARITY</span><strong>{item.popularity.toFixed(4)}</strong></div>}
          {item.rating != null && <div><span>LOCAL RATING</span><strong>{Math.round(item.rating * 10) / 10}</strong></div>}
          {item.priceLevel != null && <div><span>PRICE LEVEL</span><strong>{item.priceLevel}</strong></div>}
          {item.location && <div><span>LOCATION</span><strong>{item.location}</strong></div>}
        </div>

        {presentation && (
          <div className="provenance-presentation">
            <span className="small-cap">HOW IT IS PRESENTED</span>
            {presentation.identityNote && <p className="provenance-caveat">{presentation.identityNote}</p>}
            {presentation.locationNote && <p className="provenance-caveat">{presentation.locationNote}</p>}
            {presentation.notes.map((note, index) => (
              <p className="provenance-caveat" key={index}>{note}</p>
            ))}
            {chosenText && (
              <p className="provenance-chosen">
                <b>Chosen from Qloo&rsquo;s own description</b>
                {chosenText}
              </p>
            )}
            {presentation.excerpt && (
              <p className="provenance-excerpt-lead">{presentation.excerpt}</p>
            )}
            {presentation.hasMore && item.description && (
              <p className="provenance-original-label">Qloo&rsquo;s full description</p>
            )}
          </div>
        )}

        {item.description && <p className="provenance-description">{item.description}</p>}

        {event && (
          <div className="provenance-call">
            <span className="small-cap">THE CALL THAT PRODUCED IT</span>
            <div className="provenance-call-head">
              <span className="provenance-workflow">qloo {event.workflow ?? 'workflow'}</span>
              {event.durationMs != null && <span className="provenance-duration">{(event.durationMs / 1000).toFixed(1)}s</span>}
            </div>
            {request && (
              <pre className="provenance-request">{JSON.stringify(request, null, 2)}</pre>
            )}
            {event.correlationId && (
              <div className="provenance-correlation"><span>CORRELATION ID</span><code>{event.correlationId}</code></div>
            )}
            {event.acquiredAt && (
              <div className="provenance-correlation"><span>ACQUIRED</span><code>{new Date(event.acquiredAt).toLocaleString()}</code></div>
            )}
            {event.resultExcerpt && event.resultExcerpt.length > 0 && (
              <div className="provenance-excerpt">
                <span>RETURNED</span>
                <ul>{event.resultExcerpt.map((line, index) => <li key={index}>{line}</li>)}</ul>
              </div>
            )}
          </div>
        )}

        {usedBy.length > 0 && (
          <div className="provenance-uses">
            <span className="small-cap">USED BY</span>
            {usedBy.map((concept) => (
              <div key={concept.id} className="provenance-use">
                <strong>{concept.name}</strong>
                {concept.decisions
                  .filter((decision) => decision.evidenceIds.includes(evidenceId))
                  .map((decision) => <p key={decision.id}><em>{decision.field}</em> {decision.proposal}</p>)}
              </div>
            ))}
          </div>
        )}

        {item.kind === 'entity' && project && onRecomposed && (
          <div className="provenance-removal">
            <span className="small-cap">THE EVIDENCE TEST</span>
            <p>Remove this venue and rebuild the directions from what is left. Qloo is not called again.</p>
            <button className="button button-secondary" onClick={removeAndRecompose} disabled={removing}>
              {removing ? 'Recomposing…' : 'Remove this and recompose'}
            </button>
            {removalError && <p className="provenance-removal-error" role="alert">{removalError}</p>}
            {recomposed && (
              <div className="provenance-recomposed">
                <strong>{recomposed.concepts.length} of {concepts.length} directions survived</strong>
                <span>{recomposed.concepts.map((concept) => concept.name).join(', ') || 'None: every direction lost its support.'}</span>
                <em>{recomposed.notice}</em>
              </div>
            )}
          </div>
        )}
      </aside>
    </div>
  )
}
