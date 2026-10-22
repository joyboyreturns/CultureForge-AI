/**
 * The basemap: OpenFreeMap vector tiles (OpenMapTiles schema, OpenStreetMap
 * data), drawn with a compact style written here so it follows the studio's
 * own light and dark themes. No key, no third-party style file.
 *
 * When the tiles cannot be reached the map falls back to the old
 * latitude/longitude grid, and the screen says so.
 */
import type { LayerSpecification, StyleSpecification } from 'maplibre-gl'
import type { Bounds } from './mapModel'
import { overlayLayers, overlaySources } from './layers'
import type { OverlayColors, OverlayData, OverlayVisibility } from './layers'

export const TILEJSON_URL = 'https://tiles.openfreemap.org/planet'
export const GLYPHS_URL = 'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf'
export const BASEMAP_SOURCE = 'openmaptiles'
const FONT = ['Noto Sans Regular']

export const EVIDENCE_ATTRIBUTION = 'Cells: Qloo · Pins: Nominatim address match'

export type Theme = 'dark' | 'light'
export type BasemapMode = 'streets' | 'grid'

const PALETTE: Record<Theme, Record<string, string>> = {
  dark: {
    background: '#16201a', water: '#1d3b4d', landcover: '#1b2b21', park: '#234a2f', landuse: '#18241d', building: '#27352c',
    minor: '#34443a', major: '#4b5d51', motorway: '#6b7a4a', casing: '#0d130f', boundary: '#6a7c6e',
    label: '#b8c6b9', labelMajor: '#e6eee3', halo: '#121a15', grid: '#2a362f',
  },
  light: {
    background: '#eef0e6', water: '#c6d7dc', landcover: '#e2e8d5', park: '#d8e4c9', landuse: '#e9ebe0', building: '#dfdfd3',
    minor: '#ffffff', major: '#fbf6e6', motorway: '#f0dfb4', casing: '#d2d6c8', boundary: '#a6ad9f',
    label: '#5d6a60', labelMajor: '#27322a', halo: '#f6f6ef', grid: '#d4dbd1',
  },
}

const name: unknown = ['coalesce', ['get', 'name:en'], ['get', 'name_en'], ['get', 'name']]

