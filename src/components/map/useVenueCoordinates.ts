import { useCallback, useEffect, useMemo, useState } from 'react'
import type { VenueGeocode } from '../../contracts'
import { geocodeVenues } from '../../api'
import { geocodeBatches, geocodeKey, isDefinitive, normaliseGeocode } from './mapModel'
import type { VenueCandidate } from './mapModel'

/**
 * Locate the venues once, lazily, when the map opens.
 *
 * Definitive answers (plotted, not found, outside the city, ambiguous) are
 * held in memory for the life of the page, keyed by city, venue and address,
 * so reopening the map or switching directions never asks again. A transport
 * failure is not held: it is shown, with a retry.
 */
const held = new Map<string, VenueGeocode>()

export function useVenueCoordinates(candidates: VenueCandidate[], city: string) {
  const [results, setResults] = useState<Record<string, VenueGeocode>>({})
  const [pending, setPending] = useState(0)
  const [error, setError] = useState('')
  const [serverEnabled, setServerEnabled] = useState(true)
  const [attempt, setAttempt] = useState(0)

  const signature = useMemo(() => candidates.map((c) => `${c.venue.id}:${c.venue.address ?? ''}:${c.eligible ? 1 : 0}`).join('|'), [candidates])

  useEffect(() => {
    // What is already held is shown at once.
    const known: Record<string, VenueGeocode> = {}
    for (const c of candidates) {
      const hit = c.venue.address ? held.get(geocodeKey(city, c.venue.id, c.venue.address)) : undefined
      if (hit) known[c.venue.id] = hit
    }
    setResults(known)
    setError('')
    const batches = geocodeBatches(candidates, city, (id, address) => held.has(geocodeKey(city, id, address)))
    const total = batches.reduce((n, b) => n + b.length, 0)
    setPending(total)
    if (!total) return
    const controller = new AbortController()
    ;(async () => {
      for (const batch of batches) {
        try {
          const response = await geocodeVenues(batch, controller.signal)
          if (controller.signal.aborted) return
          setServerEnabled(response.enabled)
          const answered: Record<string, VenueGeocode> = {}
          for (const raw of response.results) {
            const row = normaliseGeocode(raw)
            const sent = row && batch.find((v) => v.id === row.id)
            if (!row || !sent) continue
            answered[row.id] = row
            if (isDefinitive(row)) held.set(geocodeKey(city, sent.id, sent.address), row)
          }
          // A venue the server did not answer for is unresolved, not plotted.
          for (const v of batch) if (!answered[v.id]) answered[v.id] = { id: v.id, status: 'unavailable', reason: 'The server returned no answer for this venue.' }
          setResults((current) => ({ ...current, ...answered }))
        } catch (caught) {
          if (controller.signal.aborted) return
          setError(caught instanceof Error ? caught.message : 'The venues could not be located.')
          const failed: Record<string, VenueGeocode> = {}
          for (const v of batch) failed[v.id] = { id: v.id, status: 'unavailable', reason: 'The geocoding request failed; nothing was placed.' }
          setResults((current) => ({ ...current, ...failed }))
        }
        setPending((n) => Math.max(0, n - batch.length))
      }
    })()
    return () => controller.abort()
    // `signature` stands for the candidates' identity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature, city, attempt])

  const retry = useCallback(() => setAttempt((n) => n + 1), [])
  return { results, pending, error, serverEnabled, retry }
}
