import type {
  Concept, CulturalSignal, Delivery, Evidence, GenerateResponse, ProjectRequest, TraceEvent,
} from './contracts'

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

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    const payload = await response.json().catch(() => ({})) as { detail?: unknown }
    throw new Error(detailMessage(payload, `Request failed (${response.status})`))
  }
  return await response.json() as T
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
export async function compareAudience(project: ProjectRequest, audience: string): Promise<AudienceComparison> {
  return postJson<AudienceComparison>('/api/projects/compare', { project, audience })
}

/** A candidate Qloo audience seed, before the founder confirms it. */
export interface TasteSeed {
  tagId: string
  label: string
  popularity: number | null
  type?: string | null
}

export interface TasteResolution {
  audience: string
  candidates: TasteSeed[]
  cached: boolean
  unresolved: unknown[]
}

/** Resolve an audience into candidate Qloo seeds, before any research runs. */
export async function resolveTaste(project: ProjectRequest, audience: string): Promise<TasteResolution> {
  return postJson<TasteResolution>('/api/taste/resolve', { project, audience })
}

/** A run of the research agent. */
export interface ResearchRun {
  runId: string
  status: 'running' | 'complete' | 'clarify' | 'failed'
  createdAt: number
  audience: string
  events: TraceEvent[]
  result: GenerateResponse | null
  clarification: { reason: string; question: string; field: string } | null
  error: string | null
  transportRequests: number
  workflowCalls: number
}

export async function startResearch(project: ProjectRequest, audience: string, seedTagIds: string[] = []): Promise<{ runId: string; status: string }> {
  return postJson('/api/research/runs', { project, audience, seedTagIds })
}

export async function fetchResearchRun(runId: string): Promise<ResearchRun> {
  const response = await fetch(`/api/research/runs/${runId}`)
  if (!response.ok) throw new Error('That research run is no longer available.')
  return await response.json() as ResearchRun
}

/** A shared, frozen exploration. */
export async function shareExploration(payload: unknown): Promise<{ snapshotId: string }> {
  return postJson('/api/explorations/share', payload)
}

export async function fetchSnapshot(snapshotId: string): Promise<GenerateResponse> {
  const response = await fetch(`/api/snapshots/${snapshotId}`)
  if (!response.ok) throw new Error('That snapshot is no longer available.')
  return await response.json() as GenerateResponse
}

/** Qloo's own A/B between two groups of entities. */
export interface AudienceComparisonResult {
  shared: {
    tagId: string | null
    label: string | null
    subtype: string | null
    popularity: number | null
    score: number | null
    groupAHits: number | null
    groupBHits: number | null
  }[]
  groupA: { tagId: string | null; label: string | null; subtype: string | null; popularity: number | null }[]
  groupB: { tagId: string | null; label: string | null; subtype: string | null; popularity: number | null }[]
  matchedEntities: number
  interpretation: unknown
  trace: TraceEvent
}

export async function compareAudiences(
  groupA: string[], groupB: string[], targetType = 'place'
): Promise<AudienceComparisonResult> {
  return postJson<AudienceComparisonResult>('/api/projects/compare/audiences', { groupA, groupB, targetType })
}

/** A tournament between real Qloo entities. */
export async function rankAnchors(
  options: string[], includeTags: string[], signalLocation?: string, optionType = 'place'
): Promise<{ ranked: { entityId: string | null; label: string | null; affinity: number | null; popularity: number | null; position: number }[]; trace: TraceEvent }> {
  return postJson('/api/projects/rank', { options, includeTags, signalLocation, optionType })
}

/** Rebuild the directions without a piece of evidence, using no new call. */
export async function recompose(
  project: ProjectRequest, excludeEntityIds: string[], excludeTagIds: string[] = []
): Promise<{ concepts: Concept[]; evidence: Evidence[]; dropped: number; notice: string }> {
  return postJson('/api/projects/recompose', { project, excludeEntityIds, excludeTagIds })
}

import { mockGenerate } from './mockData'
