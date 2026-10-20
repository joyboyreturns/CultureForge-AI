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
  clarification: { reason: string; question: string; field: string; suggestion?: string | null } | null
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
export interface AnchorRanking {
  ranked: {
    entityId: string | null
    label: string | null
    affinity: number | null
    popularity: number | null
    position: number
  }[]
  /** The signal Qloo actually sent, taken from its own request. */
  signalsUsed: Record<string, unknown>
  trace: TraceEvent
}

export async function rankAnchors(
  options: string[], signalLocation?: string, demographic?: string, optionType = 'place'
): Promise<AnchorRanking> {
  return postJson<AnchorRanking>('/api/projects/rank', { options, signalLocation, demographic, optionType })
}

/** Rebuild the directions without a piece of evidence, using no new call. */
export async function recompose(
  project: ProjectRequest, excludeEntityIds: string[], excludeTagIds: string[] = []
): Promise<{ concepts: Concept[]; evidence: Evidence[]; dropped: number; notice: string }> {
  return postJson('/api/projects/recompose', { project, excludeEntityIds, excludeTagIds })
}

// ---------------------------------------------------------------------------
// Investigating a direction
// ---------------------------------------------------------------------------

/** One question an investigation can open. Each is a named Qloo workflow. */
export interface Facet {
  id: string
  workflow: string
  question: string
}

export interface InvestigationTool {
  facet: string
  workflow: string
  question?: string
  status: 'ok' | 'error' | 'needs_input'
  cached: boolean
  transportRequests: number
  durationMs?: number | null
  resultCount: number
  detail?: string
  acquiredAt: string
}

export interface GeoPoint {
  lat: number
  lon: number
  geohash?: string | null
  affinity?: number | null
  popularity?: number | null
}

export interface Investigation {
  directionId: string | null
  project: ProjectRequest
  facets: string[]
  questions: string[]
  reference: string | null
  within: string
  tools: InvestigationTool[]
  geography: {
    entityId: string | null
    within: string
    points: GeoPoint[]
    bounds: { west: number; south: number; east: number; north: number }
    metric: string
    note: string
  } | null
  tags: { id: string; name: string; type?: string | null; popularity?: number | null; affinity?: number | null }[]
  demographics: {
    entityId: string | null
    age: Record<string, number>
    gender: Record<string, number>
    note: string
  } | null
  findings: string[]
  limitations: string[]
  transportRequests: number
  investigatedAt: string
}

export async function listFacets(): Promise<{ facets: Facet[] }> {
  const response = await fetch('/api/facets')
  if (!response.ok) throw new Error('The open questions could not be loaded.')
  return await response.json() as { facets: Facet[] }
}

export async function investigate(payload: {
  project: ProjectRequest
  directionId?: string
  entityIds: string[]
  reference?: string
  within: string
  facets: string[]
  seedTagIds?: string[]
}): Promise<Investigation> {
  return postJson<Investigation>('/api/projects/investigate', payload)
}

/** The explorations this workspace has saved. */
export interface SavedExploration {
  id: string
  title: string
  brief: Record<string, unknown>
  createdAt: number
  updatedAt: number
  versions: { id: string; version: number; createdAt: number; note: string | null }[]
}

export async function listExplorations(): Promise<{ explorations: SavedExploration[] }> {
  const response = await fetch('/api/explorations')
  if (!response.ok) throw new Error('The saved explorations could not be loaded.')
  return await response.json() as { explorations: SavedExploration[] }
}

export async function fetchExploration(id: string): Promise<SavedExploration & { result: GenerateResponse }> {
  const response = await fetch(`/api/explorations/${id}`)
  if (!response.ok) throw new Error('That exploration is no longer saved.')
  return await response.json() as SavedExploration & { result: GenerateResponse }
}

export async function fetchUsage(): Promise<{ requests: number; upstreamCalls: number; byRoute: Record<string, number> }> {
  const response = await fetch('/api/usage')
  if (!response.ok) throw new Error('The usage could not be read.')
  return await response.json() as { requests: number; upstreamCalls: number; byRoute: Record<string, number> }
}

import { mockGenerate } from './mockData'
