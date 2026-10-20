import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import {
  ArrowDownToLine, ArrowLeft, ArrowRight, ArrowUpRight, AudioLines, Share2,
  Bookmark, Check, CheckCheck, ChevronRight, CircleHelp, Coffee,
  Fingerprint, FlaskConical, Globe2, Layers3, LayoutGrid, Leaf, Lightbulb,
  LoaderCircle, MapPin, Menu, Moon, Play, Plus, Search, ShieldCheck, SlidersHorizontal,
  Sparkles, Sun, Target, Users, WandSparkles, Waves, X,
} from 'lucide-react'
import type { Concept, CulturalSignal, Delivery, Evidence, GenerateResponse, ProjectRequest, TraceEvent } from './contracts'
import { compareAudience, compareAudiences, fetchSnapshot, generateConcepts, rankAnchors, recompose, resolveTaste, shareExploration, startResearch } from './api'
import type { TasteSeed } from './api'
import { CulturalConstellation } from './components/CulturalConstellation'
import { ProvenanceDrawer } from './components/ProvenanceDrawer'
import { AgentTrace } from './components/AgentTrace'
import { TasteSeeds } from './components/TasteSeeds'
import { AudienceComparison } from './components/AudienceComparison'
import { AnchorTournament } from './components/AnchorTournament'
import { CulturalHeat } from './components/CulturalHeat'
import { mockGenerate } from './mockData'

 type Screen = 'home' | 'create' | 'progress' | 'results' | 'compare'
 type Theme = 'dark' | 'light'
const initial: ProjectRequest = {
  businessType: 'Food & beverage', audience: 'Design-conscious Gen Z & young professionals',
  location: 'Brooklyn, New York', budget: '$25k – $50k', objectives: ['Build a loyal community'],
}
const audiencePresets = ['Design-conscious Gen Z', 'Independent creatives', 'Young families', 'Mindful professionals']
const objectives = ['Build a loyal community', 'Stand out in a crowded market', 'Attract a new audience', 'Create a memorable experience']
const titles: Record<Screen, string> = { home: 'Overview', create: 'New exploration', progress: 'Agent workspace', results: 'Concept studio', compare: 'Scenario lab' }
function readStored<T,>(key: string, fallback: T): T {
  try { const value = localStorage.getItem(key); return value ? JSON.parse(value) as T : fallback } catch { return fallback }
}
function writeStored(key: string, value: unknown) { try { localStorage.setItem(key, JSON.stringify(value)) } catch { /* Storage can be disabled in private browser sessions. */ } }

