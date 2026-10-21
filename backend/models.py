import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

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
    id: str = Field(max_length=180)
    kind: Literal['entity', 'tag'] = 'entity'
    label: str = Field(max_length=400)
    entityId: Optional[str] = Field(default=None, max_length=300)
    entityType: Optional[str] = Field(default=None, max_length=120)
    tagId: Optional[str] = Field(default=None, max_length=300)
    affinity: Optional[float] = None
    popularity: Optional[float] = None
    rating: Optional[float] = None
    priceLevel: Optional[int] = None
    description: Optional[str] = Field(default=None, max_length=3000)
    image: Optional[str] = Field(default=None, max_length=2000)
    location: Optional[str] = Field(default=None, max_length=250)
    traceId: Optional[str] = Field(default=None, max_length=180)
    #: How this piece of evidence should be presented, derived from it by
    #: rule. It changes nothing about the evidence itself.
    presentation: Optional[dict] = None

class Decision(BaseModel):
    """One business proposal, and the evidence it was derived from.

    `origin` is always 'cultureforge_rule': these are CultureForge's business
    interpretations, not Qloo claims.
    """
    id: str = Field(max_length=180)
    field: str = Field(max_length=120)
    proposal: str = Field(max_length=1000)
    evidenceIds: list[str] = Field(default_factory=list, max_length=30)
    ruleId: str = Field(max_length=180)
    origin: Literal['cultureforge_rule'] = 'cultureforge_rule'

class TraceEvent(BaseModel):
    """A real tool call. The timings come from the Qloo harness execution block."""
    id: str
    step: str
    workflow: Optional[str] = None
    status: Literal['ok', 'needs_input', 'error', 'cached', 'skipped', 'running'] = 'ok'
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
    """How fresh the evidence is. The UI must label this honestly.

    `mock` stays in the union so a snapshot taken before the live-only
    switch still loads; nothing produces it any more.
    """
    kind: Literal['fresh', 'cache', 'snapshot', 'mock'] = 'fresh'
    acquiredAt: Optional[str] = None
    servedAt: Optional[str] = None
    expiresAt: Optional[str] = None
    # How many upstream requests this result actually cost. Evidence that was
    # already held cost nothing, and the number says so.
    transportRequests: Optional[int] = None
    # Where the answer was held: this server's evidence store, or the
    # browser. The studio says so rather than guessing.
    cachedIn: Optional[Literal['browser', 'server']] = None

class Concept(BaseModel):
    id: str = Field(max_length=180)
    name: str = Field(max_length=240)
    tagline: str = Field(max_length=500)
    description: str = Field(max_length=4000)
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
    evidenceIds: list[str] = Field(default_factory=list, max_length=50)
    decisions: list[Decision] = Field(default_factory=list, max_length=40)
    limitations: list[str] = Field(default_factory=list, max_length=30)

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


class EvidencePresentationRequest(BaseModel):
    """Ask the model to choose from the returned evidence what to show.

    The body is the evidence itself. Every piece of it is a value Qloo
    returned, so nothing here can introduce a fact.
    """
    evidence: list[Evidence] = Field(default_factory=list, max_length=50)


#: The Qloo entity types this API knows how to ask about.
ENTITY_TYPES = ('place', 'movie', 'tv_show', 'podcast', 'person', 'book',
                'music', 'game', 'brand', 'other')


class EntityRequest(BaseModel):
    """One named Qloo entity."""
    entity: str = Field(min_length=1, max_length=240)
    entityType: Optional[str] = Field(default=None, max_length=40)
    limit: int = Field(default=10, ge=1, le=50)


class EntityListRequest(BaseModel):
    """One to five named Qloo entities."""
    entities: list[str] = Field(min_length=1, max_length=5)
    entityType: Optional[str] = Field(default=None, max_length=40)
    limit: int = Field(default=10, ge=1, le=50)


class WherePopularRequest(EntityRequest):
    """One entity, and the area to map it within."""
    within: str = Field(min_length=1, max_length=160)
    limit: int = Field(default=20, ge=1, le=100)


