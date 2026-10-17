import catalog from '../shared/mockCatalog.json'
import type { Concept, GenerateResponse, ProjectRequest } from './contracts'

/** This catalog and its rules are shared with backend/mock_generator.py. No live evidence is inferred. */
function normalize(value: string): string { return value.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim() }
function fingerprint(value: string): number { return Array.from(normalize(value)).reduce((sum, char, index) => sum + char.charCodeAt(0) * (index + 1), 0) % 10000 }
const clamp = (value: number) => Math.max(65, Math.min(96, value))
function audienceLens(audience: string) {
  const words = ` ${normalize(audience)} `
  const ranked = catalog.profiles.map(profile => ({ profile, matches: profile.keywords.filter(keyword => words.includes(` ${keyword} `)) }))
  ranked.sort((a, b) => b.matches.length - a.matches.length)
  return ranked[0].matches.length ? ranked[0] : { profile: catalog.profiles[catalog.profiles.length - 1], matches: [] }
}
function investment(budget: string, factor: number): string {
  const [low, high] = budget.startsWith('Under') ? [12, 22] : budget.includes('100k+') ? [110, 170] : budget.includes('50k – $100k') ? [55, 88] : budget.includes('25k – $50k') ? [28, 46] : [25, 50]
  return `$${Math.round(low * factor)}–${Math.round(high * factor)}k pilot`
}
export function mockGenerate(project: ProjectRequest): GenerateResponse {
  const business = catalog.businesses[project.businessType]
  const { profile, matches } = audienceLens(project.audience)
  const seed = fingerprint(project.audience)
  const objective = project.objectives[0]?.trim() || 'Learn what resonates with this audience'
  const rationale = matches.length
    ? `Mock audience lens: ${profile.label}. Matched words: ${matches.join(', ')}. This is a template rule, not a measured audience preference.`
    : `No predefined audience keywords matched. These mock directions use your brief “${project.audience}” and a general pilot-and-feedback approach; no preferences are inferred.`
  const names = profile.names[project.businessType]
  const delivery = profile.delivery[project.businessType]
  const concepts: Concept[] = business.templates.map((template, index) => ({
    id: `${business.slug}-${profile.id}-${seed}-${index + 1}`,
    direction: String(index + 1).padStart(2, '0'),
    name: names[index], tagline: template.tagline,
    description: `${template.offering}${profile.id === 'general' ? ` Audience brief: “${project.audience}”.` : ''} ${delivery}`,
    audienceFit: clamp(profile.fits[index] + (seed + index * 3) % 5 - 2),
    culturalRelevance: clamp(84 + (seed + index * 7) % 11),
    feasibility: clamp(86 - index * 3 + (seed + index) % 5),
    budget: project.budget, investment: investment(project.budget, template.costFactor),
    signals: [profile.signals[0][0], template.theme, profile.signals[1][0]],
    accent: catalog.accents[index], image: template.image, imageAlt: template.imageAlt,
    personality: template.personality, audienceRationale: rationale,
    implementationNote: `Proposed pilot in ${project.location}. Test the objective “${objective}” within ${project.budget}. The displayed range is an illustrative pilot allowance, not a validated full-business startup cost.`,
    moments: template.moments.map((title, momentIndex) => ({ title, description: [
      `Prototype this signature moment with a small group drawn from your audience brief: ${project.audience}.`,
      delivery,
      `Trial this in ${project.location} and collect feedback against your objective: ${objective}.`,
    ][momentIndex] })),
  }))
  return {
    projectId: `cf-${Date.now().toString(36)}`, project, concepts,
    signals: profile.signals.map(([label, hypothesis], index) => ({ label, detail: `Mock hypothesis to test: ${hypothesis}. Audience brief: ${project.audience}.`, score: 78 + (seed + index * 5) % 15, category: 'Mock assumption', affinity: null, provenance_id: null })),
    dataMode: 'mock', conceptMode: 'sample',
    notice: `Rule-based mock generation for ${project.businessType} using the “${profile.label}” lens. Concepts, cultural hypotheses, scores, and pilot budgets are illustrative. Qloo is not connected to this mock run.`,
    provenance: { source: 'Mock', endpoint: null, documentation: null, resolved_tags: [] },
  }
}
