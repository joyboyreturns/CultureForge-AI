export type BusinessType = 'Food & beverage' | 'Retail' | 'Hospitality' | 'Wellness' | 'Entertainment'
export interface ProjectRequest { businessType: BusinessType; businessIdea?: string; audience: string; location: string; budget: string; objectives: string[] }
export interface CulturalSignal { label: string; detail: string; score?: number | null; affinity?: number | null; category: string; provenance_id?: string | null }
export interface ExperienceMoment { title: string; description: string }

/** A single piece of retrieved Qloo evidence. Every value here came from Qloo. */
export interface Evidence {
  id: string
  /** entity: a returned place. tag: an audience seed. crossdomain: a non-place entity returned for the same tags, with no location. */
  kind: 'entity' | 'tag' | 'crossdomain'
  label: string
  entityId?: string | null
  entityType?: string | null
  tagId?: string | null
  affinity?: number | null
  popularity?: number | null
  rating?: number | null
  priceLevel?: number | null
  description?: string | null
  image?: string | null
  location?: string | null
  /** The street address Qloo returned for a place, verbatim. Qloo places carry no coordinates. */
  address?: string | null
  traceId?: string | null
  /** How this piece of evidence should be presented, derived from it by rule.
   *  It changes nothing about the evidence itself. */
  presentation?: EvidencePresentation | null
  relevance?: { version: string; evidenceClass?: EvidenceClass | null; relationship: 'direct' | 'indirect' | 'unknown' | 'excluded'; category: string; anchorEligible: boolean; geography: string; audience: string; confidence: string; reasons: string[] } | null
  /** A coordinate for the place itself, set only from a verified geocode of
   *  the address Qloo returned (backend/geocode.py). It is an address match,
   *  not a surveyed venue point, and is usually absent. */
  coordinates?: { lat: number; lon: number; source?: string | null } | null
}

/** What `POST /api/geo/venues` says about one venue's returned address. */
export type VenueGeocodeStatus = 'plotted' | 'not_found' | 'outside_city' | 'ambiguous' | 'no_address' | 'unavailable'
export interface VenueGeocode {
  id: string
  status: VenueGeocodeStatus
  lat?: number | null
  lon?: number | null
  /** The geocoder's own name for the matched place. */
  matched?: string | null
  source?: string | null
  precision?: string | null
  reason?: string | null
  cached?: boolean | null
}
export interface GeoVenuesResponse { results: VenueGeocode[]; enabled: boolean }

/** What a piece of evidence is to this brief, by CultureForge's relevance rule. */
export type EvidenceClass = 'direct_business' | 'indirect_business' | 'cultural_attraction' | 'audience_affinity' | 'unverified_geography' | 'unrelated'

/** The tidied view of one piece of evidence. Every string in it is either
 *  Qloo's own or a statement about what Qloo's own does not establish. */
export interface EvidencePresentation {
  version: string
  id?: string | null
  entityId?: string | null
  label?: string
  /** 'place', 'organisation' or 'seed', read from Qloo's own description. */
  identity: 'place' | 'organisation' | 'seed'
  /** The family the tag urn carries, for an audience seed. */
  tagFamily?: string
  tagBucket?: string
  identityNote: string
  /** A lead-in from the returned description, at a sentence boundary. */
  excerpt: string
  hasMore: boolean
  description?: string | null
  requestedLocation?: string | null
  returnedLocation?: string | null
  locationNote: string
  notes: string[]
}

/** One business proposal and the evidence it came from. Always a CultureForge interpretation. */
export interface Decision { id: string; field: string; proposal: string; evidenceIds: string[]; ruleId: string; origin: 'cultureforge_rule' }

/** A real Qloo tool call, with the harness's own timing. */
export interface TraceEvent {
  id: string
  step: string
  workflow?: string | null
  status: 'ok' | 'needs_input' | 'error' | 'cached' | 'skipped' | 'running'
  durationMs?: number | null
  correlationId?: string | null
  resultCount?: number | null
  detail?: string | null
  evidenceIds: string[]
  acquiredAt?: string | null
  /** The allowlisted request that was sent. Never raw subprocess output. */
  request?: { method?: string | null; path?: string | null; query?: unknown; endpoint?: string | null; documentation?: string | null } | null
  /** A short excerpt of what came back. */
  resultExcerpt?: string[] | null
}

/** How fresh the evidence is. The UI labels this honestly. */
export interface Delivery { kind: 'fresh' | 'cache' | 'snapshot' | 'mock'; acquiredAt?: string | null; servedAt?: string | null; expiresAt?: string | null; /** Upstream requests this result actually cost. */ transportRequests?: number | null; /** Where the answer was held: the backend's store, or this browser. */ cachedIn?: 'browser' | 'server' | null }

