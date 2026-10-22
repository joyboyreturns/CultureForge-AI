import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { LocateFixed, LoaderCircle, RotateCcw, Search } from 'lucide-react'
import type { GeoJSONSource, Map as MapLibreMap, MapLayerMouseEvent } from 'maplibre-gl'
import type { Concept, Evidence, ProjectRequest } from '../../contracts'
import type { RecomposeResult } from '../../api'
import {
  KIND_WORDS, boundsOf, cellFeatures, cellMetric, citedVenueIds, decodeMapHash, directionsCiting, encodeMapHash,
  matchSearch, nearBounds, placementOf, pointFeatures, venueCandidates, venueFeatures,
} from './mapModel'
import type { Bounds, CellPoint, PlottedVenue, SearchTarget } from './mapModel'
import { BASEMAP_SOURCE, EVIDENCE_ATTRIBUTION, composeStyle } from './style'
import type { BasemapMode, Theme } from './style'
import { CLICKABLE, EMPTY, LAYER_GROUPS, readOverlayColors } from './layers'
import type { OverlayData, OverlayVisibility } from './layers'
import { useVenueCoordinates } from './useVenueCoordinates'
import { LayersPanel } from './LayersPanel'
import { DirectionPicker } from './DirectionPicker'
import { VenuePanel } from './VenuePanel'
import { RemovalExperiment } from './RemovalExperiment'
import { JudgeHints } from './JudgeHints'

/**
 * The Cultural Opportunity Explorer: the brief's evidence on a real street
 * map. One MapLibre instance for the life of the view; everything after
 * creation (venues, cells, the chosen direction, the theme, a failed
 * basemap) is applied to it in place.
 */
export interface CellsLayer { points: CellPoint[]; within: string; placeLabel: string }

type Status = 'loading' | 'ready' | 'failed'

function currentTheme(): Theme {
  return document.documentElement.dataset.theme === 'light' ? 'light' : 'dark'
}
function prefersReducedMotion() {
  return Boolean(window.matchMedia?.('(prefers-reduced-motion: reduce)').matches)
}