export default function App() {
  const [screen, setScreen] = useState<Screen>(() => window.location.hash === '#workspace/create' ? 'create' : 'home')
  const [theme, setTheme] = useState<Theme>(() => readStored('cultureforge-theme', 'dark'))
  const [form, setForm] = useState<ProjectRequest>(initial)
  const [result, setResult] = useState<GenerateResponse>(() => mockGenerate(initial))
  const [selected, setSelected] = useState(() => mockGenerate(initial).concepts[0].id)
  const [saved, setSaved] = useState<string[]>(() => readStored('cultureforge-saved', []))
  const [menuOpen, setMenuOpen] = useState(false)
  const [providerError, setProviderError] = useState('')
  const [modal, setModal] = useState<Concept | null>(null)
  const [toast, setToast] = useState('')
  const [savedOnly, setSavedOnly] = useState(false)
  const [scenarioBusy, setScenarioBusy] = useState(false)
  const [provenanceId, setProvenanceId] = useState<string | null>(null)
  const [researchRunId, setResearchRunId] = useState<string | null>(null)
  const [seedCandidates, setSeedCandidates] = useState<TasteSeed[] | null>(null)
  const [seedBusy, setSeedBusy] = useState(false)
  const [clarification, setClarification] = useState<{ reason: string; question: string; field: string } | null>(null)
  const [shareUrl, setShareUrl] = useState('')
  const runId = useRef(0)
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.documentElement.style.colorScheme = theme
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#141412' : '#f6f5f0')
    writeStored('cultureforge-theme', theme)
  }, [theme])
  useEffect(() => { writeStored('cultureforge-saved', saved) }, [saved])
  useEffect(() => {
    function startNewExploration() { setProviderError(''); setSavedOnly(false); setScreen('create') }
    window.addEventListener('cultureforge:open-create', startNewExploration)
    return () => window.removeEventListener('cultureforge:open-create', startNewExploration)
  }, [])
  useEffect(() => { if (!toast) return; const timer = window.setTimeout(() => setToast(''), 3000); return () => clearTimeout(timer) }, [toast])
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'instant' }); setMenuOpen(false) }, [screen])
  useEffect(() => {
    const snapshotId = new URLSearchParams(window.location.search).get('snapshot')
    if (!snapshotId) return
    let cancelled = false
    fetchSnapshot(snapshotId)
      .then((data) => {
        if (cancelled) return
        setResult(data); setSelected(data.concepts[0]?.id ?? '01'); setScreen('results')
      })
      .catch((error) => { if (!cancelled) setToast(error instanceof Error ? error.message : 'That snapshot could not be opened.') })
    return () => { cancelled = true }
  }, [])
  function navigate(next: Screen) { if (screen === 'progress') runId.current++; setMenuOpen(false); setScreen(next) }
  // The studio is served either standalone at / or embedded in the prototype's
  // landing page. "Landing" has to work in both cases: hand control back to the
  // prototype when it is embedded, and always fall back to the app's own home
  // screen so the button can never dead-end.
  function goToLanding() {
    window.dispatchEvent(new Event('cultureforge:show-landing'))
    navigate('home')
  }
  const savedHere = result.concepts.filter(concept => saved.includes(concept.id))
  function save(id: string) { setSaved(current => current.includes(id) ? current.filter(value => value !== id) : [...current, id]) }
  async function create(project: ProjectRequest = form, demo = false) {
    const id = ++runId.current
    setProviderError(''); setForm(project); setScreen('progress'); setSavedOnly(false)
    setClarification(null); setResearchRunId(null)
    if (demo) {
      const data = mockGenerate(project)
      setResult(data); setSelected(data.concepts[0]?.id ?? '01'); setScreen('results')
      return
    }
    try {
      // A cached result is already warm, so it appears immediately. A cold
      // result shows its real progress in the workspace instead of a timer.
      const data = await generateConcepts(project)
      if (id !== runId.current) return
      setResult(data); setSelected(data.concepts[0]?.id ?? '01'); setScreen('results')
    } catch (error) {
      if (id !== runId.current) return
      setProviderError(error instanceof Error ? error.message : 'Research could not finish. Please try again.'); setScreen('create')
    }
  }

  /**
   * The research path the studio takes: resolve the audience into candidate
   * Qloo seeds, let the founder confirm them, then run the agent for real and
   * watch its actual steps.
   */
  async function beginResearch(project: ProjectRequest = form) {
    setSeedBusy(true); setProviderError('')
    try {
      const resolution = await resolveTaste(project, project.audience)
      setSeedCandidates(resolution.candidates)
    } catch (error) {
      setProviderError(error instanceof Error ? error.message : 'The audience could not be resolved.')
    }
    setSeedBusy(false)
  }

  async function confirmSeeds(tagIds: string[]) {
    setSeedCandidates(null); setScreen('progress'); setClarification(null)
    try {
      const { runId: started } = await startResearch(form, form.audience, tagIds)
      setResearchRunId(started)
    } catch (error) {
      setProviderError(error instanceof Error ? error.message : 'The research could not be started.')
      setScreen('create')
    }
  }

  function onRunComplete(data: GenerateResponse) {
    setResult(data); setSelected(data.concepts[0]?.id ?? '01'); setResearchRunId(null); setScreen('results')
  }

  function onRunClarify(ask: { reason: string; question: string; field: string }) {
    setClarification(ask); setResearchRunId(null); setScreen('create')
  }

  async function shareThisExploration() {
    try {
      const { snapshotId } = await shareExploration(result)
      const url = `${window.location.origin}${window.location.pathname}?snapshot=${snapshotId}`
      setShareUrl(url)
      try { await navigator.clipboard.writeText(url) } catch { /* clipboard may be blocked */ }
      setToast('Share link copied. It reopens exactly this exploration.')
    } catch (error) {
      setToast(error instanceof Error ? error.message : 'This exploration could not be shared.')
    }
  }

  async function applyScenario(audience: string, scores: number[]) {
    // For an evidence-composed exploration the scenario lab must re-research
    // with Qloo rather than shift a locally computed score.
    if (result.conceptMode === 'evidence_composed') {
      setScenarioBusy(true)
      try {
        const live = await compareAudience(result.project, audience)
        const next: GenerateResponse = {
          ...result,
          project: { ...result.project, audience },
          concepts: live.concepts,
          signals: live.signals,
          evidence: live.evidence,
          trace: live.trace,
          delivery: live.delivery,
          notice: live.notice,
        }
        setForm(next.project); setResult(next); setSelected(next.concepts[0]?.id ?? ''); setSavedOnly(false)
        setToast('Re-researched with live Qloo evidence for the new audience.')
      } catch (error) {
        setToast(error instanceof Error ? error.message : 'The comparison could not be completed.')
      }
      setScenarioBusy(false)
      navigate('results')
      return
    }
    const next = mockGenerate({ ...result.project, audience })
    next.concepts = next.concepts.map((concept, index) => ({ ...concept, audienceFit: scores[index] }))
    setForm(next.project); setResult(next); setSelected(next.concepts[0].id); setSavedOnly(false)
    setToast('New audience concepts generated with the mock model.'); navigate('results')
  }
  function exportBrief() {
    const entries = savedHere.length ? savedHere : result.concepts
    const text = `# CultureForge — Exploration brief\n\nAudience: ${result.project.audience}\nLocation: ${result.project.location}\nBudget: ${result.project.budget}\nObjectives: ${result.project.objectives.join(', ')}\n\nData: ${result.dataMode === 'live' ? 'Qloo aggregate cultural signals' : 'Illustrative mock data'}\nAll concept narratives, fit scores, costs, and scenario shifts are sample estimates.\n\n${entries.map(concept => `## ${concept.name}\n${concept.tagline}\n\n${concept.description}\n\nSample fit: ${concept.audienceFit}/100\nIllustrative investment: ${concept.investment}\nCultural themes: ${concept.signals.join(', ')}\n`).join('\n')}\n## Supporting mock hypotheses\n${result.signals.map(signal => `- ${signal.label}: ${signal.detail}`).join('\n')}\n\n${result.notice}`
    const url = URL.createObjectURL(new Blob([text], { type: 'text/markdown;charset=utf-8' }))
    const link = document.createElement('a'); link.href = url; link.download = 'cultureforge-exploration.md'; link.click(); URL.revokeObjectURL(url)
    setToast('Your exploration brief is ready.')
  }
  return <div className="studio-shell">
    {menuOpen && <button className="sidebar-backdrop" aria-label="Close navigation" onClick={() => setMenuOpen(false)} />}
    <aside className={`sidebar ${menuOpen ? 'is-open' : ''}`}>
      <button className="brand" onClick={() => navigate('home')} aria-label="CultureForge home"><span className="brand-symbol"><Waves size={21} strokeWidth={2.4}/></span><span>CultureForge<span className="brand-ai">AI</span></span></button>
      <button className="sidebar-close icon-button" aria-label="Close navigation" onClick={() => setMenuOpen(false)}><X size={19}/></button>
      <div className="workspace-switch"><span className="workspace-icon">CF</span><span><strong>Founder workspace</strong><small>Your ideas, taking shape</small></span><ChevronRight size={14}/></div>
      <p className="nav-label">WORKSPACE</p>
      <nav aria-label="Main navigation">
        <NavItem icon={<LayoutGrid size={17}/>} label="Overview" active={screen === 'home'} onClick={() => navigate('home')}/>
        <NavItem icon={<Sparkles size={17}/>} label="New exploration" active={screen === 'create' || screen === 'progress'} onClick={() => navigate('create')}/>
        <NavItem icon={<Layers3 size={17}/>} label="Concept studio" active={screen === 'results' && !savedOnly} onClick={() => { setSavedOnly(false); navigate('results') }} suffix="03"/>
        <NavItem icon={<FlaskConical size={17}/>} label="Scenario lab" active={screen === 'compare'} onClick={() => navigate('compare')}/>
      </nav>
      <div className="nav-rule"/><p className="nav-label">YOUR COLLECTION</p>
      <NavItem icon={<Bookmark size={17}/>} label="Saved concepts" active={screen === 'results' && savedOnly} onClick={() => { setSavedOnly(true); navigate('results') }} suffix={String(savedHere.length).padStart(2, '0')}/>
      <button className="mini-project" onClick={() => navigate('results')}><span className="project-color"/><span>{result.project.location.split(',')[0]}, reimagined<small>{result.project.businessType} · Exploration</small></span><ArrowUpRight size={13}/></button>
      <div className="sidebar-bottom"><div className="demo-promo"><span className="small-cap"><span className="orange-dot"/> THE CULTUREFORGE EXPERIENCE</span><h3>One idea.<br/>A world of possibilities.</h3><button onClick={() => create(initial, true)}>Take a guided demo <Play size={13} fill="currentColor"/></button><span className="demo-promo-art"><Waves size={67} strokeWidth={1}/></span></div>
      <div className="sidebar-foot"><div className="founder-avatar">V</div><span><strong>Vincent’s workspace</strong><small>Qloo Agentic Hackathon</small></span><span className="workspace-indicator"/></div></div>
    </aside>
    <main className="main-area"><header className="topbar"><div className="topbar-left"><button className="studio-return" onClick={goToLanding}><ArrowLeft size={14}/> Landing</button><button className="mobile-menu icon-button" aria-label="Open navigation" onClick={() => setMenuOpen(true)}><Menu size={20}/></button><span className="topbar-workspace">Workspace</span><ChevronRight size={12}/><span>{titles[screen]}</span></div><div className="topbar-right"><span className="prototype-badge"><span/> {result.dataMode === 'live' ? 'Qloo signals connected' : 'Prototype · mock data'}</span><span className="topbar-separator"/><a className="topbar-link" href="/">Front page <ArrowUpRight size={13}/></a><button className="theme-toggle" aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`} title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`} onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>{theme === 'dark' ? <Sun size={17}/> : <Moon size={17}/>}<span>{theme === 'dark' ? 'Light' : 'Dark'} mode</span></button><button className="top-new icon-button" aria-label="Create a new exploration" onClick={() => navigate('create')}><Plus size={18}/></button></div></header>
      <div className="page-content" key={screen}>
        {screen === 'home' && <Home start={() => navigate('create')} demo={() => create(initial, true)} explore={() => navigate('results')}/>}
        {screen === 'create' && (seedCandidates
          ? <TasteSeeds candidates={seedCandidates} audience={form.audience} busy={seedBusy}
              onConfirm={confirmSeeds} onCancel={() => setSeedCandidates(null)}/>
          : <Create form={form} setForm={setForm} submit={() => beginResearch()} error={providerError} back={() => navigate('home')}/>)}
        {screen === 'create' && clarification && <div className="clarification" role="alert"><strong>{clarification.question}</strong><p>{clarification.reason}</p></div>}
        {screen === 'progress' && (researchRunId
          ? <Progress project={form} runId={researchRunId} onComplete={onRunComplete} onClarify={onRunClarify}/>
          : <Progress project={form}/>)}
        {screen === 'results' && <Results result={result} selected={selected} select={setSelected} saved={saved} save={save} savedOnly={savedOnly} setSavedOnly={setSavedOnly} open={setModal} compare={() => navigate('compare')} exportBrief={exportBrief} onInspect={setProvenanceId} onShare={shareThisExploration} shareUrl={shareUrl}/>}
        <ProvenanceDrawer evidence={result.evidence} concepts={result.concepts} trace={result.trace} evidenceId={provenanceId} project={result.project} onClose={() => setProvenanceId(null)} onRecomposed={(next)=>{ if(next.concepts.length) { setResult({...result, concepts:next.concepts, evidence:next.evidence}); setSelected(next.concepts[0]?.id ?? selected); setToast('Recomposed without that venue. Qloo was not called again.') } else { setToast('Every direction lost its support without that venue.') } }}/>
        {screen === 'compare' && <Compare result={result} back={() => navigate('results')} apply={applyScenario} busy={scenarioBusy}/> }
      </div><footer className="page-footer"><span><Waves size={13}/> CultureForge AI <i/> Built for the culturally curious.</span><span>Human ambition. Cultural intelligence.</span></footer>
    </main>
    {modal && <ConceptModal concept={modal} saved={saved.includes(modal.id)} save={() => save(modal.id)} close={() => setModal(null)}/ >}
    {toast && <div className="toast" role="status"><CheckCheck size={17}/>{toast}</div>}
  </div>
}
function NavItem({ icon, label, active, onClick, suffix }: { icon: ReactNode; label: string; active: boolean; onClick: () => void; suffix?: string }) {
  return <button className={`nav-item ${active ? 'active' : ''}`} onClick={onClick} aria-current={active ? 'page' : undefined}>{icon}<span>{label}</span>{suffix && <small>{suffix}</small>}</button>
}
function BusinessIcon({type,size=14}:{type:ProjectRequest['businessType'];size?:number}) { const Icon = {'Food & beverage':Coffee,Retail:Layers3,Hospitality:Globe2,Wellness:Leaf,Entertainment:AudioLines}[type]; return <Icon size={size}/> }
function Eyebrow({ children }: { children: ReactNode }) { return <div className="eyebrow"><span/>{children}</div> }
function Button({ children, onClick, variant = 'primary', type = 'button', disabled = false }: { children: ReactNode; onClick?: () => void; variant?: 'primary' | 'secondary' | 'text'; type?: 'button' | 'submit'; disabled?: boolean }) { return <button type={type} className={`button button-${variant}`} onClick={onClick} disabled={disabled}>{children}</button> }

