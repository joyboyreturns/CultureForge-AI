import type { Evidence } from '../contracts'

/**
 * The places Qloo actually returned, with the photograph Qloo actually
 * returned for them.
 *
 * The concept cards use the same images as inspiration. This strip is the
 * other half of the truth: the raw evidence, with the numbers Qloo measured
 * next to the picture that came with them. Nothing here is styled to look
 * better than it is — the affinity and popularity are printed as Qloo
 * returned them, to four decimal places where they were given.
 *
 * The tidying is done by rule, not by a model. A place Qloo describes as an
 * organisation is marked as one, and it is shown under its own name; a place
 * that came back with the city but not the borough says so; a returned
 * popularity of zero is printed as zero, because it is a real value and not
 * a missing one.
 */
export function PlaceStrip({ evidence, onInspect }: {
  evidence: Evidence[]
  onInspect?: (evidenceId: string) => void
}) {
  // A place without a photograph is still a place Qloo returned. It is shown
  // without one, rather than dropped from the list of the evidence.
  const places = evidence.filter((item) => item.kind === 'entity')
  if (!places.length) return null
  const caveats = places
    .map((place) => place.presentation?.locationNote ?? '')
    .filter((note, index, all) => note && all.indexOf(note) === index)

  return <section data-tour="sources" className="place-strip" aria-label="The places Qloo returned, with the photographs it returned for them">
    <div className="place-strip-head">
      <span className="small-cap"><span className="orange-dot"/> THE PLACES QLOO RETURNED</span>
      <span className="sample-label">QLOO PHOTOGRAPHY &amp; MEASUREMENTS</span>
    </div>
    <ul className="place-strip-rail">
      {places.map((place) => (
        <li key={place.id} className={place.presentation?.identity === 'organisation' ? 'is-organisation' : undefined}>
          <figure>
            {place.image
              ? <img src={place.image} alt={`Photograph Qloo returned for ${place.label}`} loading="lazy" />
              : <span className="place-strip-no-image" aria-hidden="true">NO PHOTOGRAPH RETURNED</span>}
            <figcaption>
              <b>{place.label}</b>
              {place.location && <span>{place.location}</span>}
              {place.presentation?.identity === 'organisation' && (
                <span className="place-strip-kind">ORGANISATION</span>
              )}
            </figcaption>
          </figure>
          <div className="place-strip-metrics">
            {place.affinity != null && <span>affinity {place.affinity.toFixed(4)}</span>}
            {place.popularity != null && <span>popularity {place.popularity.toFixed(4)}</span>}
            {place.rating != null && <span>rated {place.rating.toFixed(1)}</span>}
            {onInspect && (
              <button type="button" className="place-strip-inspect" onClick={() => onInspect(place.id)}>
                trace
              </button>
            )}
          </div>
        </li>
      ))}
    </ul>
    <p className="place-strip-note">
      Every frame above was served by Qloo for this audience and this location. The
      numbers are Qloo&rsquo;s own affinity, popularity and rating — not a fit score
      for your business.
      {caveats.length > 0 && ` ${caveats[0]}`}
    </p>
  </section>
}
