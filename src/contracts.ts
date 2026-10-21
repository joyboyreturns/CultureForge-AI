export type BusinessType = 'Food & beverage' | 'Retail' | 'Hospitality' | 'Wellness' | 'Entertainment'
export interface ProjectRequest { businessType: BusinessType; audience: string; location: string; budget: string; objectives: string[] }
export interface CulturalSignal { label: string; detail: string; score?: number | null; affinity?: number | null; category: string; provenance_id?: string | null }
export interface ExperienceMoment { title: string; description: string }

/** A single piece of retrieved Qloo evidence. Every value here came from Qloo. */
export interface Evidence {
  id: string
  kind: 'entity' | 'tag'
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
  traceId?: string | null
  /** How this piece of evidence should be presented, derived from it by rule.
   *  It changes nothing about the evidence itself. */
  presentation?: EvidencePresentation | null
}

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
  provenance?: ProvenanceMetadata | null
  evidence: Evidence[]
  trace: TraceEvent[]
  delivery?: Delivery | null
  /** Which composer produced these directions. */
  composerVersion?: string | null
}
