import { useEffect, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight, Check, X } from 'lucide-react'
import { TOUR_STEPS, tourNeedsEvidence } from '../tourSteps'

const STORAGE = 'cultureforge-guided-tour-v1'
function savedStep() {
  try { const n = Number(localStorage.getItem(STORAGE)); return Number.isInteger(n) && n >= 0 && n < TOUR_STEPS.length ? n : 0 } catch { return 0 }
}

export function GuidedTour({ screen, hasEvidence, onNavigate, onInspect, onRemoval, onNotebook, onClose }: {
  screen: string
  hasEvidence: boolean
  onNavigate: (screen: 'home' | 'create' | 'results') => void
  onInspect: () => void
  onRemoval: () => void
  onNotebook: () => void
  onClose: () => void
}) {
  const [index, setIndex] = useState(savedStep)
  const [highlight, setHighlight] = useState<{ top: number; left: number; width: number; height: number } | null>(null)
  const panel = useRef<HTMLElement>(null)
  const step = TOUR_STEPS[index]
  const unavailable = tourNeedsEvidence(index) && !hasEvidence

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    panel.current?.focus()
    return () => { if (previous?.isConnected) previous.focus() }
  }, [])
  useEffect(() => {
    function escape(event: KeyboardEvent) { if (event.key === 'Escape') { event.stopPropagation(); onClose() } }
    document.addEventListener('keydown', escape)
    return () => document.removeEventListener('keydown', escape)
  }, [onClose])
  useEffect(() => {
    try { localStorage.setItem(STORAGE, String(index)) } catch { /* Tour remains usable without storage. */ }
    const target = document.querySelector<HTMLElement>(step.target)
    if (target && screen === step.screen) target.scrollIntoView({ block: 'center', behavior: 'instant' })
    function measure() {
      const node = screen === step.screen ? document.querySelector<HTMLElement>(step.target) : null
      if (!node) { setHighlight(null); return }
      const r = node.getBoundingClientRect()
      setHighlight({ top: r.top - 6, left: r.left - 6, width: r.width + 12, height: r.height + 12 })
    }
    measure()
    window.addEventListener('resize', measure)
    window.addEventListener('scroll', measure, true)
    return () => { window.removeEventListener('resize', measure); window.removeEventListener('scroll', measure, true) }
  }, [index, screen, step])

  function act() {
    if (unavailable) { onNavigate('create'); onClose(); return }
    onNavigate(step.screen)
    if (step.id === 'sources') { onClose(); onInspect() }
    if (step.id === 'removal') { onClose(); onRemoval() }
    if (step.id === 'pilot') { onClose(); onNotebook() }
  }

  return <>
    {highlight && <div className="tour-highlight" style={highlight} aria-hidden="true"/>}
    <aside className="guided-tour panel" ref={panel} role="dialog" aria-modal="false" aria-labelledby="tour-title" tabIndex={-1}>
      <header><span className="small-cap">GUIDED TOUR · {index + 1} OF {TOUR_STEPS.length}</span><button className="icon-button" onClick={onClose} aria-label="Pause guided tour"><X size={17}/></button></header>
      <div className="tour-dots" aria-label="Tour steps">{TOUR_STEPS.map((item, i) => <button key={item.id} className={i === index ? 'is-active' : ''} aria-label={`Tour step ${i + 1}: ${item.title}`} aria-current={i === index ? 'step' : undefined} onClick={() => setIndex(i)}/>)}</div>
      <h2 id="tour-title">{step.title}</h2><p>{step.body}</p>
      {unavailable && <p className="tour-prerequisite">Research a brief first to explore this step with real evidence. You can still read the rest of the tour.</p>}
      <button className="button button-primary tour-action" onClick={act}>{unavailable ? 'Create an exploration first' : step.action}<ArrowRight size={15}/></button>
      <footer><button className="text-link" disabled={index === 0} onClick={() => setIndex((n) => n - 1)}><ArrowLeft size={14}/> Back</button>{index < TOUR_STEPS.length - 1 ? <button className="text-link" onClick={() => setIndex((n) => n + 1)}>Next <ArrowRight size={14}/></button> : <button className="text-link" onClick={() => { try { localStorage.removeItem(STORAGE) } catch { /* Optional storage. */ } onClose() }}>Finish tour <Check size={14}/></button>}</footer>
      <small>Pause anytime. Reopen “Guided tour” to continue.</small>
    </aside>
  </>
}
