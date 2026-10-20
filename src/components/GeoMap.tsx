import { useMemo, useState } from 'react'

/**
 * The geographic interest plot.
 *
 * Qloo's `where_popular` workflow returns geographic cells — a latitude, a
 * longitude, an affinity and a popularity — for the places where one entity
 * has strong query-relative affinity. That is a heat map of interest, and it
 * is drawn here as one.
 *
 * It is NOT a street map, and it is NOT where the venues are. Qloo's geocode
 * carries an address rather than a coordinate, so the venue pins on the
 * constellation cannot be placed on a real map. This plot is the geographic
 * reference the evidence actually supports, and it says so on its face.
 */

export interface GeoPoint {
  lat: number
  lon: number
  geohash?: string | null
  affinity?: number | null
  popularity?: number | null
}

export interface GeoLayer {
  entityId?: string | null
  within?: string | null
  points: GeoPoint[]
  bounds?: { west: number; south: number; east: number; north: number } | null
  metric?: string
  note?: string
}

const WIDTH = 860
const HEIGHT = 460
const PAD = 62

/** An equirectangular projection, which is the honest one for a small area. */
function project(point: GeoPoint, bounds: { west: number; south: number; east: number; north: number }) {
  const spanLon = Math.max(0.0001, bounds.east - bounds.west)
  const spanLat = Math.max(0.0001, bounds.north - bounds.south)
  const x = PAD + ((point.lon - bounds.west) / spanLon) * (WIDTH - PAD * 2)
  // Latitude grows northwards; the screen grows downwards.
  const y = HEIGHT - PAD - ((point.lat - bounds.south) / spanLat) * (HEIGHT - PAD * 2)
  return { x, y }
}

