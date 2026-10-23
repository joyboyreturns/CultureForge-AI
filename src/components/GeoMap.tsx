import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { LocateFixed, Search } from 'lucide-react'
import type { GeoJSONSource, Map as MapLibreMap, StyleSpecification } from 'maplibre-gl'
import type { Concept, Evidence, EvidenceClass } from '../contracts'

/**
 * The geographic interest map.
 *
 * Qloo's `where_popular` workflow returns geographic cells — a latitude, a
 * longitude, an affinity and a popularity — for the places where one entity
 * has strong query-relative affinity. That is a map of interest, and it is
 * drawn here as one, with MapLibre.
 *
 * It is NOT where the venues are. Qloo's geocode for a place carries an
 * address rather than a coordinate, and CultureForge does not geocode, so a
 * place is drawn only when a verified coordinate came back with it. There is
 * no basemap either: no tile server, no style URL, no key. The grid is
 * latitude and longitude, and the screen says so.
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

/** What the map knows about the brief beyond the cells. Optional: the
 *  investigation view draws the cells alone. */
export interface GeoContext {
  evidence: Evidence[]
  concepts: Concept[]
  selectedId: string
  /** The Qloo entity whose interest the cells describe. */
  entityId: string
  /** The selected direction's anchor entity, when it has one. */
  anchorEntityId?: string
}

type Bounds = { west: number; south: number; east: number; north: number }
type LayerKey = 'cells' | 'competitors' | 'attractions' | 'context'
type Status = 'loading' | 'ready' | 'failed'

const CLASS_LABEL: Record<EvidenceClass, string> = {
  direct_business: 'Direct business reference',
  indirect_business: 'Adjacent business reference',
  cultural_attraction: 'Cultural attraction',
  audience_affinity: 'Audience affinity',
  unverified_geography: 'Direct reference, location unconfirmed',
  unrelated: 'Unrelated to this brief',
}

const UNKNOWNS = [
  'Where any place is. A cell is where interest concentrates, not an address or a site.',
  'Foot traffic or visitor counts. Qloo does not return them.',
  'Demand, revenue, rent or willingness to pay.',
  'How crowded the area is with competitors. Only references with a verified coordinate are drawn, and nothing here is a density.',
  'How large the cell is or how precisely it is placed. Qloo does not state it.',
]

const ATTRIBUTION = 'Interest cells: <a href="https://docs.qloo.com/" target="_blank" rel="noreferrer">Qloo</a> where_popular · No basemap · Rendering: <a href="https://maplibre.org/" target="_blank" rel="noreferrer">MapLibre GL JS</a>'

function verifiedCoordinate(item: Evidence) {
  const c = item.coordinates
  if (!c || !Number.isFinite(c.lat) || !Number.isFinite(c.lon)) return null
  if (Math.abs(c.lat) > 90 || Math.abs(c.lon) > 180) return null
  return { lat: c.lat, lon: c.lon }
}

function classOf(item: Evidence): EvidenceClass | null {
  return item.relevance?.evidenceClass ?? null
}

/** Straight-line distance between two returned coordinates, in kilometres. */
function distanceKm(a: { lat: number; lon: number }, b: { lat: number; lon: number }) {
  const rad = Math.PI / 180
  const dLat = (b.lat - a.lat) * rad
  const dLon = (b.lon - a.lon) * rad
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dLon / 2) ** 2
  return 6371 * 2 * Math.asin(Math.sqrt(h))
}

function boundsOf(points: { lat: number; lon: number }[], fallback?: Bounds | null): Bounds {
  if (!points.length) return fallback ?? { west: -180, east: 180, south: -85, north: 85 }
  const lats = points.map((p) => p.lat)
  const lons = points.map((p) => p.lon)
  return { west: Math.min(...lons), east: Math.max(...lons), south: Math.min(...lats), north: Math.max(...lats) }
}

