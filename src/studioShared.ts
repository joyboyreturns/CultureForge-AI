import type { ProjectRequest } from './contracts'
import demoBriefs from '../shared/demoBriefs.json'

export type Screen = 'home' | 'create' | 'progress' | 'results' | 'compare'
export type Theme = 'dark' | 'light'
// The concept studio is read one section at a time, not as one long scroll.
// The sidebar and the section rail above the answer both move between these.
export type ResultsView = 'brief' | 'trace' | 'places' | 'directions' | 'test' | 'decide' | 'roots'
export const RESULT_VIEWS: { id: ResultsView; label: string; hint: string }[] = [
  { id: 'brief', label: 'Executive brief', hint: 'The answer, the lead direction and what Qloo changed.' },
  { id: 'trace', label: 'Evidence trace', hint: 'Which returned places and signals each decision rests on.' },
  { id: 'places', label: 'Places & signals', hint: 'How the idea was read, and the places Qloo returned for it.' },
  { id: 'directions', label: 'Directions', hint: 'Every proposed direction, its photograph, citations and limits.' },
  { id: 'test', label: 'Evidence test', hint: 'Hold each direction to its anchor and let the evidence disagree.' },
  { id: 'decide', label: 'Decision', hint: 'The agent’s findings, the comparison and a bounded analysis.' },
  { id: 'roots', label: 'Cultural roots', hint: 'Signals, the interest map, the constellation and more views.' },
]
// The example is a prepared brief that names its business idea and ships in shared/demoPack.json, so it
// opens instantly and its places match the idea. The landing page (main.js) runs the same one.
export const HERO_BRIEF_ID = 'tokyo-morning-bakery'
export const initial = (demoBriefs.briefs.find((brief) => brief.id === HERO_BRIEF_ID) ?? demoBriefs.briefs[0]).project as ProjectRequest
export const audiencePresets = ['Design-conscious Gen Z', 'Independent creatives', 'Young families', 'Mindful professionals']
export const objectives = ['Build a loyal community', 'Stand out in a crowded market', 'Attract a new audience', 'Create a memorable experience']
export const titles: Record<Screen, string> = { home: 'Overview', create: 'New exploration', progress: 'Agent workspace', results: 'Concept studio', compare: 'Scenario lab' }