function Home({ start, demo, explore }: { start: () => void; demo: () => void; explore: () => void }) {
  return <div className="home-page"><div className="welcome-row"><span>YOUR NEXT CHAPTER STARTS HERE</span><span className="edition-tag">CULTURE / COMMERCE / POSSIBILITY</span></div>
    <section className="hero"><div className="hero-copy"><Eyebrow>BUILT ON CULTURE. MADE FOR YOU.</Eyebrow><h1>Great ideas have<br/>a <em>cultural edge.</em></h1><p>Discover what moves your audience.<br/>Build a business that moves them.</p><div className="hero-actions"><Button onClick={start}>Find your next big idea <ArrowUpRight size={18}/></Button><button className="play-button" onClick={demo}><span><Play size={12} fill="currentColor"/></span> Explore the demo</button></div><div className="hero-assurance"><ShieldCheck size={14}/> Evidence-led thinking <span/> Your imagination, amplified</div></div>
      <div className="hero-composition"><div className="hero-image main-photo"><div className="photo-grain"/><span className="image-caption">BROOKLYN, NEW YORK <ArrowUpRight size={14}/></span><div className="image-story"><span>THE NEXT WAVE OF THIRD PLACES</span><h2>Where coffee<br/>meets <em>culture.</em></h2></div></div><div className="orbit-sticker"><Waves size={27}/><span>FOLLOW THE<br/>CULTURAL CURRENT</span></div><div className="signal-card"><div className="signal-card-label"><span className="orange-dot"/> A CONNECTION WORTH EXPLORING <ArrowUpRight size={13}/></div><div className="signal-link"><span><AudioLines size={16}/> Vinyl culture</span><span className="connection-line"/><span><Coffee size={16}/> Café rituals</span></div><div className="signal-card-footer"><span>Different interests. Shared audience.</span><span className="sample-mini">SAMPLE SIGNAL</span></div></div><span className="composition-index">01 / A WORLD OF CONNECTIONS</span></div></section>
    <section className="possibility-strip"><div><span className="strip-number">01</span><span><strong>Understand the audience.</strong><small>Discover cultural affinities that connect.</small></span></div><ArrowRight size={16}/><div><span className="strip-number">02</span><span><strong>Explore the unexpected.</strong><small>Three distinct concepts. One clear vision.</small></span></div><ArrowRight size={16}/><div><span className="strip-number">03</span><span><strong>Make your next move.</strong><small>Compare, refine, and find your direction.</small></span></div></section>
    <section className="discovery-section"><div className="section-heading"><div><Eyebrow>LESS GUESSWORK. MORE POSSIBILITY.</Eyebrow><h2>A new way to see <em>what’s next.</em></h2></div><button className="text-link" onClick={explore}>Inside an exploration <ArrowUpRight size={15}/></button></div><div className="discovery-grid"><button className="discovery-card graph-card" onClick={explore}><div className="discovery-top"><span className="feature-icon"><Fingerprint size={19}/></span><ArrowUpRight size={17}/></div><h3>Connect the cultural dots.</h3><p>Music, places, brands, and behavior.<br/>See the world through your audience’s tastes.</p><CultureGraph compact/><span className="feature-bottom">CROSS-DOMAIN CULTURAL INTELLIGENCE <Plus size={12}/></span></button><button className="discovery-card concept-teaser" onClick={demo}><div className="discovery-top"><span className="feature-icon"><Lightbulb size={19}/></span><ArrowUpRight size={17}/></div><h3>From insight to “what if.”</h3><p>Turn cultural connections into business<br/>experiences with a point of view.</p><div className="teaser-stack"><span className="stack-back"/><span className="stack-middle"/><div className="stack-front"><span className="tiny-cap">CONCEPT 01 · SAMPLE</span><h4>The Listening Room</h4><span>A café built around the perfect side A.</span><div><AudioLines size={16}/><span>COFFEE × VINYL × CONNECTION</span></div></div></div><span className="feature-bottom">THREE DIFFERENTIATED CONCEPTS <Plus size={12}/></span></button><button className="discovery-card scenario-teaser" onClick={explore}><div className="discovery-top"><span className="feature-icon"><SlidersHorizontal size={19}/></span><ArrowUpRight size={17}/></div><h3>A small change. A new angle.</h3><p>Shift the audience. Explore the tradeoffs.<br/>Find the idea that feels right.</p><div className="teaser-bars"><span>Independent creatives <b>94</b><i><em style={{width:'94%'}}/></i></span><span>Mindful professionals <b>86</b><i><em style={{width:'86%'}}/></i></span><span>Young families <b>78</b><i><em style={{width:'78%'}}/></i></span><small>ILLUSTRATIVE AUDIENCE-FIT SCORES</small></div><span className="feature-bottom">INTERACTIVE SCENARIO EXPLORATION <Plus size={12}/></span></button></div></section>
    <div className="home-bottom-note"><span><Sparkles size={16}/> Curiosity is your competitive advantage.</span><span>Explore freely. Build thoughtfully.</span></div>
  </div>
}