class TrendsRequest(EntityListRequest):
    """Popularity over time, over a bounded date range.

    The dates are Qloo's own format, and a malformed one is rejected here
    rather than becoming a confusing upstream error later.
    """
    startDate: str = Field(default='', max_length=20)
    endDate: str = Field(default='', max_length=20)
    limit: int = Field(default=10, ge=1, le=50)

    @field_validator('startDate', 'endDate')
    @classmethod
    def _a_real_date(cls, value: str) -> str:
        if not value:
            return value
        try:
            datetime.date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError('Dates must be written as YYYY-MM-DD.') from exc
        return value


class InvestigationRequest(BaseModel):
    """Open the questions a direction has not answered yet."""
    project: ProjectRequest
    directionId: str = Field(default='', max_length=120)
    entityIds: list[str] = Field(default_factory=list, max_length=25)
    reference: str = Field(default='', max_length=120)
    within: str = Field(default='', max_length=160)
    facets: list[str] = Field(default_factory=list, max_length=10)
    seedTagIds: list[str] = Field(default_factory=list, max_length=10)


class ChallengeRevision(BaseModel):
    """The exploration exactly as it is on screen.

    The test has to answer about what the reader is looking at. If the app
    re-composed the brief, or the founder confirmed different audience seeds,
    the stored evidence is the evidence — and the test is about that.
    """
    model_config = ConfigDict(extra='forbid')
    evidence: list[Evidence] = Field(default_factory=list, max_length=50)
    concepts: list[Concept] = Field(default_factory=list, max_length=10)
    resolvedTags: list[str] = Field(default_factory=list, max_length=10)


class ChallengeRequest(BaseModel):
    """Test a direction against the local evidence."""
    project: ProjectRequest
    #: Which direction to test. Empty tests every direction in the answer.
    directionId: str = ''
    #: Hold the claim to a different anchor: the same direction, built around
    #: a different place. The verdict then answers for that one.
    anchorEntityId: str = ''
    #: The exploration as it stands. When it is sent, the test is about this
    #: evidence and not a fresh generation from the brief.
    revision: Optional[ChallengeRevision] = None


class ChallengeProbeRequest(BaseModel):
    """Run one bounded Qloo replacement probe against a direction on screen."""
    model_config = ConfigDict(extra='forbid')
    project: ProjectRequest
    directionId: str = Field(min_length=1, max_length=120)
    revision: ChallengeRevision


class EvidenceVerdictInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    directionId: str = Field(min_length=1, max_length=120)
    verdict: Literal['supported', 'contested', 'unproven']
    reason: str = Field(default='', max_length=600)


class EvidenceAnalysisRequest(BaseModel):
    """Analyze exactly the exploration currently shown in the studio."""
    model_config = ConfigDict(extra='forbid')
    project: ProjectRequest
    evidence: list[Evidence] = Field(default_factory=list, max_length=50)
    concepts: list[Concept] = Field(default_factory=list, max_length=10)
    challenge: Optional[list[EvidenceVerdictInput]] = Field(default=None, max_length=10)


class EvidenceAnalysisDirection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    directionId: str
    hypothesis: str = Field(min_length=8, max_length=500)
    supportingEvidenceIds: list[str] = Field(max_length=12)
    challengingEvidenceIds: list[str] = Field(max_length=12)
    assumptions: list[str] = Field(max_length=5)
    alternativeExplanation: str = Field(min_length=4, max_length=320)
    nextStep: Literal['compare_audiences', 'rank_anchors', 'remove_anchor', 'investigate_direction', 'none']
    nextStepReason: str = Field(min_length=4, max_length=240)


class EvidenceAnalysisOutput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    directions: list[EvidenceAnalysisDirection]
    recommendedDirectionId: Optional[str] = None
    recommendationRationale: str = Field(min_length=4, max_length=500)
    whatWouldChangeTheConclusion: str = Field(min_length=4, max_length=320)


class EvidenceAnalysisResult(EvidenceAnalysisOutput):
    model: str
    cached: bool = False
    limitation: str = 'This is an evidence-grounded cultural hypothesis, not a measure of demand or business success.'
    # Deterministic ratios disclose how much of the rule composer rationale has citations.
    coverage: dict[str, dict[str, object]] = Field(default_factory=dict)
    confidence: dict[str, Literal['Supported', 'Contested', 'Unresolved']] = Field(default_factory=dict)


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
