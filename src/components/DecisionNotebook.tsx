import { useEffect, useRef, useState } from 'react'
import { ArrowDownToLine, Check, X } from 'lucide-react'
import type { Concept, GenerateResponse } from '../contracts'
import type { ChallengeResult } from '../api'
import { defaultDecision, notebookKey, readDecision, renderDecision } from '../decisionNotebook'
import type { DecisionDraft } from '../decisionNotebook'
import { renderBrief } from '../brief'

export function DecisionNotebook({ result, concept, challenge, onClose }: {
  result: GenerateResponse
  concept: Concept
  challenge: ChallengeResult | null
  onClose: () => void
}) {
  const storageKey = notebookKey(result, concept)
  const [draft, setDraft] = useState<DecisionDraft>(() => readDecision(storageKey) ?? defaultDecision(result, concept))
  const [notice, setNotice] = useState('')
  const dialog = useRef<HTMLElement>(null)
  const close = useRef(onClose)
  close.current = onClose
  const verdict = challenge?.directions.find((row) => row.directionId === concept.id)
  const sources = result.evidence.filter((item) => concept.evidenceIds.includes(item.id))
  const ready = Boolean(draft.hypothesis.trim() && draft.success.trim() && draft.stop.trim())
  const set = <K extends keyof DecisionDraft>(key: K, value: DecisionDraft[K]) => { setDraft((old) => ({ ...old, [key]: value, savedAt: undefined })); setNotice('') }

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    dialog.current?.focus()
    function keydown(event: KeyboardEvent) {
      if (event.key === 'Escape') { event.stopPropagation(); close.current() }
      if (event.key !== 'Tab') return
      const nodes = dialog.current?.querySelectorAll<HTMLElement>('button:not(:disabled),textarea,select,input,a[href]')
      if (!nodes?.length) return
      const first = nodes[0], last = nodes[nodes.length - 1]
      if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog.current)) { event.preventDefault(); last.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
    }
    document.addEventListener('keydown', keydown)
    return () => { document.body.style.overflow = overflow; document.removeEventListener('keydown', keydown); if (previous?.isConnected) previous.focus() }
  }, [])

  function save() {
    const next = { ...draft, savedAt: new Date().toISOString() }
    try { localStorage.setItem(storageKey, JSON.stringify(next)); setDraft(next); setNotice('Saved in this browser. Export a copy to take it with you.') }
    catch { setNotice('Browser storage is unavailable. Download the decision record to keep your work.') }
  }
  function download() {
    const text = renderBrief(result, [concept], challenge) + '\n\n' + renderDecision(draft)
    const url = URL.createObjectURL(new Blob([text], { type: 'text/markdown;charset=utf-8' }))
    const link = document.createElement('a'); link.href = url; link.download = 'cultureforge-decision-record.md'; link.click()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    setNotice('Decision record exported with its Qloo citations and separately labeled team observations.')
  }

  return <div className="notebook-backdrop" onClick={onClose}>
    <section ref={dialog} className="decision-notebook" role="dialog" aria-modal="true" aria-labelledby="notebook-title" tabIndex={-1} onClick={(e) => e.stopPropagation()}>
      <header><div><span className="small-cap">FROM CULTURAL FIT TO A FIELD EXPERIMENT</span><h2 id="notebook-title">What would you try next?</h2><p>{concept.name} · {result.project.location}</p></div><button className="icon-button" aria-label="Close decision notebook" onClick={onClose}><X size={19}/></button></header>
      <div className="notebook-scope"><strong>{verdict ? `Cultural anchor verdict: ${verdict.verdict}` : 'Cultural anchor: not tested'}</strong><p>{verdict?.scope ?? 'The current direction has no recorded anchor verdict.'} Field observations below are entered by you and remain separate from Qloo evidence.</p></div>
      <div className="notebook-layout"><div className="notebook-fields">
        <label>Hypothesis to test<textarea rows={3} maxLength={2000} value={draft.hypothesis} onChange={(e) => set('hypothesis', e.target.value)}/></label>
        <label>How will you test it?<select value={draft.method} onChange={(e) => set('method', e.target.value as DecisionDraft['method'])}><option value="interviews">Audience interviews</option><option value="concept_test">Concept walkthrough</option><option value="pop_up">Small pop-up or prototype</option></select></label>
        <label>Accountable owner<input type="text" maxLength={160} placeholder="Who will run this experiment?" value={draft.owner ?? ''} onChange={(e) => set('owner', e.target.value)}/></label>
        <label>Review date<input type="date" value={draft.reviewDate ?? ''} onChange={(e) => set('reviewDate', e.target.value)}/></label>
        <label>Experiment spending cap<input type="text" maxLength={100} placeholder="Enter your own cap and currency, e.g. USD 200" value={draft.spendingCap ?? ''} onChange={(e) => set('spendingCap', e.target.value)}/></label>
        <label>Proceed only if…<textarea rows={2} maxLength={2000} placeholder="Define the observation you would need before investing more." value={draft.success} onChange={(e) => set('success', e.target.value)}/></label>
        <label>Revise or stop if…<textarea rows={2} maxLength={2000} placeholder="Write the result that would contradict your hypothesis." value={draft.stop} onChange={(e) => set('stop', e.target.value)}/></label>
        <label>Your field observations<textarea rows={3} maxLength={6000} placeholder="Leave blank until you have observed something. Record who, when and what happened without private personal details." value={draft.observations} onChange={(e) => set('observations', e.target.value)}/></label>
        <label>Your current decision<select value={draft.choice} onChange={(e) => set('choice', e.target.value as DecisionDraft['choice'])}><option value="investigate">Investigate further</option><option value="revise">Revise the concept</option><option value="park">Park this direction</option></select></label>
      </div><aside className="notebook-evidence"><span className="small-cap">THE QLOO BASIS YOU ARE STARTING FROM</span><h3>A proposal, with references.</h3>{sources.length ? sources.map((item) => <div key={item.id}><strong>{item.label}</strong><small>{item.kind === 'entity' ? 'Returned place' : 'Resolved cultural signal'} · {item.id}</small></div>) : <p>No sources are cited by this direction.</p>}<h3>What could change your mind?</h3><p>{verdict?.falsifier ?? 'Run the cultural anchor test to inspect its falsifier. Your field experiment asks a separate question about the proposed experience.'}</p><p>{concept.limitations[0]}</p><small>These references can inform an experiment. They do not establish customer demand or a viable business.</small></aside></div>
      <footer><span className={`notebook-status ${ready ? 'is-ready' : ''}`}><Check size={15}/>{ready ? 'Experiment criteria defined' : 'Draft — define both proceed and stop criteria'}</span><div><button className="button button-secondary" onClick={download}><ArrowDownToLine size={15}/> Download decision record</button><button className="button button-primary" onClick={save}>Save in this browser <Check size={15}/></button></div><p>Notebook notes stay in this browser. Shared exploration links carry the Qloo record; download the decision record to include your notes. A changed evidence set starts a separate notebook.</p>{notice && <p role="status">{notice}</p>}</footer>
    </section>
  </div>
}