function CultureGraph({ compact = false }: { compact?: boolean }) {
  return <div className={`culture-graph ${compact ? 'compact' : ''}`} aria-label="Illustrative connections between an audience and cultural interests"><svg viewBox="0 0 500 250" aria-hidden="true"><defs><linearGradient id={compact?'edge-small':'edge-large'}><stop stopColor="#ef7148" stopOpacity=".8"/><stop offset="1" stopColor="#a5af8e" stopOpacity=".2"/></linearGradient></defs>{[[70,60],[420,55],[420,190],[85,200],[265,30]].map(([x,y],i)=><path key={i} d={`M250 128 Q${x} 128 ${x} ${y}`} stroke={`url(#${compact?'edge-small':'edge-large'})`} fill="none" strokeWidth="1.2"/>)}<circle cx="250" cy="128" r="63" fill="none" stroke="currentColor" strokeDasharray="3 7" opacity=".1"/><circle cx="250" cy="128" r="90" fill="none" stroke="currentColor" opacity=".05"/></svg><div className="graph-center"><Fingerprint size={22}/><span>Your audience</span></div><span className="graph-node node-one"><AudioLines size={13}/> Vinyl & jazz</span><span className="graph-node node-two"><Coffee size={13}/> Café culture</span><span className="graph-node node-three"><Leaf size={13}/> Slow living</span><span className="graph-node node-four"><Globe2 size={13}/> Local discovery</span>{!compact && <span className="graph-node node-five"><Layers3 size={13}/> Design</span>}</div>
}
function Create({ form, setForm, submit, error, back }: { form: ProjectRequest; setForm: (project: ProjectRequest) => void; submit: () => void; error: string; back: () => void }) {
  const [custom, setCustom] = useState('')
  const types = [{label:'Food & beverage',icon:Coffee},{label:'Retail',icon:Layers3},{label:'Hospitality',icon:Globe2},{label:'Wellness',icon:Leaf},{label:'Entertainment',icon:AudioLines}] as const
  const allGoals = [...new Set([...objectives, ...form.objectives])]
  function toggle(goal: string) { setForm({...form, objectives: form.objectives.includes(goal) ? form.objectives.filter(value => value !== goal) : [...form.objectives, goal]}) }
  const add = () => { const value=custom.trim(); if(value && !form.objectives.includes(value)) toggle(value); setCustom('') }
  return <div className="create-page"><button className="back-link" onClick={back}><ArrowLeft size={14}/> Back to overview</button><div className="page-heading"><div><Eyebrow>THE BEGINNING OF SOMETHING GOOD</Eyebrow><h1>Tell us what you’re<br/><em>dreaming of.</em></h1><p>You bring the ambition. We’ll find the cultural connections.</p></div><span className="page-index">EXPLORATION / 001</span></div><div className="create-layout"><form className="creation-form panel" onSubmit={event => { event.preventDefault(); submit() }}>{error && <div className="api-error" role="alert">{error}</div>}<div className="form-section"><div className="form-section-title"><span>01</span><div><h3>What are you building?</h3><p>Choose the world your idea belongs in.</p></div></div><div className="business-types">{types.map(({label,icon:Icon})=><button type="button" className={form.businessType===label?'business-tile selected':'business-tile'} aria-pressed={form.businessType===label} key={label} onClick={()=>setForm({...form,businessType:label})}><Icon size={20}/><span>{label}</span>{form.businessType===label&&<Check size={12}/>}</button>)}</div></div><div className="form-section"><div className="form-section-title"><span>02</span><div><h3>Who do you want to move?</h3><p>Describe the people at the heart of your idea.</p></div></div><label className="field"><span>Target audience</span><div className="input-with-icon"><Users size={16}/><input required minLength={2} maxLength={240} value={form.audience} onChange={event=>setForm({...form,audience:event.target.value})}/></div></label><div className="preset-row"><span>TRY</span>{audiencePresets.slice(0,3).map(preset=><button type="button" key={preset} onClick={()=>setForm({...form,audience:preset})}>{preset}<Plus size={10}/></button>)}</div><div className="field-grid"><label className="field"><span>Location</span><div className="input-with-icon"><MapPin size={16}/><input required minLength={2} maxLength={160} value={form.location} onChange={event=>setForm({...form,location:event.target.value})}/></div></label><label className="field"><span>Starting budget</span><select value={form.budget} onChange={event=>setForm({...form,budget:event.target.value})}>{['Under $25k','$25k – $50k','$50k – $100k','$100k+','Still figuring it out'].map(budget=><option key={budget}>{budget}</option>)}</select></label></div></div><div className="form-section"><div className="form-section-title"><span>03</span><div><h3>What would success feel like?</h3><p>Select the things that matter to you.</p></div></div><div className="goal-grid">{allGoals.map(goal=><button type="button" className={`goal-chip ${form.objectives.includes(goal)?'selected':''}`} aria-pressed={form.objectives.includes(goal)} key={goal} onClick={()=>toggle(goal)}><span>{form.objectives.includes(goal)?<Check size={12}/>:<Plus size={12}/>}</span>{goal}</button>)}</div><div className="custom-goal"><input aria-label="Custom objective" placeholder="Something else on your mind?" value={custom} onChange={event=>setCustom(event.target.value)} onKeyDown={event=>{if(event.key==='Enter'){event.preventDefault();add()}}}/><button type="button" onClick={add} disabled={!custom.trim()} aria-label="Add custom objective"><Plus size={15}/></button></div></div><div className="form-submit-row"><span><ShieldCheck size={14}/> Your vision stays yours.</span><Button type="submit">Find my cultural edge <ArrowUpRight size={17}/></Button></div></form><aside className="creation-aside"><div className="brief-preview panel"><span className="small-cap"><span className="orange-dot"/> YOUR EXPLORATION, AT A GLANCE</span><div className="brief-art"><Fingerprint size={52} strokeWidth={1}/><span/><span/></div><h3>A little context.<br/><em>A lot of possibility.</em></h3><dl><div><dt>Business</dt><dd>{form.businessType}</dd></div><div><dt>Location</dt><dd>{form.location || 'Your neighborhood'}</dd></div><div><dt>Budget</dt><dd>{form.budget}</dd></div></dl><div className="brief-deliverables"><span><Check size={13}/> 3 original concept directions</span><span><Check size={13}/> Cultural signals & evidence</span><span><Check size={13}/> Audience scenario comparison</span></div></div><div className="curiosity-note"><Lightbulb size={18}/><p><strong>Get specific. Stay curious.</strong>The most interesting connections often start with the smallest details.</p></div></aside></div></div>
}
function Progress({project,runId,onComplete,onClarify}:{project:ProjectRequest;runId?:string;onComplete?:(result:GenerateResponse)=>void;onClarify?:(ask:{reason:string;question:string;field:string})=>void}) {
  const [stage,setStage]=useState(0)
  useEffect(()=>{const timers=[window.setTimeout(()=>setStage(1),850),window.setTimeout(()=>setStage(2),1800),window.setTimeout(()=>setStage(3),2850)];return()=>timers.forEach(clearTimeout)},[])
  const steps=[{icon:Search,title:'Understand the audience',detail:'Resolving interests, place, and cultural context.'},{icon:Fingerprint,title:'Connect the cultural dots',detail:'Finding meaningful affinities across culture.'},{icon:WandSparkles,title:'Shape three possibilities',detail:'Bringing the connections into concept directions.'}]
  return <div className="progress-page"><span className="small-cap"><span className="orange-dot pulse"/> AGENT WORKSPACE</span><div className="agent-orbit"><div className="orbit-outer"/><div className="orbit-middle"/><span className="orbit-icon"><Waves size={35}/></span><span className="satellite sat-one"><Coffee size={17}/></span><span className="satellite sat-two"><AudioLines size={17}/></span><span className="satellite sat-three"><Leaf size={17}/></span></div><h1>Curiosity is<br/><em>connecting the dots.</em></h1><p>Your brief is becoming a world of possibilities.</p><div className="progress-context"><span><BusinessIcon type={project.businessType} size={13}/>{project.businessType}</span><span><MapPin size={13}/>{project.location}</span></div><div className="agent-steps panel" aria-live="polite">{steps.map(({icon:Icon,title,detail},index)=><div className={`agent-step ${stage>index?'complete':stage===index?'working':'pending'}`} key={title}><span className="agent-step-icon">{stage>index?<Check size={17}/>:<Icon size={17}/>}</span><div><strong>{title}</strong><small>{detail}</small></div><span className="step-status">{stage>index?'Complete':stage===index?<><LoaderCircle size={12} className="spin"/> Working</>:'Up next'}</span></div>)}<div className="agent-progress-track"><i style={{width:`${Math.min(100,18+stage*29)}%`}}/></div></div>{runId&&<AgentTrace runId={runId} onComplete={onComplete as (r:GenerateResponse)=>void} onClarify={onClarify as (a:{reason:string;question:string;field:string})=>void}/>}<span className="progress-footnote"><ShieldCheck size={13}/> {runId?'A real research run. Every step below is a Qloo call the agent made.':'A guided prototype workflow. Sample scores stay clearly labeled.'}</span></div>
}

