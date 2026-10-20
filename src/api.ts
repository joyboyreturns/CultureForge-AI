import type { Concept, CulturalSignal, Delivery, Evidence, GenerateResponse, ProjectRequest, TraceEvent } from './contracts'
import { mockGenerate } from './mockData'

/**
 * Extract a human-readable message from an error body.
 *
 * `detail` is normally a string, but FastAPI's validation errors arrive as a
 * list of objects. Rendering that list directly would show the user a raw
 * Python dict dump, so flatten it into "field: message" pairs.
 */
function detailMessage(body: unknown, fallback: string): string {
  const detail = (body as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail)) {
    const parts = detail.map((entry) => {
      const item = entry as { loc?: unknown[]; msg?: string }
      const where = Array.isArray(item.loc) ? item.loc.filter((part) => part !== 'body').join('.') : ''
      const message = item.msg ?? 'invalid value'
      return where ? `${where}: ${message}` : message
    })
    if (parts.length) return parts.join('; ')
  }
  return fallback
}

/** Provider boundary: replace MockCultureProvider with a documented Qloo adapter when credentials/API access are ready. */
export async function generateConcepts(project: ProjectRequest): Promise<GenerateResponse> {
  let response: Response
  try { response = await fetch('/api/projects/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(project) }) }
  catch { return mockGenerate(project) }
  // Vite uses 503 only when its FastAPI proxy cannot connect; provider errors
  // (including a configured Qloo failure) remain visible to the user.
  if (response.status === 503) return mockGenerate(project)
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { detail?: unknown }
    throw new Error(detailMessage(body, `API returned ${response.status}`))
  }
  return await response.json() as GenerateResponse
}

/** Report whether the backend is live and which provider it is using. */
export async function fetchHealth(): Promise<'live' | 'mock' | 'offline'> {
  try {
    const response = await fetch('/api/health')
    if (!response.ok) return 'offline'
    const body = await response.json() as { dataMode?: 'live' | 'mock' }
    return body.dataMode === 'live' ? 'live' : 'mock'
  } catch {
    return 'offline'
  }
}

/** The payload the scenario lab needs to re-research a brief for another audience. */
export interface AudienceComparison {
  audience: string
  concepts: Concept[]
  evidence: Evidence[]
  signals: CulturalSignal[]
  trace: TraceEvent[]
  delivery: Delivery | null
  resolvedTags: string[]
  notice: string
}

/**
 * Re-research the same brief for a different audience, with real Qloo calls.
 *
 * The scenario lab used to shift a locally computed score. For an
 * evidence-composed exploration that would be a lie, so this re-runs the same
 * two Qloo workflows against the new audience and returns fresh evidence.
 */
export async function compareAudience(
  project: ProjectRequest,
  audience: string
): Promise<AudienceComparison> {
  const response = await fetch('/api/projects/compare', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project, audience }),
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { detail?: unknown }
    throw new Error(detailMessage(body, `Comparison failed (${response.status})`))
  }
  return await response.json() as AudienceComparison
}
