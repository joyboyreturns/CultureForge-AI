/**
 * The evidence drawn over the basemap.
 *
 *  - `cells`: Qloo interest cells, as a heatmap of relative affinity (or
 *    popularity, when affinity barely varies) and faint dots to click.
 *  - `venues`: geocoded venues, clustered. Direct matches are filled dots,
 *    indirect anchors are hollow rings, attractions carry a dark outline;
 *    colour and shape both differ, so the kinds survive colour-blindness.
 *  - `context`: the chosen direction's cited venues, as a halo.
 *  - `selected`: the venue or cell open in the panel.
 */
import type { LayerSpecification, SourceSpecification } from 'maplibre-gl'

export interface OverlayColors {
  cellLow: string; cellHigh: string; direct: string; indirect: string; attraction: string
  context: string; ink: string; surface: string
}
export interface OverlayData {
  cells: GeoJSON.FeatureCollection; venues: GeoJSON.FeatureCollection
  context: GeoJSON.FeatureCollection; selected: GeoJSON.FeatureCollection
}
export interface OverlayVisibility { heat: boolean; venues: boolean; context: boolean }

export const EMPTY: GeoJSON.FeatureCollection = { type: 'FeatureCollection', features: [] }

export const LAYER_GROUPS: Record<keyof OverlayVisibility, string[]> = {
  heat: ['cells-heat', 'cells-dot'],
  venues: ['venue-clusters', 'venue-cluster-count', 'venue-points'],
  context: ['context-halo'],
}

export const CLICKABLE = { venue: 'venue-points', cluster: 'venue-clusters', cell: 'cells-dot' }

export function readOverlayColors(element: Element): OverlayColors {
  const style = getComputedStyle(element)
  const read = (n: string, fallback: string) => style.getPropertyValue(n).trim() || fallback
  return {
    cellLow: read('--map-cell', '#8da875'),
    cellHigh: read('--map-cell-hot', '#c0612b'),
    direct: read('--map-competitor', '#9b3a2f'),
    indirect: read('--map-indirect', '#c79a2e'),
    attraction: read('--map-attraction', '#3f5f8a'),
    context: read('--map-context', '#18221b'),
    ink: read('--text', '#18221b'),
    surface: read('--surface', '#fbfbf5'),
  }
}

export function overlaySources(data: OverlayData): Record<string, SourceSpecification> {
  return {
    cells: { type: 'geojson', data: data.cells },
    venues: { type: 'geojson', data: data.venues, cluster: true, clusterRadius: 38, clusterMaxZoom: 15,
      clusterProperties: { cited: ['+', ['get', 'cited']] } },
    context: { type: 'geojson', data: data.context },
    selected: { type: 'geojson', data: data.selected },
  }
}

export function overlayLayers(c: OverlayColors, visible: OverlayVisibility, labels: boolean): LayerSpecification[] {
  const show = (on: boolean) => ({ visibility: on ? 'visible' as const : 'none' as const })
  const kindColor = ['match', ['get', 'kind'], 'direct', c.direct, 'indirect', c.indirect, 'attraction', c.attraction, c.ink] as never
  const dimmed = (on: number, off: number) => ['case', ['==', ['get', 'dim'], 1], off, on] as never
  const layers: LayerSpecification[] = [
    { id: 'cells-heat', type: 'heatmap', source: 'cells', maxzoom: 17, layout: show(visible.heat), paint: {
      'heatmap-weight': ['interpolate', ['linear'], ['get', 'heat'], 0, 0.15, 1, 1] as never,
      'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 8, 0.8, 15, 1.6] as never,
      'heatmap-radius': ['interpolate', ['exponential', 1.5], ['zoom'], 8, 14, 12, 34, 15, 70] as never,
      'heatmap-color': ['interpolate', ['linear'], ['heatmap-density'], 0, 'rgba(0,0,0,0)', 0.25, c.cellLow, 1, c.cellHigh] as never,
      'heatmap-opacity': 0.5,
    } },
    { id: 'cells-dot', type: 'circle', source: 'cells', layout: show(visible.heat), paint: {
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 8, 2, 15, 5] as never,
      'circle-color': c.cellHigh, 'circle-opacity': 0.55, 'circle-stroke-color': c.surface, 'circle-stroke-width': 1,
    } },
    { id: 'context-halo', type: 'circle', source: 'context', layout: show(visible.context), paint: {
      'circle-radius': 14, 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': c.context, 'circle-stroke-width': 1.6, 'circle-stroke-opacity': 0.85,
    } },
    { id: 'venue-clusters', type: 'circle', source: 'venues', filter: ['has', 'point_count'], layout: show(visible.venues), paint: {
      'circle-radius': ['step', ['get', 'point_count'], 14, 4, 18, 8, 22] as never,
      'circle-color': c.surface, 'circle-opacity': 0.94,
      'circle-stroke-color': ['case', ['>', ['get', 'cited'], 0], c.context, c.ink] as never,
      'circle-stroke-width': ['case', ['>', ['get', 'cited'], 0], 2.2, 1.2] as never,
    } },
    { id: 'venue-points', type: 'circle', source: 'venues', filter: ['!', ['has', 'point_count']], layout: show(visible.venues), paint: {
      'circle-radius': ['match', ['get', 'kind'], 'indirect', 6, 'attraction', 6.5, 7] as never,
      'circle-color': ['match', ['get', 'kind'], 'indirect', c.surface, kindColor] as never,
      'circle-stroke-color': ['match', ['get', 'kind'], 'indirect', c.indirect, 'attraction', c.ink, c.surface] as never,
      'circle-stroke-width': ['match', ['get', 'kind'], 'indirect', 3, 'attraction', 2.2, 1.6] as never,
      'circle-opacity': dimmed(1, 0.28), 'circle-stroke-opacity': dimmed(1, 0.28),
    } },
    { id: 'selected-ring', type: 'circle', source: 'selected', paint: {
      'circle-radius': 18, 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': c.ink, 'circle-stroke-width': 2.4,
    } },
  ]
  if (labels) {
    layers.splice(4, 0, { id: 'venue-cluster-count', type: 'symbol', source: 'venues', filter: ['has', 'point_count'], layout: {
      ...show(visible.venues), 'text-field': ['get', 'point_count_abbreviated'] as never, 'text-font': ['Noto Sans Regular'], 'text-size': 12, 'text-allow-overlap': true,
    }, paint: { 'text-color': c.ink } })
  }
  return layers
}