function Results({result,selected,select,saved,save,savedOnly,setSavedOnly,open,compare,exportBrief,onInspect,onShare,shareUrl}:{result:GenerateResponse;selected:string;select:(id:string)=>void;saved:string[];save:(id:string)=>void;savedOnly:boolean;setSavedOnly:(value:boolean)=>void;open:(concept:Concept)=>void;compare:()=>void;exportBrief:()=>void;onInspect?:(evidenceId:string)=>void;onShare?:()=>void;shareUrl?:string}) {
  const [view,setView]=useState<'cards'|'matrix'>('cards')
  const [insightTab,setInsightTab]=useState<'signals'|'constellation'|'heat'|'anchors'|'blueprint'|'source'>('signals')
  const [whyOpen,setWhyOpen]=useState<string|null>(null)
  const chosen=result.concepts.find(concept=>concept.id===selected)??result.concepts[0]
  const filtered=savedOnly?result.concepts.filter(concept=>saved.includes(concept.id)):result.concepts
  const hasScores=result.concepts.length>0&&result.concepts.every(concept=>typeof concept.audienceFit==='number')
  const livePlaces=result.evidence.filter(item=>item.kind==='entity').length
  return <div className="results-page"><div className="results-title-row"><div><Eyebrow>YOUR AMBITION, SEEN THROUGH CULTURE</Eyebrow><h1>Three directions.<br/><em>One cultural edge.</em></h1><p>Different expressions of the same vision. Find the one that feels like you.</p></div><div className="heading-actions"><Button variant="secondary" onClick={exportBrief}><ArrowDownToLine size={15}/> Export brief</Button>{onShare&&<Button variant="secondary" onClick={onShare}><Share2 size={15}/> Share</Button>}<Button onClick={compare}>Compare audiences <ArrowUpRight size={16}/></Button></div></div><div className="exploration-context"><span><BusinessIcon type={result.project.businessType}/>{result.project.businessType}</span><span><MapPin size={14}/>{result.project.location}</span><span><Users size={14}/>{result.project.audience}</span><span className="context-budget">{result.project.budget}</span></div>
    <div className="mock-brief-summary"><ShieldCheck size={18}/><div><strong>{result.conceptMode==='evidence_composed'?'Directions composed from live Qloo evidence':'Personalized mock concepts · Qloo not connected'}</strong><p className="brief-notice">{result.notice}</p><ResearchTrace trace={result.trace} delivery={result.delivery}/></div></div><div className="results-summary"><div><span className="metric-icon"><Layers3 size={19}/></span><span><strong>03</strong><small>Distinct concept directions</small></span></div><div><span className="metric-icon"><Target size={19}/></span><span><strong>{hasScores?<>{Math.max(...result.concepts.map(concept=>concept.audienceFit as number))}<em>/100</em></>:<>{String(livePlaces).padStart(2,'0')}</>}</strong><small>{hasScores?'Highest illustrative fit':'Live Qloo places'}</small></span></div><div><span className="metric-icon"><Fingerprint size={19}/></span><span><strong>{String(result.signals.length).padStart(2,'0')}</strong><small>Cultural connections</small></span></div><div><span className="metric-icon"><Bookmark size={19}/></span><span><strong>{String(result.concepts.filter(concept=>saved.includes(concept.id)).length).padStart(2,'0')}</strong><small>Ideas in your collection</small></span></div></div>
    <div className="concept-toolbar"><div className="section-inline-heading"><h2>{savedOnly?'Your collection':'Meet the possibilities'}</h2><span className="count-badge">{filtered.length}</span></div><div className="concept-toolbar-actions"><button className={`filter-button ${savedOnly?'is-active':''}`} aria-pressed={savedOnly} onClick={()=>setSavedOnly(!savedOnly)}><Bookmark size={14}/> Saved</button><div className="view-switch" role="group" aria-label="Concept display"><button aria-label="Card view" aria-pressed={view==='cards'} className={view==='cards'?'active':''} onClick={()=>setView('cards')}><LayoutGrid size={14}/></button><button aria-label="Comparison matrix view" aria-pressed={view==='matrix'} className={view==='matrix'?'active':''} onClick={()=>setView('matrix')}><BarIcon/></button></div></div></div>
    {filtered.length===0?<div className="empty-state panel"><Bookmark size={30}/><h3>Good ideas deserve a place.</h3><p>Save a concept in this exploration to start your collection.</p><Button variant="secondary" onClick={()=>setSavedOnly(false)}>Explore the concepts <ArrowRight size={15}/></Button></div>:view==='cards'?<div className="concept-grid">{filtered.map((concept,index)=><article className={`concept-card ${selected===concept.id?'is-selected':''}`} key={concept.id}><div className={`concept-photo photo-${concept.id}`}><img src={concept.image} alt={concept.imageAlt ?? `Illustrative ${result.project.businessType.toLowerCase()} concept inspiration`} loading="lazy"/><div className="concept-photo-shade"/><span className="concept-id">DIRECTION {concept.direction ?? String(index+1).padStart(2,'0')}</span><button className={`save-button ${saved.includes(concept.id)?'saved':''}`} aria-label={`${saved.includes(concept.id)?'Unsave':'Save'} ${concept.name}`} aria-pressed={saved.includes(concept.id)} onClick={()=>save(concept.id)}><Bookmark size={16} fill={saved.includes(concept.id)?'currentColor':'none'}/></button><span className="concept-photo-bottom"><span>{concept.personality?.toUpperCase() ?? 'MOCK CONCEPT DIRECTION'}</span><ArrowUpRight size={19}/></span></div><div className="concept-card-content"><div className="concept-name-row"><h3>{concept.name}</h3>{concept.audienceFit!=null?<span className="mini-score">{concept.audienceFit}<small>SAMPLE FIT</small></span>:<span className="mini-score is-evidence">EVIDENCE<small>BASED</small></span>}</div><p className="concept-tagline">{concept.tagline}</p><p className="concept-description">{concept.description}</p><div className="taste-tags">{concept.signals.map(signal=><span key={signal}>{signal}</span>)}</div><div className="concept-card-foot"><span><small>{result.conceptMode==='evidence_composed'?'BUILT FROM QLOO EVIDENCE':'ILLUSTRATIVE PILOT'}</small><strong>{concept.investment}</strong></span><button aria-label={`Explore ${concept.name}`} onClick={()=>{select(concept.id);open(concept)}}>Explore concept <ArrowUpRight size={15}/></button></div>{concept.decisions.length>0&&<><button className="why-toggle" onClick={()=>setWhyOpen(whyOpen===concept.id?null:concept.id)} aria-expanded={whyOpen===concept.id}>Why this direction? <ChevronRight size={13} className={whyOpen===concept.id?'is-open':''}/></button>{whyOpen===concept.id&&<EvidencePanel concept={concept} evidence={result.evidence}/>}</>}</div><button className="select-concept" aria-label={`Select ${concept.name} insights`} aria-pressed={selected===concept.id} onClick={()=>select(concept.id)}>{selected===concept.id?<><Check size={12}/> Currently exploring</>:<>View supporting insights <ArrowRight size={12}/></>}</button></article>)}</div>:<div className="matrix-container panel"><table className="concept-matrix"><caption>Illustrative concept comparison. Scores are sample estimates.</caption><thead><tr><th>CONCEPT</th><th>AUDIENCE FIT</th><th>CULTURAL RELEVANCE</th><th>FEASIBILITY</th><th>INVESTMENT</th><th/></tr></thead><tbody>{filtered.map(concept=><tr key={concept.id}><td><strong>{concept.name}</strong><small>{concept.tagline}</small></td><td>{concept.audienceFit!=null?<><b>{concept.audienceFit}</b><MiniBar value={concept.audienceFit}/></>:<b className="is-null">—</b>}</td><td>{concept.culturalRelevance!=null?<><b>{concept.culturalRelevance}</b><MiniBar value={concept.culturalRelevance}/></>:<b className="is-null">—</b>}</td><td>{concept.feasibility!=null?<><b>{concept.feasibility}</b><MiniBar value={concept.feasibility}/></>:<b className="is-null">—</b>}</td><td>{concept.investment}</td><td><button className="icon-button" aria-label={`Explore ${concept.name}`} onClick={()=>open(concept)}><ArrowUpRight size={17}/></button></td></tr>)}</tbody></table></div>}
    <div className="insight-workspace"><div className="insight-main panel"><div className="insight-header"><span className="small-cap"><span className="orange-dot"/> BEHIND THE IDEA</span><span className="sample-label">{result.dataMode==='live'?'QLOO AGGREGATE SIGNALS':'ILLUSTRATIVE CULTURAL SIGNALS'}</span></div><div className="insight-title"><h2>Every good idea<br/>has <em>interesting roots.</em></h2><span className="circle-arrow"><Fingerprint size={28} strokeWidth={1}/></span></div><div className="insight-tabs" role="tablist" aria-label="Concept insights">{([{id:'signals',label:'Cultural signals'},{id:'constellation',label:'Constellation'},{id:'heat',label:'Cultural heat'},{id:'anchors',label:'Anchor tournament'},{id:'blueprint',label:'Blueprint'},{id:'source',label:'Evidence & source'}] as const).map(tab=><button key={tab.id} role="tab" aria-selected={insightTab===tab.id} className={insightTab===tab.id?'active':''} onClick={()=>setInsightTab(tab.id)}>{tab.label}</button>)}</div><div className="insight-tab-content" role="tabpanel">{insightTab==='signals'?<>{result.signals.slice(0,3).map((signal,index)=><SignalRow signal={signal} index={index} key={`${signal.label}-${index}`}/>)}</>:insightTab==='constellation'?<CulturalConstellation evidence={result.evidence} concepts={result.concepts} selectedId={selected} onSelect={select} onInspect={(id)=>onInspect?.(id)}/>:insightTab==='heat'?<CulturalHeat evidence={result.evidence} onInspect={(id)=>onInspect?.(id)}/>:insightTab==='anchors'?<AnchorTournament evidence={result.evidence} audience={result.project.audience} location={result.project.location}/>:insightTab==='blueprint'?<div className="blueprint-preview"><span className="tiny-cap">{chosen.name.toUpperCase()} · SAMPLE EXPERIENCE</span><h3>{chosen.tagline}</h3><p>{chosen.description}</p><div className="blueprint-points">{chosen.moments?.map(moment=><span key={moment.title}><Lightbulb size={16}/>{moment.title}</span>)}</div><button className="text-link" onClick={()=>open(chosen)}>Open the full concept <ArrowUpRight size={14}/></button></div>:<div className="source-panel"><ShieldCheck size={25}/><h3>Clear about what’s behind the idea.</h3><p>{result.notice}</p><p>Concept stories, fit scores, estimated costs, and scenario changes are illustrative prototype content. Qloo affinities, when connected, appear separately as aggregate evidence.</p><a href={result.provenance?.documentation??'https://github.com/qloo/qloo-hackathon-kit'} target="_blank" rel="noreferrer">Explore the Qloo Hackathon Kit <ArrowUpRight size={13}/></a></div>}</div></div><aside className="decision-card"><span className="small-cap">A DIFFERENT AUDIENCE.<br/>A DIFFERENT POSSIBILITY.</span><div className="decision-art"><Users size={32} strokeWidth={1}/><span/><span/></div><h3>What if you<br/><em>changed the lens?</em></h3><p>See how a new audience could reshape the opportunity.</p><Button variant="secondary" onClick={compare}>Open scenario lab <ArrowUpRight size={16}/></Button><span className="decision-foot">SMALL SHIFTS. INTERESTING CONSEQUENCES.</span></aside></div><div className="evidence-footnote"><ShieldCheck size={14}/><p>{result.dataMode==='live'?'Live Qloo aggregate signals are connected.':'You’re exploring with clearly labeled mock data.'} All concept-fit scores and investment ranges are illustrative estimates.</p><span>CURIOSITY, WITH CONTEXT.</span></div>
  </div>
}
function BarIcon(){return <svg width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden="true"><path d="M2 3h11M2 7.5h11M2 12h11" stroke="currentColor" strokeWidth="1.5"/></svg>}
function MiniBar({value}:{value:number}){return <span className="mini-bar"><i style={{width:`${value}%`}}/></span>}
function EvidencePanel({concept,evidence}:{concept:Concept;evidence:Evidence[]}) {
  const byId=new Map(evidence.map(item=>[item.id,item]))
  return <div className="evidence-panel">
    <div className="evidence-panel-head">
      <span className="small-cap"><span className="orange-dot"/> OBSERVED → INTERPRETED → PROPOSED</span>
    </div>
    {concept.decisions.map(decision=>(
      <div className="decision" key={decision.id}>
        <span className="decision-field">{decision.field}</span>
        <p className="decision-proposal">{decision.proposal}</p>
        <div className="decision-sources">
          <span className="decision-origin">CultureForge rule · {decision.ruleId}</span>
          {decision.evidenceIds.map(id=>{
            const item=byId.get(id)
            if(!item) return null
            return <span className="evidence-chip" key={id}>
              <b>{item.kind==='tag'?'AUDIENCE TAG':'QLOO PLACE'}</b>
              {item.label}
              {item.affinity!=null&&<i>affinity {item.affinity.toFixed(3)}</i>}
              {item.popularity!=null&&<i>popularity {item.popularity.toFixed(4)}</i>}
              {item.rating!=null&&<i>rated {item.rating}</i>}
            </span>
          })}
        </div>
      </div>
    ))}
    {concept.limitations.length>0&&<ul className="decision-limitations">{concept.limitations.map((line,index)=><li key={index}>{line}</li>)}</ul>}
  </div>
}

