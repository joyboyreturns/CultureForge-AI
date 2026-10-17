export type BusinessType = 'Food & beverage' | 'Retail' | 'Hospitality' | 'Wellness' | 'Entertainment'
export interface ProjectRequest { businessType: BusinessType; audience: string; location: string; budget: string; objectives: string[] }
export interface CulturalSignal { label: string; detail: string; score?: number | null; affinity?: number | null; category: string; provenance_id?: string | null }
export interface ExperienceMoment { title: string; description: string }
export interface Concept { id: string; name: string; tagline: string; description: string; audienceFit: number; culturalRelevance: number; feasibility: number; budget: string; investment: string; signals: string[]; accent: string; image: string; direction?: string | null; imageAlt?: string | null; personality?: string | null; audienceRationale?: string | null; implementationNote?: string | null; moments?: ExperienceMoment[] }
export interface ProvenanceMetadata { source: 'Qloo API' | 'Mock'; endpoint?: string | null; documentation?: string | null; resolved_tags: string[] }
export interface GenerateResponse { projectId: string; project: ProjectRequest; concepts: Concept[]; signals: CulturalSignal[]; dataMode: 'mock' | 'live'; conceptMode: 'sample'; notice: string; provenance?: ProvenanceMetadata | null }
