from typing import Literal, Optional
from pydantic import BaseModel, Field

BusinessType = Literal['Food & beverage', 'Retail', 'Hospitality', 'Wellness', 'Entertainment']

class ProjectRequest(BaseModel):
    businessType: BusinessType
    audience: str = Field(min_length=2, max_length=240)
    location: str = Field(min_length=2, max_length=160)
    budget: str
    objectives: list[str] = Field(default_factory=list)

class CulturalSignal(BaseModel):
    label: str
    detail: str
    score: Optional[int] = None
    affinity: Optional[float] = None
    category: str
    provenance_id: Optional[str] = None

class ExperienceMoment(BaseModel):
    title: str
    description: str

class Evidence(BaseModel):
    """A single piece of retrieved Qloo evidence.

    Everything here is a value Qloo returned. CultureForge never invents an
    entity, a metric, or a location.
    """
    id: str
    kind: Literal['entity', 'tag'] = 'entity'
    label: str
    entityId: Optional[str] = None
    entityType: Optional[str] = None
    tagId: Optional[str] = None
    affinity: Optional[float] = None
    popularity: Optional[float] = None
    rating: Optional[float] = None
    priceLevel: Optional[int] = None
    description: Optional[str] = None
    image: Optional[str] = None
    location: Optional[str] = None
    traceId: Optional[str] = None

class Decision(BaseModel):
    """One business proposal, and the evidence it was derived from.

    `origin` is always 'cultureforge_rule': these are CultureForge's business
    interpretations, not Qloo claims.
    """
    id: str
    field: str
    proposal: str
    evidenceIds: list[str] = Field(default_factory=list)
    ruleId: str
    origin: Literal['cultureforge_rule'] = 'cultureforge_rule'

class TraceEvent(BaseModel):
    """A real tool call. The timings come from the Qloo harness execution block."""
    id: str
    step: str
    workflow: Optional[str] = None
    status: Literal['ok', 'needs_input', 'error', 'cached', 'skipped'] = 'ok'
    durationMs: Optional[int] = None
    correlationId: Optional[str] = None
    resultCount: Optional[int] = None
    detail: Optional[str] = None
    evidenceIds: list[str] = Field(default_factory=list)
    acquiredAt: Optional[str] = None
    # The allowlisted request that was sent, and a short excerpt of what came
    # back. Never the raw subprocess output, which can carry credentials.
    request: Optional[dict] = None
    resultExcerpt: Optional[list[str]] = None

class Delivery(BaseModel):
    """How fresh the evidence is. The UI must label this honestly."""
    kind: Literal['fresh', 'cache', 'snapshot', 'mock'] = 'mock'
    acquiredAt: Optional[str] = None
    servedAt: Optional[str] = None
    expiresAt: Optional[str] = None

class Concept(BaseModel):
    id: str
    name: str
    tagline: str
    description: str
    audienceFit: Optional[int] = None
    culturalRelevance: Optional[int] = None
    feasibility: Optional[int] = None
    budget: str
    investment: str
    signals: list[str]
    accent: str
    image: str
    direction: Optional[str] = None
    imageAlt: Optional[str] = None
    personality: Optional[str] = None
    audienceRationale: Optional[str] = None
    implementationNote: Optional[str] = None
    moments: list[ExperienceMoment] = Field(default_factory=list)
    # Evidence-backed concepts (conceptMode='evidence_composed') carry these.
    evidenceIds: list[str] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

class ProvenanceMetadata(BaseModel):
    source: Literal['Qloo API', 'Mock']
    endpoint: Optional[str] = None
    documentation: Optional[str] = None
    resolved_tags: list[str] = []

class GenerateResponse(BaseModel):
    projectId: str
    project: ProjectRequest
    concepts: list[Concept]
    signals: list[CulturalSignal]
    dataMode: Literal['mock', 'live']
    conceptMode: Literal['sample', 'evidence_composed'] = 'sample'
    notice: str
    provenance: Optional[ProvenanceMetadata] = None
    evidence: list[Evidence] = Field(default_factory=list)
    trace: list[TraceEvent] = Field(default_factory=list)
    delivery: Optional[Delivery] = None
    # Which composer produced these directions, so an old snapshot is never
    # mistaken for a current one.
    composerVersion: Optional[str] = None

class CompareRequest(BaseModel):
    """Re-research a brief for a different audience."""
    project: ProjectRequest
    audience: str = Field(min_length=2, max_length=240)
    # When the founder confirmed the audience seeds, the research uses exactly
    # these instead of resolving the audience again.
    seedTagIds: list[str] = Field(default_factory=list)

class RecomposeRequest(BaseModel):
    """Rebuild the directions without a piece of the evidence."""
    project: ProjectRequest
    excludeEntityIds: list[str] = Field(default_factory=list)
    excludeTagIds: list[str] = Field(default_factory=list)
