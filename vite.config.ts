import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

/**
 * The API proxy.
 *
 * The same one serves the dev server and the built site, so `npm run
 * preview` reaches the backend exactly as `npm run dev` does. When the
 * backend is not running, the answer says so in words instead of hanging.
 */
/** The part of Node's ServerResponse the proxy error handler uses. */
type ProxyResponse = { headersSent: boolean; writeHead: (status: number, headers: Record<string, string>) => void; end: (body: string) => void }

const apiProxy = {
  '/api': {
    target: loadEnv('development', '.', 'CULTUREFORGE_').CULTUREFORGE_API_TARGET || 'http://127.0.0.1:8000',
    configure(proxy: { on: (event: 'error', listener: (error: unknown, request: unknown, response: ProxyResponse) => void) => void }) {
      proxy.on('error', (_error, _request, response) => {
        if (response.headersSent) return
        response.writeHead(503, { 'Content-Type': 'application/json' })
        response.end(JSON.stringify({ detail: 'The CultureForge backend could not be reached. Start it on port 8000, then try again.' }))
      })
    },
  },
}

export default defineConfig({
  plugins: [react()],
  server: { proxy: apiProxy },
  preview: { proxy: apiProxy },
  build: {
    rollupOptions: {
      // Paths are resolved against the project root.
      input: {
        // The marketing front page with the background video. Its "Open studio"
        // link loads the React app in place.
        index: 'index.html',
        // The concept studio, also reachable directly.
        studio: 'studio/index.html',
      },
    },
  },
})
