/**
 * MapLibre, loaded only when a map is drawn.
 *
 * The library is large, so GeoMap imports this module dynamically and the
 * rest of the studio never pays for it. The worker is bundled by Vite and its
 * URL handed to MapLibre, because the library's default (a file next to its
 * own module) does not exist once the app is bundled.
 *
 * No key and no third-party style file: the explorer's style is written in
 * code (src/components/map/style.ts) over OpenFreeMap tiles, and the
 * investigation view's interest plot draws no basemap at all.
 */
import { AttributionControl, Map as MapLibreMap, NavigationControl, ScaleControl, setWorkerUrl } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'

setWorkerUrl(workerUrl)

export { AttributionControl, MapLibreMap, NavigationControl, ScaleControl }
