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
  // Opening the tour takes the reader to the screen its current step is about.
  useEffect(() => {
    if (step.screen !== screen && !(tourNeedsEvidence(index) && !hasEvidence)) onNavigate(step.screen)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  useEffect(() => {
    function escape(event: KeyboardEvent) { if (event.key === 'Escape') { event.stopPropagation(); onClose() } }
    document.addEventListener('keydown', escape)
    return () => document.removeEventListener('keydown', escape)
  }, [onClose])
  useEffect(() => {
    try { localStorage.setItem(STORAGE, String(index)) } catch { /* Tour remains usable without storage. */ }
    let cancelled = false
    let scrolled = false
    let ticks = 0
    let asked = false
    function measure() {
      const node = screen === step.screen ? document.querySelector<HTMLElement>(step.target) : null
      if (!node) { setHighlight((current) => current ? null : current); return null }
      const r = node.getBoundingClientRect()
      const next = { top: r.top - 6, left: r.left - 6, width: r.width + 12, height: r.height + 12 }
      setHighlight((current) => current && current.top === next.top && current.left === next.left && current.width === next.width && current.height === next.height ? current : next)
      return node
    }
    // The target may not be mounted yet (the screen just changed), so look for
    // it for a couple of seconds and bring it into view the moment it appears.
    // A step with nothing to point at returns the page to the top, so the
    // panel never talks about something that is scrolled out of sight.
    const started = Date.now()
    function settle() {
      if (cancelled) return
      const node = measure()
      // Not on the first pass: the app resets scroll to the top when a screen
      // changes, and that runs after this effect.
      if (ticks++ === 0) return
      // A target that lives in the evidence workbench: open the workbench for it, once.
      if (!node && screen === step.screen && screen === 'results' && !asked && Date.now() - started > 400) { asked = true; window.dispatchEvent(new Event('cultureforge:show-workbench')) }
      if (node && !scrolled) {
        scrolled = true
        const tall = node.getBoundingClientRect().height > window.innerHeight * 0.7
        node.scrollIntoView({ block: tall ? 'start' : 'center', behavior: 'instant' })
        measure()
      } else if (!node && !scrolled && screen !== step.screen) {
        window.scrollTo({ top: 0, behavior: 'instant' })
        scrolled = true
      } else if (!node && !scrolled && Date.now() - started > 2000) {
        window.scrollTo({ top: 0, behavior: 'instant' })
        scrolled = true
      }
    }
    settle()
    const timer = window.setInterval(settle, 120)
    window.addEventListener('resize', measure)
    window.addEventListener('scroll', measure, true)
    return () => { cancelled = true; window.clearInterval(timer); window.removeEventListener('resize', measure); window.removeEventListener('scroll', measure, true) }
  }, [index, screen, step])

  // Moving between steps also moves to the screen the step is about, so the
  // panel and what it describes are never on different pages.
  function go(next: number) {
    const target = TOUR_STEPS[next]
    setIndex(next)
    if (target.screen !== screen && !(tourNeedsEvidence(next) && !hasEvidence)) onNavigate(target.screen)
  }

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
      <div className="tour-dots" aria-label="Tour steps">{TOUR_STEPS.map((item, i) => <button key={item.id} className={i === index ? 'is-active' : ''} aria-label={`Tour step ${i + 1}: ${item.title}`} aria-current={i === index ? 'step' : undefined} onClick={() => go(i)}/>)}</div>
      <h2 id="tour-title">{step.title}</h2><p>{step.body}</p>
      {unavailable && <p className="tour-prerequisite">Research a brief first to explore this step with real evidence. You can still read the rest of the tour.</p>}
      <button className="button button-primary tour-action" onClick={act}>{unavailable ? 'Create an exploration first' : step.action}<ArrowRight size={15}/></button>
      <footer><button className="text-link" disabled={index === 0} onClick={() => go(index - 1)}><ArrowLeft size={14}/> Back</button>{index < TOUR_STEPS.length - 1 ? <button className="text-link" onClick={() => go(index + 1)}>Next <ArrowRight size={14}/></button> : <button className="text-link" onClick={() => { try { localStorage.removeItem(STORAGE) } catch { /* Optional storage. */ } onClose() }}>Finish tour <Check size={14}/></button>}</footer>
      <small>Pause anytime. Reopen “Guided tour” to continue.</small>
    </aside>
  </>
}
