import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': {
    target: 'http://127.0.0.1:8000',
    configure(proxy) {
      proxy.on('error', (_error, _request, response) => {
        if (response.headersSent) return
        response.writeHead(503, { 'Content-Type': 'application/json' })
        response.end(JSON.stringify({ detail: 'The CultureForge backend could not be reached. Start it on port 8000, then try again.' }))
      })
    },
  } } },
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
