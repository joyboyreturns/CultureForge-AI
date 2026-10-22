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

/**
 * The browser's own cache of real answers.
 *
 * The backend already holds every piece of evidence for 24 hours, so a repeat
 * brief costs nothing upstream. This holds the *composed* answer for twelve
 * hours as well, so a reload paints the same exploration immediately instead
 * of waiting on a round trip, and so the label can say plainly that the
 * answer was held rather than freshly fetched.
 *
 * Only real answers are held. There is no mock fallback anywhere in this
 * module: if the backend cannot answer, the caller is told that.
 */
const CACHE_STORAGE_KEY = 'cultureforge-live-results-v2'
const CACHE_TTL_MS = 12 * 60 * 60 * 1000
const CACHE_MAX_ENTRIES = 12

interface CacheEntry { storedAt: number; response: GenerateResponse }

/** A stable key for a brief, so the same brief finds the same held answer. */
function briefKey(project: ProjectRequest): string {
  return [
    project.businessType,
    project.audience.trim(),
    project.location.trim(),
    project.budget,
    [...project.objectives].map((objective) => objective.trim()).sort().join('|'),
  ].join('::')
}

function readCache(): Record<string, CacheEntry> {
  try {
    const raw = localStorage.getItem(CACHE_STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) as Record<string, CacheEntry> : {}
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

function writeCache(key: string, entry: CacheEntry) {
  try {
    const cache = readCache()
    cache[key] = entry
    // Keep the newest few briefs. The rest are one round trip away anyway.
    const kept = Object.keys(cache)
      .sort((a, b) => cache[b].storedAt - cache[a].storedAt)
      .slice(0, CACHE_MAX_ENTRIES)
    const trimmed: Record<string, CacheEntry> = {}
    for (const item of kept) trimmed[item] = cache[item]
    localStorage.setItem(CACHE_STORAGE_KEY, JSON.stringify(trimmed))
  } catch { /* Storage can be disabled in private browser sessions. */ }
}

/** The held answer for this brief, if one is still fresh. */
export function heldResult(project: ProjectRequest): GenerateResponse | null {
  const entry = readCache()[briefKey(project)]
  if (!entry?.response) return null
  if (Date.now() - entry.storedAt > CACHE_TTL_MS) return null
  const held = entry.response.delivery
  return {
    ...entry.response,
    delivery: {
      kind: 'cache',
      acquiredAt: held?.acquiredAt ?? new Date(entry.storedAt).toISOString(),
      servedAt: new Date().toISOString(),
      expiresAt: new Date(entry.storedAt + CACHE_TTL_MS).toISOString(),
      // Holding it in this browser cost nothing upstream.
      transportRequests: 0,
      cachedIn: 'browser',
    },
  }
}

function rememberResult(project: ProjectRequest, response: GenerateResponse) {
  if (!response || response.dataMode !== 'live') return
  writeCache(briefKey(project), { storedAt: Date.now(), response })
}

/**
 * Hold a real answer that arrived by another route — a research run, say —
 * so the browser holds it too, not just the backend.
 */
export function rememberLiveResult(project: ProjectRequest, response: GenerateResponse) {
  rememberResult(project, response)
}

/**
 * Ask the backend for a real, evidence-backed answer.
 *
 * There is no mock fallback here on purpose. A founder who cannot reach the
 * API has to be told that, rather than shown a plausible fiction that would
 * look like data.
 */
export async function generateConcepts(project: ProjectRequest): Promise<GenerateResponse> {
  let response: Response
  try {
    response = await fetch('/api/projects/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(project) })
  } catch {
    throw new Error('The CultureForge backend could not be reached. It runs on port 8000 — start it, then try again.')
  }
  // A provider error, including a rejected Qloo call, stays visible. The
  // backend's own message says what went wrong.
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { detail?: unknown }
    throw new Error(detailMessage(body, `The backend returned ${response.status}.`))
  }
  const data = await response.json() as GenerateResponse
  rememberResult(project, data)
  return data
}

/** What the backend is actually doing: live Qloo, not live, or unreachable. */
export interface BackendStatus {
  mode: 'live' | 'mock' | 'offline'
  /** True when the backend can answer with real Qloo evidence right now. */
  ready: boolean
  reason: string | null
  workflows: string[]
}

export async function fetchHealth(): Promise<BackendStatus> {
  try {
    const response = await fetch('/api/health')
    if (!response.ok) {
      return { mode: 'offline', ready: false, reason: `The backend answered ${response.status}.`, workflows: [] }
    }
    const body = await response.json() as {
      dataMode?: 'live' | 'mock'
      providerReady?: boolean
      reason?: string | null
      workflows?: string[]
    }
    const live = body.dataMode === 'live'
    return {
      mode: live ? 'live' : 'mock',
      ready: live && body.providerReady !== false,
      reason: body.reason ?? null,
      workflows: body.workflows ?? [],
    }
  } catch {
    return { mode: 'offline', ready: false, reason: 'The backend could not be reached.', workflows: [] }
  }
}

/** A prepared example brief, and whether the server already holds its evidence. */
export interface ExampleBrief {
  id: string
  label: string
  project: ProjectRequest
  /** True when running it costs no upstream request. */
  held: boolean
}

/** The prepared example briefs. Asking costs no Qloo request. */
export async function fetchExamples(): Promise<ExampleBrief[]> {
  const response = await fetch('/api/examples')
  if (!response.ok) throw new Error(`The example briefs could not be listed (the backend answered ${response.status}).`)
  const body = await response.json() as { examples?: ExampleBrief[] }
  return body.examples ?? []
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
  const comparison = await postJson<AudienceComparison>('/api/projects/compare', { project, audience })
  // The same brief, seen through a different audience, is still a real answer.
  // Hold it, so reopening the studio does not spend the call again.
  rememberResult({ ...project, audience }, {
    projectId: `cf-${comparison.audience}`,
    project: { ...project, audience },
    concepts: comparison.concepts,
    signals: comparison.signals,
    evidence: comparison.evidence,
    trace: comparison.trace,
    delivery: comparison.delivery,
    notice: comparison.notice,
    provenance: {
      source: 'Qloo API',
      endpoint: 'qloo exec find_tags → recommend',
      resolved_tags: comparison.resolvedTags ?? [],
    },
    dataMode: 'live',
    conceptMode: 'evidence_composed',
  })
  return comparison
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

export async function fetchSnapshot(snapshotId: string): Promise<GenerateResponse & { challenge?: ChallengeResult }> {
  const response = await fetch(`/api/snapshots/${snapshotId}`)
  if (!response.ok) throw new Error('That snapshot is no longer available.')
  return await response.json() as GenerateResponse & { challenge?: ChallengeResult }
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
// Choosing what to show
// ---------------------------------------------------------------------------

/**
 * What the model chose from the evidence.
 *
 * The model returns ids; the server renders its own words. So `sentences`
 * here is Qloo's own text, never the model's.
 */
export interface EvidenceSelection {
  entityId: string
  sentences: string[]
  sentenceIds: string[]
  tagIds: string[]
}

export interface PresentationSelection {
  selections: Record<string, EvidenceSelection>
  /** 'model' when the model chose something usable; 'rules' otherwise. */
  source: 'model' | 'rules'
  model?: string | null
  reason?: string | null
  cached?: boolean
}

/**
 * Ask the configured model to choose which of Qloo's own sentences to lead with.
 *
 * It may only return ids, so it cannot write a fact. If it cannot be
 * reached, or answers with something that does not pass the validation, the
 * rules stay in place and nothing is lost.
 */
export async function selectPresentation(evidence: Evidence[]): Promise<PresentationSelection> {
  return postJson<PresentationSelection>('/api/evidence/presentation', { evidence })
}

// ---------------------------------------------------------------------------
// Testing a direction against the local evidence
// ---------------------------------------------------------------------------

export type Verdict = 'supported' | 'contested' | 'unproven'

export interface ChallengeCheck {
  name: string
  result: 'pass' | 'fail' | 'mixed'
  detail: string
  metric: Record<string, unknown>
}

export interface ChallengedDirection {
  directionId: string
  name: string
  verdict: Verdict
  /** What the verdict is about. It is narrow on purpose. */
  scope: string
  reason: string
  /** The claim this direction makes, and what would contradict it. */
  claim: string
  falsifier: string
  unprovenIf: string
  /** The order the directions arrived in, before the test. */
  arrivalOrder?: string[]
  /** The place the direction is actually built around, when the test used
   *  a different one. The concept itself was not rebuilt. */
  originalAnchor?: { entityId: string; label: string } | null
  /** True when the verdict answers for an alternative anchor rather than
   *  the direction's own reference. */
  isCounterfactual?: boolean
  /** The place the claim is held to. */
  anchor: { entityId: string | null; label: string | null } | null
  /** The other places it could have been held to. */
  alternatives: { entityId: string | null; label: string | null }[]
  checks: ChallengeCheck[]
  /** The anchor-fit-4 index: the rule's inputs and outcome, its confidence
   *  and its sensitivity. It holds positions and counts, never a score. */
  index?: {
    policy: string
    rule: string
    rankCheck: 'pass' | 'fail' | 'mixed' | null
    tagCheck: 'pass' | 'fail' | 'mixed' | null
    qualifyingTags?: number | null
    sampleSize: number
    minimumSample: number
    confidence: 'none' | 'low' | 'moderate'
    confidenceReason: string
    sensitivity: {
      stable: boolean
      checked: boolean
      rankCheck?: string
      changesWhenRemoved: { removed: string; rankCheck: string }[]
      alternativeAnchors: { entityId: string; label: string; position: number; rankCheck: 'pass' | 'fail' | 'mixed' }[]
    }
  }
  coverage: {
    venuesRetrieved: number
    venuesCited: number
    venuesCompared: number
    tagsUsed: number
    note: string
    howSignalsWereCounted?: string
  }
}

export interface ChallengeResult {
  directions: ChallengedDirection[]
  /** The order the evidence leaves the directions in. */
  order: string[]
  summary: string
  scope: string
  /** The policy that produced the verdicts, so they can be traced. */
  policyVersion: string
  whatThisIs: string
  profile: {
    demographic: string
    location: string
    signals: string[]
    /** Whether the brief actually named this demographic. */
    inferred?: boolean
    /** Who proposed the profile — CultureForge read it from the brief; Qloo
     *  converted it into the request signals it ranked against. */
    proposedBy?: string
    /** named: the brief named it. default: it did not. chosen: picked before the test. */
    source?: 'named' | 'default' | 'chosen'
    proposed?: string
    choices?: string[]
  }
  /** The order the directions arrived in, before the test. */
  arrivalOrder?: string[]
}

export interface ReplacementProbeResult {
  policyVersion: string
  directionId: string
  outcome: 'unresolved'
  hypothesis: string
  falsifier: string
  anchor: { entityId: string; label: string }
  sources: { entityId: string | null; label: string }[]
  replacements: Evidence[]
  observation: string
  scope: string
  query: Record<string, unknown>
  cached: boolean
  transportRequests: number
  limitations: string
}

/**
 * Test the directions against the local evidence.
 *
 * The brief is re-composed from evidence that is already held, so this costs
 * no Qloo call of its own until the checks run. The verdict is about local
 * cultural fit, and says so.
 */
export async function challengeDirections(
  project: ProjectRequest, directionId = '', anchorEntityId = '',
  revision?: { evidence: Evidence[]; concepts: Concept[]; resolvedTags: string[] },
  demographic = '',
): Promise<ChallengeResult> {
  return postJson<ChallengeResult>('/api/projects/challenge', {
    project, directionId, anchorEntityId, revision, demographic,
  })
}

/** The demographic profile the evidence test would use, before it runs. Costs no Qloo request. */
export interface ProfileProposal { demographic: string; named: boolean; choices: string[]; policyVersion: string }
export async function proposeProfile(audience: string): Promise<ProfileProposal> {
  return postJson<ProfileProposal>('/api/profile/propose', { audience })
}

export interface EvidenceAnalysisDirection {
  directionId: string
  hypothesis: string
  supportingEvidenceIds: string[]
  challengingEvidenceIds: string[]
  assumptions: string[]
  alternativeExplanation: string
  nextStep: 'compare_audiences' | 'rank_anchors' | 'remove_anchor' | 'investigate_direction' | 'none'
  nextStepReason: string
}
export interface EvidenceAnalysisResult {
  directions: EvidenceAnalysisDirection[]
  recommendedDirectionId?: string | null
  recommendationRationale: string
  whatWouldChangeTheConclusion: string
  model: string
  cached: boolean
  limitation: string
  coverage: Record<string, { numerator: number; denominator: number; decisionEvidenceIds: string[]; label: string }>
  confidence: Record<string, 'Supported' | 'Contested' | 'Unresolved'>
}

/** Explicitly analyze the exact brief, directions and evidence currently shown. */
export async function analyzeEvidence(
  project: ProjectRequest, evidence: Evidence[], concepts: Concept[], challenge?: ChallengeResult | null,
): Promise<EvidenceAnalysisResult> {
  const challengeSummary = challenge?.directions.map(({ directionId, verdict, reason }) => ({ directionId, verdict, reason })) ?? null
  return postJson<EvidenceAnalysisResult>('/api/projects/analyze', { project, evidence, concepts, challenge: challengeSummary })
}

/** Exclude the selected direction's primary cited place in one cached Qloo Insights query. */
export async function challengeReplacementProbe(
  project: ProjectRequest, directionId: string,
  revision: { evidence: Evidence[]; concepts: Concept[]; resolvedTags: string[] }
): Promise<ReplacementProbeResult> {
  return postJson<ReplacementProbeResult>('/api/projects/challenge-probe', {
    project, directionId, revision,
  })
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

/** Qloo interest cells for one place within an area: where its affinity is
 *  strong, as latitude/longitude cells. They are not venue coordinates. */
export interface InterestLayer {
  entityId: string
  within: string
  points: { lat: number; lon: number; geohash?: string | null; affinity?: number | null; popularity?: number | null }[]
  bounds: { west: number; south: number; east: number; north: number } | null
  note: string
  cached: boolean
  transportRequests: number
}
export async function fetchInterestCells(entityId: string, within: string): Promise<InterestLayer> {
  const body = await postJson<{ points: InterestLayer['points']; bounds: InterestLayer['bounds']; note: string; cached?: boolean; transportRequests?: number }>(
    '/api/qloo/where-popular', { entity: entityId, within, limit: 20 })
  return { entityId, within, points: body.points ?? [], bounds: body.bounds ?? null, note: body.note,
    cached: Boolean(body.cached), transportRequests: body.transportRequests ?? 0 }
}
