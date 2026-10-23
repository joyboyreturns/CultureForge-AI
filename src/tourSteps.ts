export const TOUR_STEPS = [
  { id: 'welcome', title: 'Make a decision you can explain', target: '[data-tour="overview"]', screen: 'home',
    body: 'Follow a brief from Qloo observations to a business hypothesis, then challenge its evidence. The tour itself makes no Qloo or model requests.', action: 'Show the overview' },
  { id: 'brief', title: 'Start with a real audience and place', target: '[data-tour="brief"]', screen: 'create',
    body: 'Describe who you want to serve and where. Confirm the cultural signals Qloo resolves. Starting research is your choice; held evidence is reused.', action: 'Open the brief' },
  { id: 'difference', title: 'See what Qloo changed', target: '[data-tour="qloo-difference"]', screen: 'results',
    body: 'This strip lists what the answer rests on that only Qloo could supply: the places it returned, the extra questions the agent chose to ask it, which parts were written by rules or by a model, and whether anything pushed back on the lead direction.', action: 'Read the contribution strip' },
  { id: 'sources', title: 'Separate observations from proposals', target: '[data-tour="sources"]', screen: 'results',
    body: 'Qloo supplies the places and cultural signals. CultureForge proposes the direction. Open one source to inspect its request, returned excerpt and timing.', action: 'Inspect a source' },
  { id: 'challenge', title: 'Let the evidence disagree', target: '[data-tour="challenge"]', screen: 'results',
    body: 'Test the evidence to see a supported, contested or unproven anchor hypothesis. Read the claim and falsifier. Running a missing check can spend Qloo quota; the tour never runs it for you.', action: 'Find the evidence test' },
  { id: 'removal', title: 'Take away the convenient example', target: '[data-tour="removal"]', screen: 'results',
    body: 'Remove one returned venue at a time and compare the rebuilt answer. A source change and a changed direction are different outcomes. This uses held evidence only.', action: 'Open the removal test' },
  { id: 'pilot', title: 'Choose what you will test with people', target: '[data-tour="pilot"]', screen: 'results',
    body: 'Pick a direction, write a field experiment and define what would make you revise it. Your observations stay separate from Qloo evidence and never alter its verdict.', action: 'Open the decision notebook' },
] as const

export function tourNeedsEvidence(step: number) { return step >= 2 }