/** A latitude/longitude grid, so a map with no basemap can still be read. */
function graticule(bounds: Bounds) {
  const span = Math.max(bounds.east - bounds.west, bounds.north - bounds.south, 0.001)
  const steps = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 30]
  const step = steps.find((s) => span / s <= 5) ?? 30
  const pad = step * 8
  const west = Math.max(-180, Math.floor((bounds.west - pad) / step) * step)
  const east = Math.min(180, Math.ceil((bounds.east + pad) / step) * step)
  const south = Math.max(-85, Math.floor((bounds.south - pad) / step) * step)
  const north = Math.min(85, Math.ceil((bounds.north + pad) / step) * step)
  const features: GeoJSON.Feature[] = []
  for (let lon = west; lon <= east + 1e-9; lon += step) {
    features.push({ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: [[lon, south], [lon, north]] } })
  }
  for (let lat = south; lat <= north + 1e-9; lat += step) {
    features.push({ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: [[west, lat], [east, lat]] } })
  }
  return { type: 'FeatureCollection', features } as GeoJSON.FeatureCollection
}

function readColors(element: Element) {
  const style = getComputedStyle(element)
  const read = (name: string, fallback: string) => style.getPropertyValue(name).trim() || fallback
  return {
    background: read('--map-ground', '#ece7f3'),
    grid: read('--line', '#d5d0dc'),
    cellLow: read('--map-cell', '#8b71ac'),
    cellHigh: read('--map-cell-hot', '#c0612b'),
    stroke: read('--text', '#1c1723'),
    competitor: read('--map-competitor', '#9b3a2f'),
    attraction: read('--map-attraction', '#3f5f8a'),
    context: read('--map-context', '#1c1723'),
  }
}

