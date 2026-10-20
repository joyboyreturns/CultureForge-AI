import type { Evidence } from '../contracts'

/**
 * The cultural heat.
 *
 * A heatmap of Qloo's own popularity metric across everything this brief
 * retrieved: the audience seeds and the places returned for them. Popularity
 * is how widely an entity is known, not how well it fits the brief, and the
 * labels say so.
 *
 * The layout is a deterministic grid, not a position on a map. Qloo's geocode
 * carries an address rather than coordinates, so a true geographic map would
 * have to be invented. This one is honest about what it is.
 */
export function CulturalHeat({
  evidence, onInspect,
}: {
  evidence: Evidence[]
  onInspect?: (evidenceId: string) => void
}) {
  const items = evidence.filter((item) => item.popularity != null)
  if (!items.length) {
    return <div className="cultural-heat is-empty"><p>No popularity was returned for this brief, so there is no heat to show.</p></div>
  }

  const seeds = items.filter((item) => item.kind === 'tag')
  const venues = items.filter((item) => item.kind === 'entity')
  const hottest = Math.max(...items.map((item) => item.popularity as number))
  const coldest = Math.min(...items.map((item) => item.popularity as number))
  const span = Math.max(0.0001, hottest - coldest)

  function heat(value: number) {
    // Relative position between the coldest and hottest thing retrieved.
    const relative = (value - coldest) / span
    return 0.16 + relative * 0.72
  }

  function tile(item: Evidence) {
    const value = item.popularity as number
    const intensity = heat(value)
    const isVenue = item.kind === 'entity'
    return (
      <li key={item.id}>
        <button
          type="button"
          className={`heat-tile${isVenue ? ' is-venue' : ' is-seed'}`}
          style={{ '--heat': intensity } as React.CSSProperties}
          onClick={() => { if (isVenue) onInspect?.(item.id) }}
          aria-label={`${item.label}, popularity ${value.toFixed(4)}`}
        >
          <span className="heat-label">{item.label}</span>
          <span className="heat-value">{value.toFixed(3)}</span>
          {item.affinity != null && <span className="heat-affinity">affinity {item.affinity.toFixed(3)}</span>}
        </button>
      </li>
    )
  }

  return (
    <section className="cultural-heat">
      <span className="small-cap"><span className="orange-dot" /> CULTURAL HEAT</span>
      <h3>How hot is each piece of this evidence?</h3>
      <p className="heat-note">
        Qloo’s popularity metric for everything retrieved for this brief. It measures how widely
        a place or a signal is known, not how well it fits your brief. Denser means hotter.
      </p>

      {seeds.length > 0 && (
        <div className="heat-group">
          <span className="small-cap">AUDIENCE SIGNALS</span>
          <ul className="heat-grid">{seeds.map(tile)}</ul>
        </div>
      )}

      {venues.length > 0 && (
        <div className="heat-group">
          <span className="small-cap">PLACES RETURNED</span>
          <ul className="heat-grid">{venues.map(tile)}</ul>
        </div>
      )}

      <div className="heat-scale">
        <span>{coldest.toFixed(3)}</span>
        <i />
        <span>{hottest.toFixed(3)}</span>
        <em>Qloo popularity, 0 to 1</em>
      </div>
    </section>
  )
}