function ResearchTrace({trace,delivery}:{trace:TraceEvent[];delivery?:Delivery|null}) {
  if(!trace.length) return null
  const kind=delivery?.kind
  const label=kind==='cache'?'Cached Qloo evidence':kind==='fresh'?'Fresh Qloo evidence':kind==='snapshot'?'Saved Qloo snapshot':'Qloo evidence'
  const stamp=delivery?.acquiredAt?new Date(delivery.acquiredAt).toLocaleTimeString():null
  const spent=delivery?.transportRequests
  return <details className="research-trace">
    <summary><span className={`trace-badge is-${kind??'mock'}`}>{label}</span>How this was researched{stamp&&<em>acquired {stamp}</em>}{spent===0&&<em className="trace-free">0 upstream requests</em>}</summary>
    <div className="trace-list">
      {trace.map(event=>(
        <div className="trace-row" key={event.id}>
          <span className={`trace-status is-${event.status}`}/>
          <span className="trace-step">{event.step.replace(/-/g,' ')}</span>
          {event.workflow&&<span className="trace-workflow">qloo {event.workflow}</span>}
          {event.durationMs!=null&&<span className="trace-duration">{(event.durationMs/1000).toFixed(1)}s</span>}
          {event.resultCount!=null&&<span className="trace-count">{event.resultCount} results</span>}
          {event.detail&&<span className="trace-detail">{event.detail}</span>}
        </div>
      ))}
      {spent!=null&&<div className="trace-row trace-spend"><span className="trace-detail">This result cost {spent} upstream {spent===1?'request':'requests'}. {spent===0?'The evidence was already held, so the quota was not touched.':'Only the missing evidence had to be fetched.'}</span></div>}
    </div>
  </details>
}