export function GeoMap({ layer, label = 'Geographic interest' }: { layer: GeoLayer | null | undefined; label?: string }) {
  const [hovered, setHovered] = useState<number | null>(null)

  const points = layer?.points ?? []
  const bounds = useMemo(() => {
    if (points.length) {
      const lats = points.map((p) => p.lat)
      const lons = points.map((p) => p.lon)
      return {
        west: Math.min(...lons), east: Math.max(...lons),
        south: Math.min(...lats), north: Math.max(...lats),
      }
    }
    return layer?.bounds ?? { west: -180, east: 180, south: -90, north: 90 }
  }, [points, layer?.bounds])

  if (!points.length) {
    return <div className="geo-map is-empty">
      <span className="small-cap"><span className="orange-dot"/> {label.toUpperCase()}</span>
      <p>Qloo returned no geographic cells for this entity inside {layer?.within ?? 'the area'}.</p>
    </div>
  }

  const placed = points.map((point) => ({ point, ...project(point, bounds) }))

  // Affinity is the metric that matters, but within one area it is often
  // almost identical across every cell. Encoding a spread of 0.001 would draw
  // twenty identical dots and imply a comparison the data does not support,
  // so popularity is used instead, and the legend says which.
  const affinities = points.map((p) => p.affinity).filter((a): a is number => typeof a === 'number')
  const popularities = points.map((p) => p.popularity).filter((a): a is number => typeof a === 'number')
  const affinitySpread = affinities.length ? Math.max(...affinities) - Math.min(...affinities) : 0
  const useAffinity = affinitySpread > 0.005
  const values = useAffinity ? affinities : popularities
  const top = values.length ? Math.max(...values) : 1
  const bottom = values.length ? Math.min(...values) : 0
  const span = Math.max(0.0001, top - bottom)
  const scale = (value?: number | null) => (typeof value === 'number' ? (value - bottom) / span : 0)
  const metricName = useAffinity ? 'affinity' : 'popularity'
  const metricOf = (point: GeoPoint) => (useAffinity ? point.affinity : point.popularity)

  // Gridlines at round latitudes and longitudes, so the plot can be read.
  const gridLat = [0.25, 0.5, 0.75].map((f) => bounds.south + span * 0 + (bounds.north - bounds.south) * f)
  const gridLon = [0.25, 0.5, 0.75].map((f) => bounds.west + (bounds.east - bounds.west) * f)

  return <figure className="geo-map">
    <figcaption className="geo-map-head">
      <span className="small-cap"><span className="orange-dot"/> {label.toUpperCase()}</span>
      <span className="sample-label">{layer?.within ?? 'AREA'} · QLOO POPULARITY CELLS</span>
    </figcaption>

    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img"
      aria-label={`A geographic interest plot of ${points.length} Qloo cells inside ${layer?.within ?? 'the area'}`}>
      <defs>
        <radialGradient id="geo-glow">
          <stop offset="0%" stopColor="rgba(226,98,47,.30)" />
          <stop offset="100%" stopColor="rgba(226,98,47,0)" />
        </radialGradient>
      </defs>

      <rect x="0" y="0" width={WIDTH} height={HEIGHT} fill="var(--surface-raised)" />

      {gridLon.map((lon, index) => {
        const { x } = project({ lat: bounds.south, lon }, bounds)
        return <g key={`lon-${index}`}>
          <line x1={x} y1={PAD} x2={x} y2={HEIGHT - PAD} stroke="var(--line)" strokeWidth="1" strokeDasharray="3 7" />
          <text x={x} y={HEIGHT - PAD + 18} textAnchor="middle" className="geo-axis">{lon.toFixed(2)}°</text>
        </g>
      })}
      {gridLat.map((lat, index) => {
        const { y } = project({ lat, lon: bounds.west }, bounds)
        return <g key={`lat-${index}`}>
          <line x1={PAD} y1={y} x2={WIDTH - PAD} y2={y} stroke="var(--line)" strokeWidth="1" strokeDasharray="3 7" />
          <text x={PAD - 12} y={y - 5} textAnchor="end" className="geo-axis">{lat.toFixed(2)}°</text>
        </g>
      })}

      {placed.map(({ point, x, y }, index) => {
        const heat = scale(metricOf(point))
        const radius = 7 + heat * 26
        const active = hovered === index
        return <g key={`${point.lat}-${point.lon}-${index}`} className={`geo-point${active ? ' is-active' : ''}`}
          onMouseEnter={() => setHovered(index)} onMouseLeave={() => setHovered(null)}>
          <circle cx={x} cy={y} r={radius} fill="url(#geo-glow)" />
          <circle cx={x} cy={y} r={5 + heat * 4}
            fill={active ? 'var(--sun)' : 'var(--clay)'}
            stroke="var(--band-text)" strokeWidth="1.4" opacity="0.92" />
          {active && <g>
            <line x1={x} y1={y} x2={x} y2={y - 34} stroke="var(--sun)" strokeWidth="1.2" />
            <circle cx={x} cy={y - 34} r="3" fill="var(--sun)" />
            <text x={x} y={y - 42} textAnchor="middle" className="geo-tip">
              {metricOf(point) != null ? `${metricName} ${metricOf(point)!.toFixed(4)}` : `${metricName} n/a`}
            </text>
            <text x={x} y={y - 28} textAnchor="middle" className="geo-tip is-dim">
              {point.affinity != null ? `affinity ${point.affinity.toFixed(4)}` : `lat ${point.lat.toFixed(3)}, lon ${point.lon.toFixed(3)}`}
            </text>
          </g>}
        </g>
      })}
    </svg>

    <div className="geo-map-foot">
      <span className="geo-legend"><i /> lower {metricName} <i className="is-high" /> higher {metricName}</span>
      <span className="geo-note">
        {layer?.note ?? 'Qloo supplies geographic popularity cells for interest mapping. These are distinct from precise venue coordinates.'}
      </span>
    </div>

    {/* The same answer, without a pointer. */}
    <details className="geo-table">
      <summary>Read the {points.length} cells as a table</summary>
      <table>
        <thead><tr><th>Latitude</th><th>Longitude</th><th>Affinity</th><th>Popularity</th><th>Geohash</th></tr></thead>
        <tbody>
          {points.map((point, index) => <tr key={index}>
            <td>{point.lat.toFixed(4)}</td>
            <td>{point.lon.toFixed(4)}</td>
            <td>{point.affinity != null ? point.affinity.toFixed(4) : '—'}</td>
            <td>{point.popularity != null ? point.popularity.toFixed(4) : '—'}</td>
            <td>{point.geohash ?? '—'}</td>
          </tr>)}
        </tbody>
      </table>
    </details>
  </figure>
}