function basemapLayers(theme: Theme): LayerSpecification[] {
  const c = PALETTE[theme]
  const src = BASEMAP_SOURCE
  const width = (base: number, top: number) => ['interpolate', ['exponential', 1.6], ['zoom'], 10, base, 18, top] as unknown as number
  return [
    { id: 'bm-background', type: 'background', paint: { 'background-color': c.background } },
    { id: 'bm-landcover', type: 'fill', source: src, 'source-layer': 'landcover', paint: { 'fill-color': c.landcover, 'fill-opacity': 0.7 } },
    { id: 'bm-landuse', type: 'fill', source: src, 'source-layer': 'landuse', paint: { 'fill-color': c.landuse, 'fill-opacity': 0.6 } },
    { id: 'bm-park', type: 'fill', source: src, 'source-layer': 'park', paint: { 'fill-color': c.park, 'fill-opacity': 0.85 } },
    { id: 'bm-water', type: 'fill', source: src, 'source-layer': 'water', paint: { 'fill-color': c.water } },
    { id: 'bm-building', type: 'fill', source: src, 'source-layer': 'building', minzoom: 13, paint: { 'fill-color': c.building, 'fill-opacity': ['interpolate', ['linear'], ['zoom'], 13, 0, 14.5, 0.95] as unknown as number } },
    { id: 'bm-boundary', type: 'line', source: src, 'source-layer': 'boundary', filter: ['all', ['<=', ['get', 'admin_level'], 4], ['!=', ['get', 'maritime'], 1]] as never, minzoom: 3,
      paint: { 'line-color': c.boundary, 'line-width': 1, 'line-dasharray': [3, 2] } },
    { id: 'bm-road-minor', type: 'line', source: src, 'source-layer': 'transportation', minzoom: 12,
      filter: ['match', ['get', 'class'], ['minor', 'service', 'track', 'path'], true, false] as never,
      layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': c.minor, 'line-width': width(0.4, 9) } },
    { id: 'bm-road-major-casing', type: 'line', source: src, 'source-layer': 'transportation',
      filter: ['match', ['get', 'class'], ['primary', 'secondary', 'tertiary', 'trunk', 'motorway'], true, false] as never,
      layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': c.casing, 'line-width': width(1.2, 16) } },
    { id: 'bm-road-major', type: 'line', source: src, 'source-layer': 'transportation',
      filter: ['match', ['get', 'class'], ['primary', 'secondary', 'tertiary', 'trunk'], true, false] as never,
      layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': c.major, 'line-width': width(0.8, 13) } },
    { id: 'bm-road-motorway', type: 'line', source: src, 'source-layer': 'transportation',
      filter: ['==', ['get', 'class'], 'motorway'] as never,
      layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': c.motorway, 'line-width': width(1, 14) } },
    { id: 'bm-rail', type: 'line', source: src, 'source-layer': 'transportation', minzoom: 12,
      filter: ['match', ['get', 'class'], ['rail', 'transit'], true, false] as never,
      paint: { 'line-color': c.boundary, 'line-width': 1, 'line-dasharray': [2, 2], 'line-opacity': 0.7 } },
    { id: 'bm-road-label', type: 'symbol', source: src, 'source-layer': 'transportation_name', minzoom: 14,
      layout: { 'symbol-placement': 'line', 'text-field': name as never, 'text-font': FONT, 'text-size': 11 },
      paint: { 'text-color': c.label, 'text-halo-color': c.halo, 'text-halo-width': 1.4 } },
    { id: 'bm-place-label', type: 'symbol', source: src, 'source-layer': 'place',
      filter: ['match', ['get', 'class'], ['city', 'town', 'suburb', 'neighbourhood', 'quarter'], true, false] as never,
      layout: { 'text-field': name as never, 'text-font': FONT, 'text-max-width': 8,
        'text-size': ['match', ['get', 'class'], 'city', 15, 'town', 13, 11] as never },
      paint: { 'text-color': ['match', ['get', 'class'], ['city', 'town'], c.labelMajor, c.label] as never, 'text-halo-color': c.halo, 'text-halo-width': 1.6 } },
  ]
}

/** A latitude/longitude grid, so a map with no basemap can still be read. */
export function graticule(bounds: Bounds | null): GeoJSON.FeatureCollection {
  const b = bounds ?? { west: -180, east: 180, south: -80, north: 80 }
  const span = Math.max(b.east - b.west, b.north - b.south, 0.001)
  const steps = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 30]
  const step = steps.find((s) => span / s <= 5) ?? 30
  const pad = step * 8
  const west = Math.max(-180, Math.floor((b.west - pad) / step) * step)
  const east = Math.min(180, Math.ceil((b.east + pad) / step) * step)
  const south = Math.max(-85, Math.floor((b.south - pad) / step) * step)
  const north = Math.min(85, Math.ceil((b.north + pad) / step) * step)
  const features: GeoJSON.Feature[] = []
  for (let lon = west; lon <= east + 1e-9; lon += step) features.push({ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: [[lon, south], [lon, north]] } })
  for (let lat = south; lat <= north + 1e-9; lat += step) features.push({ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: [[west, lat], [east, lat]] } })
  return { type: 'FeatureCollection', features }
}

/** The whole style: the basemap (or the grid) with the evidence on top. */
export function composeStyle({ mode, theme, colors, data, visible, bounds }: {
  mode: BasemapMode; theme: Theme; colors: OverlayColors; data: OverlayData; visible: OverlayVisibility; bounds: Bounds | null
}): StyleSpecification {
  const c = PALETTE[theme]
  const streets = mode === 'streets'
  return {
    version: 8,
    ...(streets ? { glyphs: GLYPHS_URL } : {}),
    sources: {
      ...(streets
        ? { [BASEMAP_SOURCE]: { type: 'vector', url: TILEJSON_URL } }
        : { grid: { type: 'geojson', data: graticule(bounds) } }),
      ...overlaySources(data),
    },
    layers: [
      ...(streets ? basemapLayers(theme) : [
        { id: 'bm-background', type: 'background', paint: { 'background-color': c.background } } as LayerSpecification,
        { id: 'bm-grid', type: 'line', source: 'grid', paint: { 'line-color': c.grid, 'line-width': 1, 'line-dasharray': [2, 4] } } as LayerSpecification,
      ]),
      ...overlayLayers(colors, visible, streets),
    ],
  }
}
