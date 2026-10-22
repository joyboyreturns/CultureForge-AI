import type { BusinessIntent, IntentState } from './contracts'

/** Plain-language labels for what Qloo did and did not give us for one business. */
export const STATE_LABEL: Record<IntentState, string> = {
  exact: 'Exact category match',
  near: 'Near category match',
  broader: 'Broader category substituted',
  tag_no_places: 'Category exists · no places returned here',
  unresolved: 'No matching Qloo category',
  not_retrieved: 'Not retrieved in this answer',
  provider_error: 'Qloo could not answer just now',
}

/** The reading is shown only when it tells the founder something: a hybrid, a specialisation, or any limit. */
export function intentIsWorthShowing(intent?: BusinessIntent | null): intent is BusinessIntent {
  if (!intent || !intent.components.length) return false
  return intent.hybrid || intent.substitutions.length > 0 || intent.source === 'model'
    || intent.components.some(component => component.modifiers.length > 0)
    || intent.evidence.some(entry => entry.state !== 'exact')
}

/** The same reading as lines of an exported record. Counts are counts of returned places. */
export function intentLines(intent?: BusinessIntent | null): string[] {
  if (!intent || !intent.components.length) return []
  const lines = ['## How the idea was read', `Idea: ${intent.original}`,
    `Businesses: ${intent.components.map(component => component.phrase).join(' + ')}${intent.hybrid ? ' (a combination)' : ''}`,
    `Reading: ${intent.source === 'model' ? 'model-assisted proposal, validated; Qloo chose every tag' : 'deterministic rules'}`]
  for (const entry of intent.evidence) {
    lines.push(`- **${entry.phrase}** — ${STATE_LABEL[entry.state]}; ${entry.placeCount} returned places${entry.tag ? `; Qloo tag: ${entry.tag.name ?? entry.tag.id}` : ''}`)
    for (const check of entry.modifiers) lines.push(`  "${check.word}" is mentioned by ${check.mentionedIn} of ${check.of} returned places.`)
    if (entry.message) lines.push(`  ${entry.message}`)
  }
  if (intent.overlap) lines.push(`Overlap: ${intent.overlap.statement}`)
  for (const note of intent.substitutions) lines.push(`Simplified or not verified: ${note}`)
  return [...lines, '']
}