export function OpportunityMap({
  evidence, concepts, selectedId, onSelect, project, removalUnsupported, onInspect, onOpenConcept, onApplyRebuild, undo,
  cells, cellsControl,
}: {
  evidence: Evidence[]
  concepts: Concept[]
  selectedId: string
  onSelect?: (id: string) => void
  project: ProjectRequest
  removalUnsupported: string | null
  onInspect?: (evidenceId: string) => void
  onOpenConcept?: (concept: Concept) => void
  onApplyRebuild?: (rebuild: RecomposeResult, venueLabel: string) => void
  undo?: { label: string; run: () => void } | null
  cells: CellsLayer | null
  cellsControl: ReactNode
}) {
  const uid = useId()
  const [tip, setTip] = useState<{ x: number; y: number; label: string; kind: string; cited: boolean } | null>(null)
  const location = project.location
  const containerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const sideRef = useRef<HTMLElement | null>(null)
  const returnFocus = useRef<HTMLElement | null>(null)
  const [status, setStatus] = useState<Status>('loading')
  const [basemap, setBasemap] = useState<{ mode: BasemapMode; reason: string }>({ mode: 'streets', reason: '' })
  const [visible, setVisible] = useState<OverlayVisibility>({ heat: true, venues: true, context: true })
  const [layersOpen, setLayersOpen] = useState(false)
  const [focus, setFocus] = useState(true)
  const [venueId, setVenueId] = useState<string | null>(null)
  const [cellIndex, setCellIndex] = useState<number | null>(null)
  const [query, setQuery] = useState('')
  const [note, setNote] = useState('')
  const [themeTick, setThemeTick] = useState(0)
  const [done, setDone] = useState([false, false, false, false])
  const mark = useCallback((i: number) => setDone((d) => (d[i] ? d : d.map((v, j) => (j === i ? true : v)))), [])

  // --- The evidence, and where each venue stands -------------------------------
  const candidates = useMemo(() => venueCandidates(evidence), [evidence])
  const geo = useVenueCoordinates(candidates, location)
  const placements = useMemo(() => new Map(candidates.map((c) => [c.venue.id, placementOf(c, geo.results[c.venue.id])])), [candidates, geo.results])
  const plotted = useMemo<PlottedVenue[]>(() => candidates.flatMap((c) => {
    const p = placements.get(c.venue.id)
    return p?.state === 'plotted' && c.kind ? [{ venue: c.venue, kind: c.kind, at: p.at }] : []
  }), [candidates, placements])
  const unplotted = candidates.filter((c) => placements.get(c.venue.id)?.state === 'not_plotted')
  const counts = {
    cells: cells?.points.length ?? 0,
    direct: plotted.filter((p) => p.kind === 'direct').length,
    indirect: plotted.filter((p) => p.kind === 'indirect').length,
    attraction: plotted.filter((p) => p.kind === 'attraction').length,
  }

  const concept = concepts.find((c) => c.id === selectedId)
  const cited = useMemo(() => citedVenueIds(concept, evidence), [concept, evidence])
  const citedPlotted = plotted.filter((p) => cited.has(p.venue.id))
  const highlight = focus && visible.context && citedPlotted.length > 0
  const points = useMemo(() => cells?.points ?? [], [cells])
  const metric = useMemo(() => cellMetric(points), [points])

  const data = useMemo<OverlayData>(() => {
    const venue = plotted.find((p) => p.venue.id === venueId)
    const cell = cellIndex != null ? points[cellIndex] : null
    return {
      cells: cellFeatures(points),
      venues: venueFeatures(plotted, cited, highlight),
      context: highlight ? pointFeatures(citedPlotted.map((p) => p.at)) : EMPTY,
      selected: venue ? pointFeatures([venue.at]) : cell ? pointFeatures([cell]) : EMPTY,
    }
  }, [points, plotted, cited, highlight, citedPlotted, venueId, cellIndex])

  const dataBounds = useMemo(() => boundsOf([...plotted.map((p) => p.at), ...points]), [plotted, points])
  const boundsKey = dataBounds ? [dataBounds.west, dataBounds.south, dataBounds.east, dataBounds.north].map((n) => n.toFixed(4)).join(',') : ''

  // The latest of everything, for handlers registered once.
  const latest = useRef({ data, visible, bounds: dataBounds as Bounds | null, plotted, mode: 'streets' as BasemapMode })
  latest.current = { ...latest.current, data, visible, bounds: dataBounds, plotted }

  const compose = useCallback(() => {
    const container = containerRef.current
    const { data: d, visible: v, bounds, mode } = latest.current
    return composeStyle({ mode, theme: currentTheme(), colors: readOverlayColors(container ?? document.documentElement), data: d, visible: v, bounds })
  }, [])

  // --- Movement ------------------------------------------------------------------
  const userMoved = useRef(false)
  const framed = useRef(false)
  const initialHash = useRef(decodeMapHash(window.location.hash))
  const fit = useCallback((bounds: Bounds | null) => {
    const map = mapRef.current
    if (!map || !bounds) return
    map.fitBounds([[bounds.west, bounds.south], [bounds.east, bounds.north]], { padding: 56, maxZoom: 15, duration: prefersReducedMotion() ? 0 : 600 })
  }, [])
  const flyTo = useCallback((at: { lat: number; lon: number }, zoom = 15) => {
    const map = mapRef.current
    if (!map) return
    const options = { center: [at.lon, at.lat] as [number, number], zoom: Math.max(map.getZoom(), zoom) }
    if (prefersReducedMotion()) map.jumpTo(options)
    else map.easeTo({ ...options, duration: 600 })
  }, [])

  // --- The map: created once ----------------------------------------------------------
  const retryStreets = useRef<() => void>(() => {})
  const openVenue = useRef<(id: string) => void>(() => {})
  const openCell = useRef<(index: number) => void>(() => {})
  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    let cancelled = false
    let map: MapLibreMap | null = null
    let hashTimer = 0
    let basemapTimer = 0
    let basemapSeen = false
    // A new map frames the evidence afresh.
    framed.current = false
    userMoved.current = false
    setStatus('loading')
    if (navigator.onLine === false) {
      latest.current.mode = 'grid'
      setBasemap({ mode: 'grid', reason: 'This browser is offline, so street tiles cannot load.' })
    }
    retryStreets.current = () => {
      if (!map || latest.current.mode === 'streets') return
      basemapSeen = false
      latest.current.mode = 'streets'
      setBasemap({ mode: 'streets', reason: '' })
      map.setStyle(compose(), { diff: false })
      watchTiles()
    }
    const toGrid = (reason: string) => {
      if (!map || latest.current.mode === 'grid') return
      latest.current.mode = 'grid'
      setBasemap({ mode: 'grid', reason })
      map.setStyle(compose(), { diff: false })
    }

    // A basemap that never answers is treated as one that failed. The clock
    // starts once the map has loaded, and a hidden page (which draws
    // nothing) is not held against the tiles.
    const watchTiles = () => {
      window.clearTimeout(basemapTimer)
      basemapTimer = window.setTimeout(() => {
        if (basemapSeen || latest.current.mode !== 'streets') return
        if (document.hidden) watchTiles()
        else toGrid('The street tiles did not arrive in time.')
      }, 12000)
    }

    import('../maplibreLoader').then((lib) => {
      if (cancelled || !containerRef.current) return
      try {
        map = new lib.MapLibreMap({
          container, style: compose(), attributionControl: false, dragRotate: false, pitchWithRotate: false,
          maxZoom: 18, center: [0, 20], zoom: 1.2, fadeDuration: prefersReducedMotion() ? 0 : 200,
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
      m.addControl(new lib.AttributionControl({ compact: true, customAttribution: EVIDENCE_ATTRIBUTION }), 'bottom-right')
      const canvas = m.getCanvas()
      canvas.setAttribute('role', 'application')
      canvas.setAttribute('aria-label', `Street map of the evidence for ${location}. Arrow keys pan, plus and minus zoom. The venue list beside the map opens each venue.`)

      m.on('load', () => { if (!cancelled) { m.resize(); setStatus('ready'); watchTiles() } })
      m.on('data', (event) => {
        if ((event as { sourceId?: string; tile?: unknown }).sourceId === BASEMAP_SOURCE && (event as { tile?: unknown }).tile) basemapSeen = true
      })
      m.on('error', (event) => {
        const source = (event as { sourceId?: string }).sourceId
        const message = String(event.error?.message ?? '')
        if (latest.current.mode !== 'streets') return
        if ((source === BASEMAP_SOURCE || /tiles\.openfreemap\.org\/planet/.test(message)) && !basemapSeen) {
          toGrid('The street tiles could not be loaded from OpenFreeMap.')
        }
      })

      m.on('click', CLICKABLE.venue, (event: MapLayerMouseEvent) => {
        const id = event.features?.[0]?.properties?.id
        if (typeof id === 'string') { returnFocus.current = canvas; openVenue.current(id) }
      })
      m.on('click', CLICKABLE.cluster, (event: MapLayerMouseEvent) => {
        const feature = event.features?.[0]
        const clusterId = feature?.properties?.cluster_id
        const source = m.getSource('venues') as GeoJSONSource | undefined
        if (typeof clusterId !== 'number' || !source || feature?.geometry.type !== 'Point') return
        mark(0)
        const [lon, lat] = feature.geometry.coordinates as [number, number]
        source.getClusterExpansionZoom(clusterId).then((zoom) => {
          const options = { center: [lon, lat] as [number, number], zoom: Math.min(zoom + 0.2, 18) }
          if (prefersReducedMotion()) m.jumpTo(options); else m.easeTo({ ...options, duration: 500 })
        }).catch(() => { /* a cluster that vanished mid-click needs nothing */ })
      })
      m.on('click', CLICKABLE.cell, (event: MapLayerMouseEvent) => {
        const index = event.features?.[0]?.properties?.index
        if (typeof index === 'number') openCell.current(index)
      })
      for (const id of [CLICKABLE.venue, CLICKABLE.cluster, CLICKABLE.cell]) {
        m.on('mouseenter', id, () => { canvas.style.cursor = 'pointer' })
        m.on('mouseleave', id, () => { canvas.style.cursor = '' })
      }
      // A name and a plain-words kind follow the pointer over a pin.
      m.on('mousemove', CLICKABLE.venue, (event: MapLayerMouseEvent) => {
        const props = event.features?.[0]?.properties
        if (props && typeof props.label === 'string') setTip({ x: event.point.x, y: event.point.y, label: props.label, kind: String(props.kind), cited: props.cited === 1 })
      })
      m.on('mouseleave', CLICKABLE.venue, () => setTip(null))
      m.on('movestart', (event) => { if ((event as { originalEvent?: unknown }).originalEvent) { userMoved.current = true; mark(0) } })
      m.on('moveend', () => {
        if (!framed.current) return
        window.clearTimeout(hashTimer)
        hashTimer = window.setTimeout(() => {
          const hash = window.location.hash
          // Only this map's own view, or the stale create-screen marker, is replaced.
          if (hash && !hash.startsWith('#map=') && hash !== '#workspace/create') return
          const c = m.getCenter()
          history.replaceState(null, '', `${window.location.pathname}${window.location.search}${encodeMapHash({ lat: c.lat, lon: c.lng, zoom: m.getZoom() })}`)
        }, 600)
      })
      mapRef.current = m
    }).catch(() => { if (!cancelled) setStatus('failed') })

    return () => {
      cancelled = true
      window.clearTimeout(hashTimer)
      window.clearTimeout(basemapTimer)
      map?.remove()
      mapRef.current = null
    }
  }, [compose, location, mark])

  // --- Applied in place -------------------------------------------------------------
  useEffect(() => {
    const map = mapRef.current
    if (status !== 'ready' || !map) return
    for (const key of Object.keys(data) as (keyof OverlayData)[]) (map.getSource(key) as GeoJSONSource | undefined)?.setData(data[key])
  }, [status, data])

  useEffect(() => {
    const map = mapRef.current
    if (status !== 'ready' || !map) return
    for (const [group, ids] of Object.entries(LAYER_GROUPS) as [keyof OverlayVisibility, string[]][]) {
      for (const id of ids) if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', visible[group] ? 'visible' : 'none')
    }
  }, [status, visible])

  // Follow the studio's theme without recreating the map.
  useEffect(() => {
    const bump = () => setThemeTick((t) => t + 1)
    const observer = new MutationObserver(bump)
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    return () => observer.disconnect()
  }, [])
  useEffect(() => {
    const map = mapRef.current
    if (status !== 'ready' || !map || !themeTick) return
    map.setStyle(compose(), { diff: true })
  }, [status, themeTick, compose])

  // Frame the evidence when it arrives, unless the reader has moved the map
  // or a shared view of this same area was restored.
  useEffect(() => {
    const map = mapRef.current
    if (status !== 'ready' || !map || !dataBounds) return
    if (!framed.current) {
      framed.current = true
      const shared = initialHash.current
      if (shared && nearBounds(shared, dataBounds)) {
        map.jumpTo({ center: [shared.lon, shared.lat], zoom: shared.zoom })
        userMoved.current = true
        setNote('Restored the shared view from the link.')
        return
      }
      if (shared) setNote('The shared view in the link is not near this exploration’s evidence, so the evidence is framed instead.')
      map.fitBounds([[dataBounds.west, dataBounds.south], [dataBounds.east, dataBounds.north]], { padding: 56, maxZoom: 15, duration: 0 })
      return
    }
    if (!userMoved.current) fit(dataBounds)
    // boundsKey stands for dataBounds' value.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, boundsKey, fit])

  // --- Opening things -----------------------------------------------------------------
  // Evidence ids are renumbered when an answer is recomposed, so the open
  // venue is remembered by its Qloo identity too.
  const venueIdentity = useRef<string | null>(null)
  const selectVenue = useCallback((id: string | null) => {
    const item = id ? evidence.find((e) => e.id === id) : undefined
    venueIdentity.current = item ? item.entityId ?? item.label : null
    setVenueId(id); setCellIndex(null)
    if (id) mark(2)
  }, [mark, evidence])
  openVenue.current = (id: string) => { selectVenue(id); window.setTimeout(() => sideRef.current?.scrollTo?.({ top: 0 }), 0) }
  openCell.current = (index: number) => { setCellIndex(index); setVenueId(null) }
  const closeVenue = () => {
    const closing = venueId
    const fromList = Boolean(returnFocus.current?.dataset.venueId)
    returnFocus.current = null
    setVenueId(null)
    // Back to where the reader came from: the list entry (re-rendered once the
    // panel closes), or the map.
    window.setTimeout(() => {
      const entry = fromList && closing ? sideRef.current?.querySelector<HTMLElement>(`[data-venue-id="${CSS.escape(closing)}"]`) : null
      ;(entry ?? mapRef.current?.getCanvas())?.focus()
    }, 0)
  }
  const openFromList = (id: string, element: HTMLElement) => {
    returnFocus.current = element
    selectVenue(id)
    const p = plotted.find((x) => x.venue.id === id)
    if (p) flyTo(p.at)
  }
  // A venue that left the evidence (a removal was applied) closes its panel.
  useEffect(() => {
    if (!venueId) return
    const item = evidence.find((e) => e.id === venueId)
    if (!item || (item.entityId ?? item.label) !== venueIdentity.current) setVenueId(null)
  }, [evidence, venueId])
  useEffect(() => { setCellIndex(null) }, [points])

  const chooseDirection = (id: string) => { onSelect?.(id); mark(1) }
  const frameDirection = () => fit(boundsOf(citedPlotted.map((p) => p.at)))

  // --- Search: only among what the data supports ----------------------------------
  const targets = useMemo<SearchTarget[]>(() => [
    { kind: 'area', id: 'area', label: `${location} — all evidence` },
    ...candidates.map((c) => ({ kind: 'venue' as const, id: c.venue.id, label: c.venue.label })),
    ...concepts.map((c) => ({ kind: 'direction' as const, id: c.id, label: c.name })),
  ], [location, candidates, concepts])

  function search(event: FormEvent) {
    event.preventDefault()
    const hit = matchSearch(query, targets)
    mark(0)
    if (!query.trim()) { setNote(''); return }
    if (!hit) {
      setNote(`“${query.trim()}” is not in this exploration. The map moves only among ${location}, its venues and its directions. It cannot look up a new city — the browser has no geocoder — and it will never show another city’s data here. To explore another city, start a new brief for it.`)
      return
    }
    if (hit.kind === 'area') {
      if (dataBounds) { fit(dataBounds); setNote(`Framed all placed evidence for ${location}.`) }
      else setNote(`Nothing in this exploration has a verified coordinate yet, so the map cannot centre on ${location}. CultureForge does not guess where a city is.`)
      return
    }
    if (hit.kind === 'direction') {
      chooseDirection(hit.id); setFocus(true)
      const c = concepts.find((x) => x.id === hit.id)
      const b = boundsOf(plotted.filter((p) => c?.evidenceIds.includes(p.venue.id)).map((p) => p.at))
      fit(b)
      setNote(b ? `Showing the venues ${hit.label} cites.` : `${hit.label} cites no venue that could be placed on the map.`)
      return
    }
    selectVenue(hit.id)
    const p = plotted.find((x) => x.venue.id === hit.id)
    if (p) { flyTo(p.at); setNote(`Focused: ${hit.label}.`) }
    else {
      const placement = placements.get(hit.id)
      setNote(`${hit.label} is in the evidence but not on the map: ${placement?.state === 'not_plotted' ? placement.reason : 'it is still being located.'}`)
    }
  }

  // --- Rendering ------------------------------------------------------------------------
  const venue = venueId ? candidates.find((c) => c.venue.id === venueId) : undefined
  const cell = cellIndex != null ? points[cellIndex] : null
  const contextNote = !concepts.length ? 'No direction was supported, so there is no direction to show.'
    : !concept ? 'Choose a direction to show its venues.'
      : !citedPlotted.length ? `${concept.name} cites no venue that could be placed on the map.` : null
  const anyEvidence = plotted.length > 0 || points.length > 0
  const heatLegend = cells && <div className="ox-legend">
    <span className="ox-ramp" aria-hidden="true"/>
    <span className="ox-legend-ends"><span>lower</span><span>higher</span></span>
    <p>Colour shows relative {metric.name} among the {points.length} cells Qloo returned for <b>{cells.placeLabel}</b> inside {cells.within}. {metric.useAffinity ? '' : 'Affinity barely varies across these cells (a spread under 0.005), so popularity is shown instead. '}It is relative within this set — not demand, visitors or a site.</p>
  </div>

  return <figure className="ox" aria-labelledby={`${uid}-title`}>
    <figcaption className="ox-head">
      <div>
        <span className="small-cap"><span className="orange-dot"/> CULTURAL OPPORTUNITY EXPLORER</span>
        <h3 id={`${uid}-title`}>{location}</h3>
      </div>
      <span className="sample-label">{plotted.length} OF {candidates.filter((c) => c.eligible).length} VENUES PLACED · {points.length} QLOO CELLS</span>
    </figcaption>

    <JudgeHints done={done}/>

    {undo && <div className="ox-undo" role="status">
      <span>Applied: rebuilt without <b>{undo.label}</b>, from held evidence.</span>
      <button type="button" className="button button-secondary" onClick={undo.run}><RotateCcw size={14} aria-hidden="true"/> Undo</button>
    </div>}

    <div className="ox-tools">
      <form className="geo-search" role="search" onSubmit={search}>
        <label htmlFor={`${uid}-search`} className="geo-sr-only">Move to a place in this evidence</label>
        <Search size={14} aria-hidden="true"/>
        <input id={`${uid}-search`} type="search" list={`${uid}-targets`} value={query} placeholder="A venue, a direction, or the whole area"
          onChange={(event) => setQuery(event.target.value)} aria-describedby={`${uid}-note`}/>
        <datalist id={`${uid}-targets`}>{targets.map((t) => <option key={`${t.kind}-${t.id}`} value={t.label}/>)}</datalist>
        <button type="submit" className="button button-secondary">Go</button>
        <button type="button" className="button button-secondary" onClick={() => { userMoved.current = false; fit(dataBounds); setNote(dataBounds ? 'Framed all placed evidence.' : 'Nothing is placed yet, so there is nothing to frame.') }} disabled={!dataBounds}>
          <LocateFixed size={14} aria-hidden="true"/> Fit to evidence
        </button>
      </form>
      <p id={`${uid}-note`} className="geo-search-note" aria-live="polite">{note}</p>
      <DirectionPicker concepts={concepts} selectedId={selectedId} onSelect={chooseDirection} focus={focus} setFocus={setFocus}
        summary={{ cited: cited.size, plotted: citedPlotted.length, tags: concept ? concept.evidenceIds.filter((id) => evidence.some((e) => e.id === id && e.kind === 'tag')).length : 0, total: concept?.evidenceIds.length ?? 0 }}
        onFit={frameDirection} onOpen={concept && onOpenConcept ? () => onOpenConcept(concept) : undefined}/>
    </div>

    <div className="ox-body">
      <div className="ox-stage">
        {/* First in the tab order, though it floats over the map. */}
        {status !== 'failed' && <LayersPanel open={layersOpen} setOpen={setLayersOpen} visible={visible} setVisible={setVisible} counts={counts}
          heatLegend={heatLegend} cellsControl={cellsControl} contextNote={contextNote}/>}
        <div ref={containerRef} className="ox-canvas"/>
        {tip && <div className="ox-tip" style={{ left: tip.x + 14, top: tip.y + 14 }} role="presentation"><strong>{tip.label}</strong><span>{KIND_WORDS[tip.kind as keyof typeof KIND_WORDS] ?? tip.kind}{tip.cited ? ' · cited by this direction' : ''}</span><em>Click for details</em></div>}
        {status === 'ready' && plotted.length > 0 && <ul className="ox-keybar" aria-label="What the pins mean">
          <li><i className="ox-dot is-direct"/>Direct match</li><li><i className="ox-dot is-indirect"/>Related business</li><li><i className="ox-dot is-attraction"/>Cultural attraction</li><li><i className="ox-ring"/>Cited by this direction</li>
        </ul>}
        {status === 'loading' && <div className="ox-skeleton" role="status"><span/>Loading the street map…</div>}
        {status === 'failed' && <p className="ox-overlay" role="alert">This browser could not start the map (WebGL is unavailable or blocked). Every venue and its status is listed beside it.</p>}
        {status === 'ready' && !anyEvidence && geo.pending === 0 && <p className="ox-overlay is-soft">Nothing in this exploration has a verified coordinate yet, so the map is not centred on {location}. CultureForge does not guess where a city is. The venues and their reasons are listed beside the map.</p>}
        {geo.pending > 0 && <p className="ox-pill" role="status"><LoaderCircle size={13} className="spin" aria-hidden="true"/> Locating {geo.pending} venue{geo.pending === 1 ? '' : 's'}…</p>}
        {basemap.mode === 'grid' && <p className="ox-basemap-note" role="status">{basemap.reason} Showing a latitude/longitude grid instead; the evidence is unchanged. <button type="button" className="text-link" onClick={() => retryStreets.current()}>Try the street map again</button></p>}
      </div>

      <aside ref={sideRef} className={`ox-side${venue || cell ? ' is-sheet' : ''}`} aria-label="Venue detail">
        {venue ? <VenuePanel venue={venue.venue} kind={venue.kind} placement={placements.get(venue.venue.id) ?? { state: 'pending' }}
          citing={directionsCiting(venue.venue.id, concepts)} selectedId={selectedId} onSelectDirection={(id) => { chooseDirection(id); setFocus(true) }}
          onInspect={onInspect} onClose={closeVenue}>
          <RemovalExperiment venue={venue.venue} concepts={concepts} evidence={evidence} project={project} unsupported={removalUnsupported}
            onApply={onApplyRebuild} onRan={() => mark(3)}/>
        </VenuePanel> : cell ? <section className="ox-venue">
          <header className="ox-venue-head"><div>
            <span className="ox-kind is-cell">Qloo interest cell</span>
            <h3>Cell {metric.rank.get(cellIndex!)} of {points.length}, by {metric.name}</h3>
          </div><button type="button" className="icon-button" onClick={() => setCellIndex(null)} aria-label="Close cell detail">✕</button></header>
          <p className="ox-caveat">A geographic cell where Qloo reports affinity for {cells?.placeLabel}. It is not a venue, an address or a site.</p>
          <dl className="ox-values">
            <div><dt>Affinity</dt><dd>{cell.affinity != null ? cell.affinity.toFixed(4) : 'not returned'}</dd></div>
            <div><dt>Popularity</dt><dd>{cell.popularity != null ? cell.popularity.toFixed(4) : 'not returned'}</dd></div>
            {cell.geohash && <div><dt>Geohash</dt><dd>{cell.geohash}</dd></div>}
          </dl>
        </section> : venueList()}
      </aside>
    </div>

    <div className="ox-foot">
      <p>{basemap.mode === 'streets' ? '© OpenFreeMap © OpenMapTiles Data from OpenStreetMap. ' : 'No basemap is loaded. '}Interest cells: Qloo <code>where_popular</code>. Venue pins: the server geocodes the address Qloo returned with OpenStreetMap Nominatim — an address match, never a surveyed point.</p>
      <p className="ox-dim">Audience comparison is not offered on this map: Qloo’s interest cells are measured for one place, not for an audience, so there is no second audience’s cells to set beside these. The Scenario lab compares audiences with Qloo’s own A/B of cultural tags.</p>
    </div>
  </figure>

  function venueList() {
    const eligible = candidates.filter((c) => c.eligible).length
    return <div className="ox-list">
      <p className="ox-tiny">VENUES IN THIS EVIDENCE</p>
      {!candidates.length && <p className="ox-dim">Qloo returned no places for this brief, so there are no venues to place.</p>}
      {geo.error && <p className="ox-error" role="alert">{geo.error} <button type="button" className="text-link" onClick={geo.retry}>Try again</button></p>}
      {!geo.serverEnabled && <p className="ox-dim">Geocoding is switched off on this server, so only venues it already holds can be placed.</p>}
      {plotted.length > 0 && <>
        <h4>On the map <b>{plotted.length}</b></h4>
        <ul>{plotted.map((p) => <li key={p.venue.id}><button type="button" data-venue-id={p.venue.id} className={`ox-venue-btn${highlight && !cited.has(p.venue.id) ? ' is-dim' : ''}`} onClick={(e) => openFromList(p.venue.id, e.currentTarget)}>
          <i className={`ox-dot is-${p.kind}`} aria-hidden="true"/><span>{p.venue.label}</span><small>{KIND_WORDS[p.kind]}{cited.has(p.venue.id) ? ' · cited' : ''}</small>
        </button></li>)}</ul>
      </>}
      {geo.pending > 0 && <p className="ox-dim" role="status">Locating {geo.pending} of {eligible} venues on the server…</p>}
      {unplotted.length > 0 && <>
        <h4>Not on the map <b>{unplotted.length}</b></h4>
        <ul>{unplotted.map((c) => { const p = placements.get(c.venue.id); return <li key={c.venue.id}>
          <button type="button" data-venue-id={c.venue.id} className="ox-venue-btn is-unplotted" onClick={(e) => { returnFocus.current = e.currentTarget; selectVenue(c.venue.id) }}>
            <span>{c.venue.label}</span><small>not plotted: {p?.state === 'not_plotted' ? p.reason : ''}</small>
          </button></li> })}</ul>
      </>}
      {candidates.length > 0 && <p className="ox-dim">Pins are address matches from the server, not surveyed venue points.</p>}
    </div>
  }
}
