import type { BusinessIntent, IntentEvidence } from '../contracts'
import { intentIsWorthShowing, STATE_LABEL } from '../intentView'

/**
 * How the idea was read, and what Qloo returned for each business in it.
 *
 * Counts here are counts of places Qloo returned. Nothing on this panel is a score, and a business
 * without evidence says so instead of borrowing another business's.
 */
const CLASS_LABEL: Record<string, string> = {
  direct_business: 'matching business', indirect_business: 'related business', cultural_attraction: 'attraction',
  audience_affinity: 'audience affinity', unverified_geography: 'other location', unrelated: 'not matching',
}

function Stream({ entry }: { entry: IntentEvidence }) {
  const good = entry.state === 'exact' || entry.state === 'near'
  return <li className={`intent-stream is-${entry.state}`} data-state={entry.state}>
    <div className="intent-stream-head">
      <strong>{entry.phrase}</strong>
      <span className={`intent-state ${good ? 'is-good' : entry.state === 'broader' ? 'is-warn' : 'is-limit'}`}>{STATE_LABEL[entry.state]}</span>
    </div>
    <p className="intent-stream-detail">
      {entry.tag && <>Qloo tag: <em>{entry.tag.name ?? entry.tag.id}</em>. </>}
      {entry.placeCount > 0
        ? <>{entry.placeCount} {entry.placeCount === 1 ? 'place' : 'places'} returned{entry.directCount > 0 ? `, ${entry.directCount} matching the business by their own text` : ', none matching the business by their own text'}.</>
        : null}
      {entry.modifiers.map(check => <span key={check.word}> “{check.word}” is mentioned by {check.mentionedIn} of {check.of} returned places.</span>)}
      {entry.message && <> {entry.message}</>}
    </p>
    {entry.places.length > 0 && <details className="intent-places">
      <summary>Places returned for {entry.phrase}</summary>
      <ul>{entry.places.slice(0, 6).map(place => <li key={place.entityId ?? place.name}>{place.name}<small>{place.evidenceClass ? CLASS_LABEL[place.evidenceClass] ?? place.evidenceClass : 'unclassified'}{place.location ? ` · ${place.location}` : ''}</small></li>)}</ul>
    </details>}
  </li>
}

export function IntentSummary({ intent, location }: { intent?: BusinessIntent | null; location: string }) {
  if (!intentIsWorthShowing(intent)) return null
  return <section className="intent-summary panel" aria-label="How your idea was read" data-testid="intent-summary">
    <header>
      <span className="small-cap">HOW YOUR IDEA WAS READ</span>
      {intent.source === 'model' && <em className="intent-source">model-assisted reading, validated; Qloo still chose every tag</em>}
    </header>
    <dl className="intent-facts">
      <div><dt>Your idea</dt><dd>{intent.original}</dd></div>
      <div><dt>{intent.hybrid ? 'Businesses' : 'Business'}</dt><dd>{intent.components.map(component => component.phrase).join(' + ')}</dd></div>
      {intent.components.some(component => component.modifiers.length > 0) && <div><dt>Specialisation</dt><dd>{[...new Set(intent.components.flatMap(component => component.modifiers))].join(', ')}</dd></div>}
      <div><dt>Location</dt><dd>{location}</dd></div>
    </dl>
    <ul className="intent-streams">{intent.evidence.map(entry => <Stream key={`${entry.role}-${entry.phrase}`} entry={entry} />)}</ul>
    {intent.overlap && <p className={`intent-overlap ${intent.overlap.established ? 'is-established' : ''}`} role="status">{intent.overlap.statement}</p>}
    {intent.substitutions.length > 0 && <div className="intent-notes"><strong>Simplified or not verified</strong>
      <ul>{intent.substitutions.map(line => <li key={line}>{line}</li>)}</ul></div>}
  </section>
}
