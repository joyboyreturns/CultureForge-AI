import { ArrowRight } from 'lucide-react'
import type { ClarificationAsk } from '../api'

const HEADLINE: Record<string, string> = {
  UNSUPPORTED_CATEGORY: 'Qloo has no category for this business.',
  AMBIGUOUS_IDEA: 'Which business do you mean?',
  CATEGORY_NO_PLACES: 'Qloo knows this category, but returned no places for it here.',
}

/** Every button here does something: it changes the brief and runs it, or puts the cursor where the fix is. */
export function Clarification({ ask, onUseIdea, onUseLocation, onEditField }: {
  ask: ClarificationAsk
  onUseIdea: (value: string) => void
  onUseLocation: (value: string) => void
  onEditField: (field: 'businessIdea' | 'location') => void
}) {
  const field = ask.field === 'location' ? 'location' : ask.field === 'businessIdea' ? 'businessIdea' : null
  return <div className="clarification" role="alert" data-code={ask.code ?? ''}>
    <strong>{(ask.code && HEADLINE[ask.code]) || ask.question}</strong>
    <p>{ask.reason}</p>
    {ask.code && HEADLINE[ask.code] && <p className="clarification-question">{ask.question}</p>}
    <div className="clarification-actions">
      {ask.suggestion && <button type="button" className="clarification-suggestion" onClick={() => onUseLocation(ask.suggestion as string)}>Use {ask.suggestion} instead</button>}
      {ask.actions?.map(action => <button type="button" className="clarification-suggestion" key={action.value} onClick={() => onUseIdea(action.value)}>{action.label}</button>)}
      {field && <button type="button" className="clarification-edit" onClick={() => onEditField(field)}>{field === 'location' ? 'Change the location' : 'Edit the business idea'} <ArrowRight size={13}/></button>}
    </div>
  </div>
}
