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
 */
export function PlaceStrip({ evidence, onInspect }: {
  evidence: Evidence[]
  onInspect?: (evidenceId: string) => void
}) {
  const places = evidence.filter((item) => item.kind === 'entity' && item.image)
  if (!places.length) return null

  return <section className="place-strip" aria-label="The places Qloo returned, with the photographs it returned for them">
    <div className="place-strip-head">
      <span className="small-cap"><span className="orange-dot"/> THE PLACES QLOO RETURNED</span>
      <span className="sample-label">QLOO PHOTOGRAPHY &amp; MEASUREMENTS</span>
    </div>
    <ul className="place-strip-rail">
      {places.map((place) => (
        <li key={place.id}>
          <figure>
            <img src={place.image!} alt={`Photograph Qloo returned for ${place.label}`} loading="lazy" />
            <figcaption>
              <b>{place.label}</b>
              {place.location && <span>{place.location}</span>}
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
    </p>
  </section>
}
