import { useState } from 'react'
import { Check, X } from 'lucide-react'

const KEY = 'cultureforge-map-hints-dismissed'
const STEPS = ['Explore the map', 'Pick a direction', 'Inspect a venue', 'Remove its evidence']

function readDismissed() { try { return localStorage.getItem(KEY) === '1' } catch { return false } }

/** Four steps, never a modal, never over the map. */
export function JudgeHints({ done }: { done: boolean[] }) {
  const [hidden, setHidden] = useState(readDismissed)
  if (hidden) return null
  return <ol className="ox-hints" aria-label="How to read this map">
    {STEPS.map((step, index) => <li key={step} className={done[index] ? 'is-done' : ''}>
      <span aria-hidden="true">{done[index] ? <Check size={11}/> : index + 1}</span>{step}{done[index] && <span className="geo-sr-only"> (done)</span>}
    </li>)}
    <li className="ox-hints-close"><button type="button" className="icon-button" aria-label="Dismiss the map guide" onClick={() => {
      setHidden(true); try { localStorage.setItem(KEY, '1') } catch { /* storage may be disabled */ }
    }}><X size={13}/></button></li>
  </ol>
}
