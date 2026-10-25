import { useId, useState } from 'react'
import { ArrowRight } from 'lucide-react'
import { checkReword, IDEA_MAX_LENGTH } from '../rewordIdea'

/**
 * A way out of an answer that could not read the idea: the reader rewords it
 * where they are, and the same brief runs again with only the idea changed.
 */
export function RewordIdea({ current, onReword, busy = false }: { current: string; onReword: (idea: string) => void; busy?: boolean }) {
  const [value, setValue] = useState(current)
  const [problem, setProblem] = useState('')
  const fieldId = useId()
  const submit = () => {
    const check = checkReword(current, value)
    if (!check.ok) { setProblem(check.message); return }
    setProblem('')
    onReword(check.idea)
  }
  return <form className="reword-idea" onSubmit={(event) => { event.preventDefault(); submit() }} noValidate>
    <label htmlFor={fieldId}><strong>Reword the idea</strong></label>
    <p id={`${fieldId}-hint`}>Qloo matches kinds of business, not features. Lead with the kind of place (for example “film-photography café”), then add what is distinctive.</p>
    <div className="reword-row">
      <input id={fieldId} type="text" value={value} maxLength={IDEA_MAX_LENGTH + 40} aria-describedby={`${fieldId}-hint${problem ? ` ${fieldId}-problem` : ''}`}
        aria-invalid={problem ? true : undefined} disabled={busy}
        onChange={(event) => { setValue(event.target.value); if (problem) setProblem('') }}/>
      <button type="submit" className="clarification-suggestion" disabled={busy}>Run with this wording <ArrowRight size={13}/></button>
    </div>
    {problem && <p id={`${fieldId}-problem`} className="reword-problem" role="alert">{problem}</p>}
  </form>
}