export function GeoMap({ layer, label = 'Geographic interest', context }: {
  layer: GeoLayer | null | undefined
  label?: string
  context?: GeoContext
}) {
  const uid = useId()
  const containerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const [status, setStatus] = useState<Status>('loading')
  const [selected, setSelected] = useState<number | null>(null)
  const [query, setQuery] = useState('')
  const [searchNote, setSearchNote] = useState('')
  const [themeTick, setThemeTick] = useState(0)
  const [visible, setVisible] = useState<Record<LayerKey, boolean>>({ cells: true, competitors: true, attractions: true, context: true })

  const points = useMemo(() => layer?.points ?? [], [layer?.points])
  const within = layer?.within ?? 'the area'
  const bounds = useMemo(() => boundsOf(points, layer?.bounds), [points, layer?.bounds])

  // Affinity is the metric that matters, but within one area it is often
  // almost identical across every cell. Encoding a spread of 0.001 would draw
  // twenty identical dots and imply a comparison the data does not support,
  // so popularity is used instead, and the legend says which.
  const metric = useMemo(() => {
    const affinities = points.map((p) => p.affinity).filter((a): a is number => typeof a === 'number')
    const popularities = points.map((p) => p.popularity).filter((a): a is number => typeof a === 'number')
    const spread = affinities.length ? Math.max(...affinities) - Math.min(...affinities) : 0
    const useAffinity = spread > 0.005
    const values = useAffinity ? affinities : popularities
    const top = values.length ? Math.max(...values) : 1
    const bottom = values.length ? Math.min(...values) : 0
    const span = Math.max(0.0001, top - bottom)
    const of = (point: GeoPoint) => (useAffinity ? point.affinity : point.popularity)
    const heat = (point: GeoPoint) => { const v = of(point); return typeof v === 'number' ? (v - bottom) / span : 0 }
    const order = points.map((_, i) => i).sort((a, b) => (of(points[b]) ?? -Infinity) - (of(points[a]) ?? -Infinity))
    const rank = new Map(order.map((index, position) => [index, position + 1]))
    return { name: useAffinity ? 'affinity' : 'popularity', useAffinity, of, heat, order, rank }
  }, [points])

  // Evidence the brief returned, by class, and which of it can be placed.
  const evidence = useMemo(() => context?.evidence ?? [], [context?.evidence])
  const references = useMemo(() => evidence
    .map((item) => ({ item, cls: classOf(item), at: verifiedCoordinate(item) }))
    .filter((r) => r.cls === 'direct_business' || r.cls === 'cultural_attraction'), [evidence])
  const placed = useMemo(() => references.filter((r) => r.at) as { item: Evidence; cls: EvidenceClass; at: { lat: number; lon: number } }[], [references])
  const directCount = references.filter((r) => r.cls === 'direct_business').length
  const attractionCount = references.filter((r) => r.cls === 'cultural_attraction').length
  const competitorsPlaced = placed.filter((r) => r.cls === 'direct_business')
  const attractionsPlaced = placed.filter((r) => r.cls === 'cultural_attraction')

  const place = evidence.find((item) => item.entityId && item.entityId === (context?.entityId ?? layer?.entityId))
  const concept = context?.concepts.find((c) => c.id === context.selectedId)
  const isAnchor = Boolean(context && context.anchorEntityId && context.anchorEntityId === context.entityId)
  const seeds = evidence.filter((item) => item.kind === 'tag').slice(0, 6)

  const cellsGeo = useMemo(() => ({
    type: 'FeatureCollection',
    features: points.map((point, index) => ({
      type: 'Feature', properties: { index, heat: metric.heat(point) },
      geometry: { type: 'Point', coordinates: [point.lon, point.lat] },
    })),
  }) as GeoJSON.FeatureCollection, [points, metric])

  const referencesGeo = useMemo(() => ({
    type: 'FeatureCollection',
    features: placed.map(({ item, cls, at }) => ({
      type: 'Feature', properties: { id: item.id, cls },
      geometry: { type: 'Point', coordinates: [at.lon, at.lat] },
    })),
  }) as GeoJSON.FeatureCollection, [placed])

  const extentGeo = useMemo(() => {
    const { west, east, south, north } = bounds
    return { type: 'FeatureCollection', features: [{ type: 'Feature', properties: {}, geometry: {
      type: 'LineString', coordinates: [[west, south], [east, south], [east, north], [west, north], [west, south]],
    } }] } as GeoJSON.FeatureCollection
  }, [bounds])

  const fitAll = useCallback(() => {
    const map = mapRef.current
    if (!map) return
    map.fitBounds([[bounds.west, bounds.south], [bounds.east, bounds.north]], { padding: 48, maxZoom: 14, duration: 500 })
  }, [bounds])

  const focusCell = useCallback((index: number) => {
    setSelected(index)
    const point = points[index]
    const map = mapRef.current
    if (map && point) map.easeTo({ center: [point.lon, point.lat], zoom: Math.max(map.getZoom(), 12), duration: 500 })
  }, [points])

  // Follow the studio's theme: the map's paint is resolved from the tokens.
  useEffect(() => {
    const bump = () => setThemeTick((t) => t + 1)
    const observer = new MutationObserver(bump)
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    const media = window.matchMedia?.('(prefers-color-scheme: dark)')
    media?.addEventListener?.('change', bump)
    return () => { observer.disconnect(); media?.removeEventListener?.('change', bump) }
  }, [])

  // A new set of cells is a new map.
  useEffect(() => { setSelected(null); setSearchNote('') }, [points])

  // Create the map once per set of cells. MapLibre is loaded on demand.
  useEffect(() => {
    const container = containerRef.current
    if (!points.length || !container) return
    let cancelled = false
    let map: MapLibreMap | null = null
    setStatus('loading')
    const colors = readColors(container)
    const style: StyleSpecification = {
      version: 8,
      sources: {
        grid: { type: 'geojson', data: graticule(bounds) },
        extent: { type: 'geojson', data: extentGeo },
        cells: { type: 'geojson', data: cellsGeo },
        references: { type: 'geojson', data: referencesGeo },
      },
      layers: [
        { id: 'ground', type: 'background', paint: { 'background-color': colors.background } },
        { id: 'grid', type: 'line', source: 'grid', paint: { 'line-color': colors.grid, 'line-width': 1, 'line-dasharray': [2, 4] } },
        { id: 'context', type: 'line', source: 'extent', paint: { 'line-color': colors.context, 'line-width': 1.4, 'line-dasharray': [4, 3], 'line-opacity': 0.7 } },
        { id: 'cells-glow', type: 'circle', source: 'cells', paint: {
          'circle-radius': ['interpolate', ['linear'], ['get', 'heat'], 0, 14, 1, 34],
          'circle-color': colors.cellHigh, 'circle-opacity': ['interpolate', ['linear'], ['get', 'heat'], 0, 0.08, 1, 0.26], 'circle-blur': 0.9,
        } },
        { id: 'cells', type: 'circle', source: 'cells', paint: {
          'circle-radius': ['interpolate', ['linear'], ['get', 'heat'], 0, 6, 1, 11],
          'circle-color': ['interpolate', ['linear'], ['get', 'heat'], 0, colors.cellLow, 1, colors.cellHigh],
          'circle-stroke-color': colors.stroke, 'circle-stroke-width': 1, 'circle-stroke-opacity': 0.55, 'circle-opacity': 0.92,
        } },
        { id: 'cells-selected', type: 'circle', source: 'cells', filter: ['==', ['get', 'index'], -1], paint: {
          'circle-radius': 17, 'circle-opacity': 0, 'circle-stroke-color': colors.stroke, 'circle-stroke-width': 2.5,
        } },
        { id: 'competitors', type: 'circle', source: 'references', filter: ['==', ['get', 'cls'], 'direct_business'], paint: {
          'circle-radius': 6, 'circle-color': colors.competitor, 'circle-stroke-color': colors.background, 'circle-stroke-width': 2,
        } },
        { id: 'attractions', type: 'circle', source: 'references', filter: ['==', ['get', 'cls'], 'cultural_attraction'], paint: {
          'circle-radius': 6, 'circle-color': colors.attraction, 'circle-stroke-color': colors.background, 'circle-stroke-width': 2,
        } },
      ],
    }

    import('./maplibreLoader').then((lib) => {
      if (cancelled || !containerRef.current) return
      try {
        map = new lib.MapLibreMap({
          container, style, attributionControl: false, dragRotate: false, pitchWithRotate: false, maxZoom: 16,
          bounds: [[bounds.west, bounds.south], [bounds.east, bounds.north]], fitBoundsOptions: { padding: 48, maxZoom: 14 },
        })
      } catch {
        setStatus('failed')
        return
      }
      const m = map
      m.touchZoomRotate.disableRotation()
      m.keyboard.disableRotation()
      m.addControl(new lib.NavigationControl({ showCompass: false }), 'top-right')
      m.addControl(new lib.ScaleControl({ unit: 'metric' }), 'bottom-left')
      m.addControl(new lib.AttributionControl({ compact: true, customAttribution: ATTRIBUTION }), 'bottom-right')
      const canvas = m.getCanvas()
      canvas.setAttribute('aria-label', `Map of ${points.length} Qloo interest cells inside ${within}. Arrow keys pan, plus and minus zoom. The cell list beside the map selects a cell.`)
      canvas.setAttribute('role', 'application')
      m.on('load', () => {
        if (cancelled) return
        // The panel can settle after creation; frame the cells at the final size.
        m.resize()
        m.fitBounds([[bounds.west, bounds.south], [bounds.east, bounds.north]], { padding: 48, maxZoom: 14, duration: 0 })
        setStatus('ready')
      })
      m.on('click', 'cells', (event) => {
        const index = event.features?.[0]?.properties?.index
        if (typeof index === 'number') setSelected(index)
      })
      m.on('mouseenter', 'cells', () => { canvas.style.cursor = 'pointer' })
      m.on('mouseleave', 'cells', () => { canvas.style.cursor = '' })
      mapRef.current = m
    }).catch(() => { if (!cancelled) setStatus('failed') })

    return () => {
      cancelled = true
      map?.remove()
      mapRef.current = null
    }
    // The style is built from the data present at creation; later changes to
    // the references, the selection and the toggles are applied in place.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [points])

  // References and the extent can change without a new set of cells.
  useEffect(() => {
    const map = mapRef.current
    if (status !== 'ready' || !map) return
    ;(map.getSource('references') as GeoJSONSource | undefined)?.setData(referencesGeo)
    ;(map.getSource('extent') as GeoJSONSource | undefined)?.setData(extentGeo)
  }, [status, referencesGeo, extentGeo])

  // Layer toggles. The context outline exists only for the direction's anchor.
  useEffect(() => {
    const map = mapRef.current
    if (status !== 'ready' || !map) return
    const show = (on: boolean) => (on ? 'visible' : 'none')
    for (const id of ['cells', 'cells-glow', 'cells-selected']) map.setLayoutProperty(id, 'visibility', show(visible.cells))
    map.setLayoutProperty('competitors', 'visibility', show(visible.competitors))
    map.setLayoutProperty('attractions', 'visibility', show(visible.attractions))
    map.setLayoutProperty('context', 'visibility', show(visible.context && isAnchor))
  }, [status, visible, isAnchor])

  useEffect(() => {
    const map = mapRef.current
    if (status !== 'ready' || !map) return
    map.setFilter('cells-selected', ['==', ['get', 'index'], selected ?? -1])
  }, [status, selected])

  useEffect(() => {
    const map = mapRef.current
    const container = containerRef.current
    if (status !== 'ready' || !map || !container || !themeTick) return
    const colors = readColors(container)
    map.setPaintProperty('ground', 'background-color', colors.background)
    map.setPaintProperty('grid', 'line-color', colors.grid)
    map.setPaintProperty('context', 'line-color', colors.context)
    map.setPaintProperty('cells-glow', 'circle-color', colors.cellHigh)
    map.setPaintProperty('cells', 'circle-color', ['interpolate', ['linear'], ['get', 'heat'], 0, colors.cellLow, 1, colors.cellHigh])
    map.setPaintProperty('cells', 'circle-stroke-color', colors.stroke)
    map.setPaintProperty('cells-selected', 'circle-stroke-color', colors.stroke)
    map.setPaintProperty('competitors', 'circle-color', colors.competitor)
    map.setPaintProperty('attractions', 'circle-color', colors.attraction)
  }, [status, themeTick])

  // Focus targets come from the data alone: the cells' extent, each cell,
  // and each reference that carries a verified coordinate.
  const targets = useMemo(() => [
    { key: 'area', label: `${within} — all returned cells`, run: () => { setSelected(null); fitAll() } },
    ...metric.order.map((index) => ({
      key: `cell-${index}`,
      label: `Cell ${metric.rank.get(index)}${points[index].geohash ? ` · ${points[index].geohash}` : ''}`,
      run: () => focusCell(index),
    })),
    ...placed.map(({ item, at }) => ({
      key: `ref-${item.id}`, label: item.label,
      run: () => mapRef.current?.easeTo({ center: [at.lon, at.lat], zoom: 14, duration: 500 }),
    })),
  ], [within, metric, points, placed, fitAll, focusCell])

  function search(event: FormEvent) {
    event.preventDefault()
    const needle = query.trim().toLowerCase()
    if (!needle) { setSearchNote(''); return }
    const hit = targets.find((t) => t.label.toLowerCase().includes(needle))
    if (hit) { hit.run(); setSearchNote(`Focused: ${hit.label}.`); return }
    setSearchNote(`“${query.trim()}” has no coordinate in this evidence. The map can only focus on ${within}, its cells, and references Qloo returned with a coordinate; CultureForge does not look places up elsewhere.`)
  }

  if (!points.length) {
    return <div className="geo-map is-empty">
      <span className="small-cap"><span className="orange-dot"/> {label.toUpperCase()}</span>
      <p>Qloo returned no geographic cells for this entity inside {within}, so there is nothing to draw. No location has been estimated in their place.</p>
      {context && <p>{coordinateSummary(directCount, attractionCount, placed.length)}</p>}
    </div>
  }

  const cell = selected != null ? points[selected] : null
  const cellRank = selected != null ? metric.rank.get(selected) : null
  const nearby = cell ? placed.map((r) => ({ ...r, km: distanceKm(cell, r.at) })).sort((a, b) => a.km - b.km).slice(0, 5) : []
  const toggles: { key: LayerKey; label: string; count: number; swatch: string; disabled: string | null }[] = [
    { key: 'cells', label: 'Qloo interest cells', count: points.length, swatch: 'is-cell', disabled: null },
    ...(context ? [
      { key: 'competitors' as const, label: 'Competitors (verified coordinates)', count: competitorsPlaced.length, swatch: 'is-competitor',
        disabled: competitorsPlaced.length ? null : `None placed: ${directCount} direct-business reference${directCount === 1 ? '' : 's'} returned, none with a coordinate.` },
      { key: 'attractions' as const, label: 'Cultural attractions', count: attractionsPlaced.length, swatch: 'is-attraction',
        disabled: attractionsPlaced.length ? null : `None placed: ${attractionCount} returned, none with a coordinate.` },
      { key: 'context' as const, label: 'Selected direction context', count: isAnchor ? 1 : 0, swatch: 'is-context',
        disabled: isAnchor ? null : 'These cells are for another place, not the selected direction’s anchor.' },
    ] : []),
  ]

  return <figure className="geo-map">
    <figcaption className="geo-map-head">
      <span className="small-cap"><span className="orange-dot"/> {label.toUpperCase()}</span>
      <span className="sample-label">{within} · {points.length} QLOO INTEREST CELLS</span>
    </figcaption>

    <div className="geo-map-tools">
      <form className="geo-search" role="search" onSubmit={search}>
        <label htmlFor={`${uid}-search`} className="geo-sr-only">Focus on a place in this evidence</label>
        <Search size={14} aria-hidden="true"/>
        <input id={`${uid}-search`} type="search" list={`${uid}-targets`} value={query} placeholder={`Focus: ${within}, a cell, a reference`}
          onChange={(event) => setQuery(event.target.value)} aria-describedby={`${uid}-note`}/>
        <datalist id={`${uid}-targets`}>{targets.map((t) => <option key={t.key} value={t.label}/>)}</datalist>
        <button type="submit" className="button button-secondary">Focus</button>
        <button type="button" className="button button-secondary" onClick={() => { setSelected(null); fitAll() }} aria-label="Show all returned cells">
          <LocateFixed size={14} aria-hidden="true"/> All cells
        </button>
      </form>
      <p id={`${uid}-note`} className="geo-search-note" aria-live="polite">{searchNote}</p>
      <fieldset className="geo-layers">
        <legend>Layers</legend>
        {toggles.map((t) => <label key={t.key} className={t.disabled ? 'is-disabled' : ''}>
          <input type="checkbox" checked={!t.disabled && visible[t.key]} disabled={Boolean(t.disabled)}
            onChange={(event) => setVisible((v) => ({ ...v, [t.key]: event.target.checked }))}
            aria-describedby={t.disabled ? `${uid}-${t.key}-why` : undefined}/>
          <i className={`geo-swatch ${t.swatch}`} aria-hidden="true"/>
          <span>{t.label} <b>{t.count}</b></span>
          {t.disabled && <small id={`${uid}-${t.key}-why`}>{t.disabled}</small>}
        </label>)}
      </fieldset>
    </div>

    <div className="geo-map-body">
      <div className="geo-map-stage">
        <div ref={containerRef} className="geo-map-canvas"/>
        {status === 'loading' && <p className="geo-map-overlay" role="status">Drawing the cells…</p>}
        {status === 'failed' && <p className="geo-map-overlay" role="alert">This browser could not start the map (WebGL is unavailable). The cells are listed beside it and in the table below.</p>}
        <p className="geo-map-basemap">No basemap: streets and coastlines are not drawn, because no third-party tiles are loaded. The dashed grid is latitude and longitude.</p>
      </div>

      <aside className="geo-panel" aria-label="Cell detail" aria-live="polite">
        {cell && cellRank ? <>
          <div className="geo-panel-head">
            <span className="tiny-cap">CELL {cellRank} OF {points.length} · BY {metric.name.toUpperCase()}</span>
            <button type="button" className="text-link" onClick={() => setSelected(null)} aria-label="Close cell detail">Close</button>
          </div>
          <p className="geo-panel-coord">Qloo coordinate {cell.lat.toFixed(4)}, {cell.lon.toFixed(4)}{cell.geohash ? ` · geohash ${cell.geohash}` : ''}. A cell of interest, not an address.</p>

          <h4>Why look here</h4>
          <p>{metric.useAffinity
            ? `Among the ${points.length} cells Qloo returned inside ${within}, this one ranks ${cellRank} by affinity for ${place?.label ?? 'the chosen place'}.`
            : `Affinity is nearly the same across all ${points.length} cells (a spread under 0.005), so they are ordered by Qloo popularity; this one ranks ${cellRank}.`}
            {' '}That is a reason to look at this area first and check it in person — not evidence of demand, visitors or a site.</p>

          <h4>Relevant Qloo evidence</h4>
          <ul>
            <li><b>{place?.label ?? 'The chosen place'}</b>{place && classOf(place) ? ` — ${CLASS_LABEL[classOf(place)!]}` : ''}. The cells measure where interest in it concentrates.
              {place?.relevance?.reasons?.[1] && <span className="geo-panel-dim"> {place.relevance.reasons[1]}</span>}</li>
            {concept && <li><b>{concept.name}</b> — the selected direction{isAnchor ? ', anchored on this place' : ', anchored elsewhere'}; it cites {concept.evidenceIds.length} piece{concept.evidenceIds.length === 1 ? '' : 's'} of Qloo evidence.</li>}
          </ul>

          <h4>Cultural affinities</h4>
          <dl className="geo-panel-values">
            <dt>Affinity</dt><dd>{cell.affinity != null ? cell.affinity.toFixed(4) : 'not returned'}</dd>
            <dt>Popularity</dt><dd>{cell.popularity != null ? cell.popularity.toFixed(4) : 'not returned'}</dd>
          </dl>
          {seeds.length > 0 && <p className="geo-panel-dim">Audience seeds for this brief: {seeds.map((s) => s.label).join(', ')}. They describe the audience, and were not measured per cell.</p>}

          <h4>Nearby verified references</h4>
          {nearby.length ? <ul>{nearby.map((r) => <li key={r.item.id}><b>{r.item.label}</b> — {CLASS_LABEL[r.cls]}, {r.km.toFixed(1)} km straight-line between two returned coordinates.</li>)}</ul>
            : <p className="geo-panel-dim">None. {context ? 'No returned reference carries a verified coordinate, so none can be placed near this cell.' : 'This view has no brief evidence to place.'}</p>}

          <h4>Important unknowns</h4>
          <ul className="geo-panel-unknowns">{UNKNOWNS.map((u) => <li key={u}>{u}</li>)}</ul>
        </> : <>
          <span className="tiny-cap">SELECT A CELL</span>
          <p className="geo-panel-dim">Choose a cell on the map or below to read the Qloo evidence behind it and what it does not establish.</p>
        </>}

        <h4>Cells, ranked by {metric.name}</h4>
        <ol className="geo-cell-list">
          {metric.order.map((index) => <li key={index}>
            <button type="button" aria-pressed={selected === index} onClick={() => focusCell(index)}
              aria-label={`Cell ${metric.rank.get(index)}, ${metric.name} ${metric.of(points[index])?.toFixed(4) ?? 'not returned'}`}>
              <span>Cell {metric.rank.get(index)}</span>
              <span>{metric.of(points[index])?.toFixed(4) ?? '—'}</span>
            </button>
          </li>)}
        </ol>
      </aside>
    </div>

    <div className="geo-map-foot">
      <span className="geo-legend"><i /> lower {metric.name} <i className="is-high" /> higher {metric.name}</span>
      <span className="geo-note">
        {layer?.note ?? 'Qloo supplies geographic popularity cells for interest mapping. These are distinct from precise venue coordinates.'}
        {context && <> {coordinateSummary(directCount, attractionCount, placed.length)}</>}
      </span>
      <span className="geo-source">Source: Qloo <code>where_popular</code> for {place?.label ?? layer?.entityId ?? 'the chosen place'}, inside {within}. Rendered with MapLibre GL JS; no basemap.</span>
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

function coordinateSummary(direct: number, attractions: number, placed: number) {
  if (placed) return `${placed} reference${placed === 1 ? '' : 's'} carry a verified coordinate and are drawn; the rest are not placed.`
  return `No verified coordinates: Qloo returned ${direct} direct-business and ${attractions} cultural-attraction reference${direct + attractions === 1 ? '' : 's'} for this brief, located by address or city text. CultureForge does not geocode them, so none is placed on this map.`
}