function SignalRow({signal,index}:{signal:CulturalSignal;index:number}){return <div className="evidence-row"><span className="evidence-index">0{index+1}</span><div><strong>{signal.label}</strong><p>{signal.detail}</p></div><span className="evidence-value">{signal.score!=null?<>{signal.score}<small>SAMPLE INDEX</small></>:signal.affinity!=null?<>{signal.affinity.toFixed(3)}<small>QLOO AFFINITY</small></>:<ArrowUpRight size={17}/>}</span></div>}

function Compare({result,back,apply,busy}:{result:GenerateResponse;back:()=>void;apply:(audience:string,scores:number[])=>void;busy?:boolean}) {
  const [live,setLive]=useState(false)
  const startingProfile=result.project.audience==='Independent creatives'?'Mindful professionals':'Independent creatives'
  const [draft,setDraft]=useState(startingProfile)
  const [weights,setWeights]=useState(startingProfile==='Independent creatives'?[70,95,35]:[45,45,95])
  const [preset,setPreset]=useState(startingProfile)
  const profiles:Record<string,number[]>={'Independent creatives':[70,95,35],'Mindful professionals':[45,45,95],'Young families':[95,35,65],'Design-conscious Gen Z':[60,85,35]}
  const unchanged=draft.trim()===result.project.audience.trim()
  const scenario=mockGenerate({...result.project,audience:draft.trim()||result.project.audience})
  // Live concepts carry no fit score, so the scenario lab falls back to the
  // sample model's own numbers rather than inventing a shift.
  const baseScore=(concept:Concept,index:number)=>typeof concept.audienceFit==='number'?concept.audienceFit:scenario.concepts[index]?.audienceFit??60
  const newScores=result.concepts.map((concept,index)=>Math.max(45,Math.min(99,Math.round((unchanged?baseScore(concept,index):baseScore(scenario.concepts[index],index)) + (weights[0]-65)*[.05,.02,.25][index]+(weights[1]-80)*[.15,-.04,.04][index]+(weights[2]-45)*[-.12,.22,.02][index]))))
  const winnerIndex=newScores.indexOf(Math.max(...newScores))
  function chooseProfile(profile:string){setPreset(profile);setDraft(profile);setWeights(profiles[profile])}
  return <div className="compare-page"><button className="back-link" onClick={back}><ArrowLeft size={14}/> Back to concept studio</button><div className="page-heading"><div><Eyebrow>A NEW LENS ON YOUR NEXT MOVE</Eyebrow><h1>Same vision.<br/><em>New possibilities.</em></h1><p>Change the audience. Explore what could change with them.</p></div><span className="scenario-pill"><FlaskConical size={14}/> SCENARIO LAB <i/> SAMPLE MODEL</span></div><div className="scenario-layout"><aside className="scenario-controls panel"><div className="controls-heading"><span className="feature-icon"><SlidersHorizontal size={19}/></span><h3>Shift your perspective.</h3></div><label className="field"><span>New target audience</span><textarea maxLength={240} rows={2} value={draft} onChange={event=>{setDraft(event.target.value);setPreset('')}} placeholder="Describe an audience to explore…"/></label><div className="scenario-presets">{audiencePresets.map(profile=><button className={preset===profile?'selected':''} aria-pressed={preset===profile} key={profile} onClick={()=>chooseProfile(profile)}>{profile}{preset===profile?<Check size={12}/>:<Plus size={12}/>}</button>)}</div><div className="controls-rule"/><span className="small-cap">WHAT MATTERS TO THIS AUDIENCE?</span><div className="weight-sliders">{['Community & connection','Discovery & novelty','Calm & wellbeing'].map((label,index)=><label key={label}><span>{label}<b>{weights[index]}<small>/100</small></b></span><input type="range" min="0" max="100" value={weights[index]} onChange={event=>setWeights(weights.map((value,i)=>i===index?Number(event.target.value):value))}/><small>{['A place to belong','Something worth finding','Room to slow down'][index]}</small></label>)}</div><div className="sample-model-note"><CircleHelp size={14}/><p>Interactive sample model. These preferences change illustrative scores, not live Qloo measurements.</p></div></aside><div className="scenario-output"><div className="scenario-audience-cards"><div><span className="small-cap">ORIGINAL AUDIENCE</span><h3>{result.project.audience}</h3><span><MapPin size={12}/>{result.project.location}</span></div><span className="scenario-flow-arrow"><ArrowRight size={17}/></span><div><span className="small-cap"><span className="orange-dot"/> YOUR NEW SCENARIO</span><h3>{draft||'Your next audience'}</h3><span>New concept directions from the mock catalog</span></div></div><div className="scenario-chart panel"><div className="chart-heading"><div><h3>A change in perspective.</h3><p>Illustrative concept-fit scores · out of 100</p></div><div className="chart-legend"><span><i/> Original</span><span><i/> New scenario</span></div></div><div className="scenario-chart-rows">{result.concepts.map((concept,index)=><div className="scenario-chart-row" key={concept.id}><div className="chart-row-label"><span>{concept.direction??String(index+1).padStart(2,'0')}</span><strong>{concept.name}<small className="new-direction">New: {scenario.concepts[index].name}</small></strong><b className={newScores[index]-baseScore(concept,index)>=0?'positive':'negative'}>{newScores[index]-baseScore(concept,index)>0?'+':''}{newScores[index]-baseScore(concept,index)}<small> pts</small></b></div><div className="paired-bars"><div><i style={{width:`${concept.audienceFit}%`}}/><span>{concept.audienceFit}</span></div><div><i style={{width:`${newScores[index]}%`}}/><span>{newScores[index]}</span></div></div></div>)}</div><div className="chart-axis"><span>0</span><span>25</span><span>50</span><span>75</span><span>100</span></div></div><div className="scenario-insight"><span className="insight-star"><Sparkles size={21}/></span><div><span className="small-cap">AN INTERESTING DIRECTION</span><h3>{scenario.concepts[winnerIndex].name} comes into focus.</h3><p>The sample model puts this concept first for your adjusted preferences. Use it as a conversation starter for further audience research.</p></div></div><div className="scenario-apply"><button className="text-link" onClick={()=>{setDraft(result.project.audience);setWeights([65,80,45]);setPreset('')}}>Reset scenario</button><Button disabled={draft.trim().length<2} onClick={()=>apply(draft.trim(),newScores)}>Apply this scenario <ArrowUpRight size={16}/></Button>{busy&&<span className="scenario-busy">Re-researching with Qloo… this spends one workflow call.</span>}{result.conceptMode==='evidence_composed'&&<AudienceComparison project={result.project} currentAudience={result.project.audience} alternativeAudience={draft.trim()||result.project.audience} currentEvidence={result.evidence} busy={busy} onApply={(audience)=>apply(audience,newScores)}/>}</div></div></div></div>
}
function ConceptModal({concept,saved,save,close}:{concept:Concept;saved:boolean;save:()=>void;close:()=>void}) {
  const dialogRef=useRef<HTMLDivElement>(null)
  useEffect(()=>{
    const previous=document.activeElement as HTMLElement|null
    const original=document.body.style.overflow;document.body.style.overflow='hidden'
    dialogRef.current?.querySelector<HTMLButtonElement>('button')?.focus()
    function keydown(event:KeyboardEvent){if(event.key==='Escape')close();if(event.key==='Tab'){const nodes=dialogRef.current?.querySelectorAll<HTMLElement>('button,a[href],input');if(!nodes?.length)return;const first=nodes[0],last=nodes[nodes.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}}}
    document.addEventListener('keydown',keydown)
    return()=>{document.body.style.overflow=original;document.removeEventListener('keydown',keydown);previous?.focus()}
  },[close])
  const rituals=concept.moments?.length?concept.moments:[
    {title:'Test the signature offering',description:'Invite a small group to try the core experience.'},
    {title:'Refine the delivery',description:'Ask participants about timing, access, and the format.'},
    {title:'Gather local feedback',description:'Use direct feedback to refine the next pilot.'},
  ]

  return <div className="modal-backdrop" onClick={close}><div className="concept-modal" ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="concept-modal-title" onClick={event=>event.stopPropagation()}><div className="modal-cover" style={{backgroundImage:`linear-gradient(0deg,rgba(0,0,0,.75),rgba(0,0,0,.1)),url(${concept.image})`}}><button className="modal-close" onClick={close} aria-label="Close concept blueprint"><X size={19}/></button><span className="small-cap">DIRECTION {concept.direction??'01'} / EXPERIENCE BLUEPRINT</span><h2 id="concept-modal-title">{concept.name}</h2><p>{concept.tagline}</p></div><div className="modal-content"><div className="modal-intro"><span className="sample-label">ILLUSTRATIVE CONCEPT · SAMPLE ESTIMATES</span><button className={`filter-button ${saved?'is-active':''}`} onClick={save}><Bookmark size={14} fill={saved?'currentColor':'none'}/>{saved?'Saved to collection':'Save concept'}</button></div><h3>The idea, in a little more color.</h3><p className="modal-description">{concept.description}</p><div className="personalization-note"><strong>Why this mock direction?</strong><p>{concept.audienceRationale}</p><p>{concept.implementationNote}</p></div><div className="modal-stats"><div><small>AUDIENCE FIT · SAMPLE</small><b>{concept.audienceFit}<em>/100</em></b></div><div><small>ILLUSTRATIVE PILOT BUDGET</small><b>{concept.investment}</b></div><div><small>EXPERIENCE PERSONALITY</small><b>{concept.personality??'Audience-led pilot'}</b></div></div><h3>Three moments that make it yours.</h3><div className="ritual-grid">{rituals.map((ritual,index)=><div key={ritual.title}><span>0{index+1}</span><strong>{ritual.title}</strong><p>{ritual.description}</p></div>)}</div><div className="modal-themes"><span className="small-cap">CULTURAL THEMES TO EXPLORE</span><div className="taste-tags">{concept.signals.map(signal=><span key={signal}>{signal}</span>)}</div></div><div className="launch-roadmap"><div><span className="small-cap">YOUR FIRST 30 DAYS</span><h3>Start small. Learn something.</h3></div><ol><li><span>01</span><p><strong>Talk to your audience.</strong>Interview five people about the rituals, places, and experiences they return to.</p></li><li><span>02</span><p><strong>Prototype the signature moment.</strong>Run a small pop-up or invite-only session to test the experience.</p></li><li><span>03</span><p><strong>Follow the signals.</strong>Gather feedback and refine what people wanted to come back for.</p></li></ol></div><div className="modal-bottom"><span><ShieldCheck size={14}/> A starting point for research, not a validated business plan.</span><Button variant="secondary" onClick={close}>Back to the possibilities <ArrowRight size={15}/></Button></div></div></div></div>
}