export interface Concept {
  id: string
  name: string
  tagline: string
  description: string
  /** Null for evidence-composed concepts: affinity does not measure business fit. */
  audienceFit?: number | null
  culturalRelevance?: number | null
  feasibility?: number | null
  budget: string
  investment: string
  signals: string[]
  accent: string
  image: string
  direction?: string | null
  imageAlt?: string | null
  personality?: string | null
  audienceRationale?: string | null
  implementationNote?: string | null
  moments?: ExperienceMoment[]
  evidenceIds: string[]
  decisions: Decision[]
  limitations: string[]
}

export interface ProvenanceMetadata { source: 'Qloo API' | 'Mock'; endpoint?: string | null; documentation?: string | null; resolved_tags: string[] }

export interface GenerateResponse {
  projectId: string
  project: ProjectRequest
  concepts: Concept[]
  signals: CulturalSignal[]
  dataMode: 'mock' | 'live'
  conceptMode: 'sample' | 'evidence_composed'
  notice: string
  outcome?: Outcome | null
  intent?: BusinessIntent | null
  provenance?: ProvenanceMetadata | null
  evidence: Evidence[]
  trace: TraceEvent[]
  delivery?: Delivery | null
  /** Which composer produced these directions. */
  composerVersion?: string | null
  agent?: AgentReport | null
}

export interface AgentStep {
  index: number
  tool: string
  arguments: Record<string, unknown>
  question: string
  reason: string
  status: 'ok' | 'rejected' | 'error' | 'skipped'
  detail: string
  upstreamRequests: number
  cached: boolean
  resultCount: number
}

export interface AgentReport {
  /** `frontier_ai` means the configured model planned and reflected; `model` names it. */
  mode: 'frontier_ai' | 'rules'
  model?: string | null
  status: 'complete' | 'limited' | 'skipped'
  plan?: {
    operation: 'remove_anchor' | 'finish'
    directionId?: string | null
    evidenceId?: string | null
    question: string
    reason: string
  } | null
  observation?: {
    operation: 'remove_anchor' | 'finish'
    status: 'ok' | 'unavailable' | 'rejected'
    question: string
    detail: string
    evidenceIds: string[]
    cached: boolean
    upstreamRequests: number
    result: Record<string, unknown>
  } | null
  reflection?: {
    recommendedDirectionId?: string | null
    recommendationRationale?: string
    whatWouldChangeTheConclusion?: string
    model?: string
    cached?: boolean
  } | null
  /** The plan-act-observe loop: every step the agent took, in order. */
  steps?: AgentStep[]
  /** The claims that passed the citation check. */
  analysis?: {
    claims: { statement: string; directionId?: string | null; citations: { id: string; label: string }[] }[]
    recommendedDirectionId?: string | null
    summary: string
    whatWouldChangeTheConclusion: string
    promptVersion?: string
  } | null
  /** Claims the validator rejected, and why. */
  rejectedClaims?: { statement: string; reason: string }[]
  /** True when the whole report was held from an earlier run of the same evidence. */
  cached?: boolean
  modelCalls: number
  stoppingReason: string
}

export type IntentState = 'exact' | 'near' | 'broader' | 'tag_no_places' | 'unresolved' | 'not_retrieved' | 'provider_error'

export interface IntentComponent {
  role: 'primary' | 'secondary'
  phrase: string
  categoryId: string
  categoryLabel: string
  status: 'canonical' | 'open_vocabulary' | 'unresolved'
  queries: string[]
  modifiers: string[]
  source: 'rules' | 'model'
}

export interface IntentPlace { entityId: string | null; name: string; location: string | null; evidenceClass: string | null; anchorEligible: boolean }

/** What Qloo returned for one business in the idea. Counts are counts of returned places, nothing else. */
export interface IntentEvidence {
  role: 'primary' | 'secondary'
  phrase: string
  categoryLabel: string
  state: IntentState
  queriesTried: string[]
  tag: { id: string; name: string | null; quality: 'exact' | 'near' | 'broader' | null } | null
  placeCount: number
  directCount: number
  places: IntentPlace[]
  modifiers: { word: string; mentionedIn: number; of: number }[]
  categoryOnly: boolean
  message: string
  code?: string
}

export interface BusinessIntent {
  original: string
  components: IntentComponent[]
  hybrid: boolean
  ambiguous: boolean
  clarification: string
  unused: string[]
  substitutions: string[]
  source: 'rules' | 'model'
  evidence: IntentEvidence[]
  overlap: { established: boolean; sharedPlaces: { entityId: string; name: string }[]; statement: string } | null
}

export type OutcomeState = 'supported' | 'promising_unverified' | 'contested' | 'insufficient_evidence' | 'provider_failure'

export interface Outcome {
  state: OutcomeState
  missing: string[]
  recovery: { action: string; label: string }[]
  counts: Record<string, number>
  category: string | null
  categoryLabel: string | null
}
