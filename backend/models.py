from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

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
    # How many upstream requests this result actually cost. Evidence that was
    # already held cost nothing, and the number says so.
    transportRequests: Optional[int] = None

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


# ---------------------------------------------------------------------------
# The HTTP request contracts
#
# Every route that takes a body takes a typed one. A raw dict would let a
# malformed request through as something plausible — a string where a list of
# entities was meant becomes a list of single characters, and the request
# fails later, somewhere confusing, with an upstream error instead of a
# clear message about the field that was wrong.
# ---------------------------------------------------------------------------

class CompareAudiencesRequest(BaseModel):
    """Qloo's own A/B between two groups of entities."""
    model_config = ConfigDict(extra='forbid')
    groupA: list[str] = Field(min_length=1)
    groupB: list[str] = Field(min_length=1)
    targetType: str = 'place'
    limit: int = Field(default=12, ge=1, le=20)

class RankRequest(BaseModel):
    """Rank real Qloo entities by affinity for a signal set."""
    model_config = ConfigDict(extra='forbid')
    options: list[str] = Field(min_length=1)
    optionType: str = 'place'
    signals: list[str] = Field(default_factory=list)
    includeTags: list[str] = Field(default_factory=list)
    excludeTags: list[str] = Field(default_factory=list)
    signalLocation: Optional[str] = None
    demographic: Optional[str] = None
    limit: int = Field(default=6, ge=1, le=20)

class ShareRequest(BaseModel):
    """An exploration to freeze so a shared link reopens exactly it.

    Extra fields are allowed: a snapshot holds the whole exploration state,
    including parts of it that a later version of this API may add.
    """
    model_config = ConfigDict(extra='allow')
    projectId: Optional[str] = None
    project: Optional[dict] = None
    concepts: list[dict] = Field(default_factory=list)
    evidence: list[dict] = Field(default_factory=list)
    signals: list[dict] = Field(default_factory=list)
    trace: list[dict] = Field(default_factory=list)
    notice: Optional[str] = None


# ---------------------------------------------------------------------------
# The error contract
#
# Every failure answers with the same shape, so a caller can branch on the
# code instead of on the wording. `detail` stays as well, because the studio
# renders that string directly to the founder.
# ---------------------------------------------------------------------------

class ErrorBody(BaseModel):
    code: str
    message: str
    retryable: bool = False
    details: dict = Field(default_factory=dict)

class ErrorResponse(BaseModel):
    """The shape every failure uses."""
    detail: str
    error: ErrorBody
    requestId: str
