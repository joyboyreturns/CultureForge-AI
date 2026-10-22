import { ArrowUpRight } from 'lucide-react'
import type { Evidence, TraceEvent } from '../contracts'
import { bridgeDomain } from '../evidenceSummary'

/**
 * What else this audience gravitates to.
 *
 * The brief's own audience tags, sent to other Qloo domains (artists, films,
 * brands…) with no location. Every row is an entity Qloo returned, in the
 * order it returned them; a domain that was skipped or failed says so.
 */
export function AudienceBridge({ evidence, trace, onInspect }: {
  evidence: Evidence[]
  trace: TraceEvent[]
  onInspect: (evidenceId: string) => void
}) {
  const bridged = evidence.filter((item) => item.kind === 'crossdomain')
  const domains = [...new Set(bridged.map(bridgeDomain))]
  const unanswered = trace.filter((event) => event.step.startsWith('bridge-') && (event.status === 'error' || event.status === 'skipped'))
  return <div className="audience-bridge">
    <p className="source-panel-note">The same audience tags, sent to other Qloo domains with no location. These are audience-level references, not specific to any direction or to the brief’s location; each direction cites them as candidates to test.</p>
    {!bridged.length && !unanswered.length && <p className="source-panel-note">The audience bridge was switched off for this answer, so no other domains were asked.</p>}
    {domains.map((domain) => <section key={domain}>
      <span className="small-cap">QLOO {domain.toUpperCase()} · RETURNED ORDER</span>
      <ul>
        {bridged.filter((item) => bridgeDomain(item) === domain).map((item) => <li key={item.id}>
          <button type="button" onClick={() => onInspect(item.id)} aria-label={`Inspect the source of ${item.label}`}>
            <strong>{item.label}</strong>
            {item.popularity != null && <i>popularity {item.popularity.toFixed(4)}</i>}
            <ArrowUpRight size={13} aria-hidden="true"/>
          </button>
        </li>)}
      </ul>
    </section>)}
    {unanswered.map((event) => <p className="audience-bridge-gap" key={event.id}>{event.detail}</p>)}
  </div>
}
