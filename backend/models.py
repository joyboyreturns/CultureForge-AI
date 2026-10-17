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

class Concept(BaseModel):
    id: str
    name: str
    tagline: str
    description: str
    audienceFit: int
    culturalRelevance: int
    feasibility: int
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
    conceptMode: Literal['sample'] = 'sample'
    notice: str
    provenance: Optional[ProvenanceMetadata] = None
