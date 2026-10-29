import { useEffect, useState } from 'react'
import { ArrowLeft, ArrowRight, ArrowUpRight, AudioLines, Check, Coffee, Fingerprint, FlaskConical, Globe2, Layers3, Leaf, Lightbulb, MapPin, Play, Plus, Search, ShieldCheck, Sparkles, Users, Waves } from 'lucide-react'
import type { GenerateResponse, ProjectRequest } from '../contracts'
import { listExplorations } from '../api'
import type { ClarificationAsk, SavedExploration } from '../api'
import { AgentTrace } from '../components/AgentTrace'
import { RunExpectation, RUN_TIME_NOTE } from '../components/RunExpectation'
import { ExamplePicker } from '../components/ExamplePicker'
import demoBriefs from '../../shared/demoBriefs.json'
import { BusinessIcon, Eyebrow, Button } from './StudioChrome'
import { audiencePresets, objectives } from '../studioShared'

export function Home({ start, demo, explore, openExploration, runExample }: { start: () => void; demo: () => void; explore: () => void; openExploration: (id: string) => void; runExample: (project: ProjectRequest) => void }) {
  return <div className="home-page studio-home" data-tour="overview">
    <div className="welcome-row"><span>THE CULTURAL HYPOTHESIS STUDIO</span><span className="edition-tag">EVIDENCE · INTERPRETATION · CHALLENGE</span></div>
    <section className="hero studio-hero">
      <div className="hero-copy">
        <Eyebrow>DON’T JUST COLLECT SIGNALS</Eyebrow>
        <h1>Make an idea<br/>answer to its <em>evidence.</em></h1>
        <p>Turn your business brief into Qloo-backed directions. Trace each proposal to its sources, challenge its anchor, then remove evidence and see what changes.</p>
        <div className="hero-actions"><Button onClick={start}>Build a hypothesis <ArrowUpRight size={18}/></Button><button className="play-button" onClick={demo}><span><Play size={12} fill="currentColor"/></span> Run the example brief</button></div>
        <div className="hero-assurance"><ShieldCheck size={14}/> Cultural fit within retrieved evidence <span/> No demand or revenue predictions</div>
      </div>
      <div className="hypothesis-visual" aria-label="CultureForge evidence process">
        <div className="hypothesis-visual-head"><span>THE CULTUREFORGE METHOD</span><Waves size={18}/></div>
        <div className="hypothesis-step"><span>01</span><div><small>OBSERVED</small><strong>Cultural signals + returned places</strong></div><span className="hypothesis-source">QLOO EVIDENCE</span></div>
        <div className="hypothesis-connector" aria-hidden="true"/>
        <div className="hypothesis-step is-interpretation"><span>02</span><div><small>INTERPRETED</small><strong>A place based business direction</strong></div><span className="hypothesis-source">CULTUREFORGE</span></div>
        <div className="hypothesis-connector" aria-hidden="true"/>
        <div className="hypothesis-step is-test"><span>03</span><div><small>CHALLENGED</small><strong>Change the anchor. Remove evidence.</strong></div><span className="hypothesis-source">YOU DECIDE</span></div>
        <p className="hypothesis-foot">A verdict describes anchor fit in the retrieved sample. It does not validate a business.</p>
      </div>
    </section>
    <DemoShowcase onRun={runExample}/>
    <section className="possibility-strip studio-method-strip" aria-label="How an exploration works">
      <div><span className="strip-number">01</span><span><strong>Compose</strong><small>Build directions from cited evidence.</small></span></div><ArrowRight size={16}/>
      <div><span className="strip-number">02</span><span><strong>Challenge</strong><small>Test the claim against another place.</small></span></div><ArrowRight size={16}/>
      <div><span className="strip-number">03</span><span><strong>Recompose</strong><small>Remove a place and rebuild from what remains.</small></span></div>
    </section>
    <section className="discovery-section studio-capabilities">
      <div className="section-heading"><div><Eyebrow>WHERE CULTUREFORGE ADDS ITS OWN WORK</Eyebrow><h2>From returned data to<br/><em>a decision you can inspect.</em></h2></div><button className="text-link" onClick={explore}>Open the concept studio <ArrowUpRight size={15}/></button></div>
      <div className="discovery-grid">
        <button className="discovery-card" onClick={explore}><div className="discovery-top"><span className="feature-icon"><Fingerprint size={19}/></span><span className="capability-index">01</span></div><h3>Trace every direction.</h3><p>See which returned places and signals each business direction depends on. Qloo supplies the cultural evidence; CultureForge forms the proposal.</p><span className="feature-bottom">SOURCE → DECISION TRACE <ArrowUpRight size={14}/></span></button>
        <button className="discovery-card" onClick={explore}><div className="discovery-top"><span className="feature-icon"><FlaskConical size={19}/></span><span className="capability-index">02</span></div><h3>Change one assumption.</h3><p>Hold the direction steady and test it against another returned place. Watch the verdict change when its anchor changes.</p><span className="feature-bottom">COUNTERFACTUAL ANCHOR TEST <ArrowUpRight size={14}/></span></button>
        <button className="discovery-card" onClick={explore}><div className="discovery-top"><span className="feature-icon"><Layers3 size={19}/></span><span className="capability-index">03</span></div><h3>Take evidence away.</h3><p>Remove a venue and recompose the descriptions, citations, images and anchors from the remaining evidence.</p><span className="feature-bottom">EVIDENCE REMOVAL + RECOMPOSITION <ArrowUpRight size={14}/></span></button>
      </div>
    </section>
    <SavedExplorations onOpen={openExploration}/>
    <div className="home-bottom-note"><span><Sparkles size={16}/> Ideas are easier to trust when they can be challenged.</span><span>Explore carefully. Build thoughtfully.</span></div>
  </div>
}

const SHOWCASE = ['tokyo-morning-bakery', 'paris-ice-cream', 'melbourne-specialty-coffee']
export function DemoShowcase({ onRun, title }: { onRun: (project: ProjectRequest) => void; title?: string }) {
  const [category, setCategory] = useState('All')
  const categories = ['All', ...new Set(demoBriefs.briefs.map((brief) => brief.project.businessType))]
  const ordered = [...SHOWCASE, 'berlin-plant-based-trial', 'mexico-city-bookshop-cafe', 'vienna-plant-based-trial']
  const demos = [...demoBriefs.briefs].sort((a, b) => {
    const rank = (id: string) => ordered.includes(id) ? ordered.indexOf(id) : ordered.length
    return rank(a.id) - rank(b.id)
  }).filter((brief) => category === 'All' || brief.project.businessType === category)
  return <section className="demo-showcase" aria-labelledby="demo-showcase-title">
    <div className="section-heading"><div><Eyebrow>SEE IT WORK</Eyebrow><h2 id="demo-showcase-title">{title ?? <>Try a real example. <em>One tap.</em></>}</h2></div></div>
    <p>Browse {demoBriefs.briefs.length} trial briefs across five business categories. Inspect the evidence and its limits, then try your own idea.</p>
    <div className="showcase-filters" role="group" aria-label="Filter trial ideas by business category">{categories.map((item) => <button type="button" key={item} aria-pressed={category === item} onClick={() => setCategory(item)}>{item}</button>)}</div>
    <ul>{demos.map((brief) => <li key={brief.id}><button type="button" onClick={() => onRun(brief.project as ProjectRequest)} aria-label={`Open the demo: ${brief.label}, ${brief.project.location}`}>
      <span className="demo-place"><MapPin size={14}/>{brief.project.location}</span>
      <strong>{brief.project.businessIdea ?? brief.label}</strong>
      <span className="demo-audience">{brief.project.audience}</span>
      {'trialNote' in brief && <span className="demo-audience">{brief.trialNote}</span>}
      <span className="demo-includes">{brief.project.businessType} · Evidence · Remove a place</span>
      <span className="demo-go">Open demo <ArrowUpRight size={15}/></span>
    </button></li>)}</ul>
  </section>
}

export function SavedExplorations({ onOpen }: { onOpen: (id: string) => void }) {
  const [items, setItems] = useState<SavedExploration[]>([])
  const [loaded, setLoaded] = useState(false)
  useEffect(() => {
    listExplorations()
      .then((data) => setItems(data.explorations))
      .catch(() => setItems([]))
      .finally(() => setLoaded(true))
  }, [])
  if (!loaded) return null
  if (!items.length) return null
  return <section className="saved-explorations">
    <div className="section-heading">
      <div><Eyebrow>REPLAY REAL EXPLORATIONS</Eyebrow><h2>Still here,<br/><em>even after a restart.</em></h2></div>
      <span className="sample-label">RECORDED QLOO EVIDENCE · NO FRESH EXECUTION</span>
    </div>
    <ul className="saved-exploration-list">
      {items.slice(0, 6).map((item) => <li key={item.id}>
        <button onClick={() => onOpen(item.id)}>
          <span className="saved-exploration-title">{item.title}</span>
          <span className="saved-exploration-meta">
            {String((item.brief as { location?: string })?.location ?? 'exploration')} · recorded {new Date(item.updatedAt * 1000).toLocaleDateString()} · {item.versions.length} version{item.versions.length === 1 ? '' : 's'}
          </span>
          <ArrowUpRight size={16}/>
        </button>
      </li>)}
    </ul>
  </section>
}

export function Create({ form, setForm, submit, runExample, error, back }: { form: ProjectRequest; setForm: (project: ProjectRequest) => void; submit: () => void; runExample: (project: ProjectRequest) => void; error: string; back: () => void }) {
  const [custom, setCustom] = useState('')
  const types = [{label:'Food & beverage',icon:Coffee},{label:'Retail',icon:Layers3},{label:'Hospitality',icon:Globe2},{label:'Wellness',icon:Leaf},{label:'Entertainment',icon:AudioLines}] as const
  const allGoals = [...new Set([...objectives, ...form.objectives])]
  function toggle(goal: string) { setForm({...form, objectives: form.objectives.includes(goal) ? form.objectives.filter(value => value !== goal) : [...form.objectives, goal]}) }
  const add = () => { const value=custom.trim(); if(value && !form.objectives.includes(value)) toggle(value); setCustom('') }
  return <div className="create-page" data-tour="brief"><button className="back-link" onClick={back}><ArrowLeft size={14}/> Back to overview</button><div className="page-heading"><div><Eyebrow>THE BEGINNING OF SOMETHING GOOD</Eyebrow><h1>Tell us what you’re<br/><em>dreaming of.</em></h1><p>You bring the ambition. We’ll find the cultural connections.</p></div><span className="page-index">EXPLORATION / 001</span></div><div className="create-layout"><form className="creation-form panel" onSubmit={event => { event.preventDefault(); submit() }}>{error && <div className="api-error" role="alert">{error}</div>}<div className="form-section"><div className="form-section-title"><span>01</span><div><h3>What are you building?</h3><p>Choose the world your idea belongs in.</p></div></div><label className="field"><span>Business idea</span><input id="brief-idea" maxLength={160} value={form.businessIdea ?? ''} onChange={event => setForm({...form, businessIdea: event.target.value})} placeholder="e.g. Artisan bakery, record shop, ceramics studio"/><small>Name one business (café, bakery, bookshop, ice cream parlour, record shop) and a city. Qloo covers large cities best; a niche idea in a small city may come back as “not enough evidence”, and the page will say why. First evidence opens automatically when available, while research continues in the background. Availability and demand still need testing.</small></label><div className="business-types">{types.map(({label,icon:Icon})=><button type="button" className={form.businessType===label?'business-tile selected':'business-tile'} aria-pressed={form.businessType===label} key={label} onClick={()=>setForm({...form,businessType:label})}><Icon size={20}/><span>{label}</span>{form.businessType===label&&<Check size={12}/>}</button>)}</div></div><div className="form-section"><div className="form-section-title"><span>02</span><div><h3>Who do you want to move?</h3><p>Describe the people at the heart of your idea.</p></div></div><label className="field"><span>Target audience</span><div className="input-with-icon"><Users size={16}/><input id="brief-audience" required minLength={2} maxLength={240} value={form.audience} onChange={event=>setForm({...form,audience:event.target.value})}/></div></label><div className="preset-row"><span>TRY</span>{audiencePresets.slice(0,3).map(preset=><button type="button" key={preset} onClick={()=>setForm({...form,audience:preset})}>{preset}<Plus size={10}/></button>)}</div><div className="field-grid"><label className="field"><span>Location</span><div className="input-with-icon"><MapPin size={16}/><input id="brief-location" required minLength={2} maxLength={160} value={form.location} onChange={event=>setForm({...form,location:event.target.value})}/></div></label><label className="field"><span>Starting budget</span><select value={form.budget} onChange={event=>setForm({...form,budget:event.target.value})}>{['Under $25k','$25k – $50k','$50k – $100k','$100k+','Still figuring it out'].map(budget=><option key={budget}>{budget}</option>)}</select></label></div></div><div className="form-section"><div className="form-section-title"><span>03</span><div><h3>What would success feel like?</h3><p>Select the things that matter to you.</p></div></div><div className="goal-grid">{allGoals.map(goal=><button type="button" className={`goal-chip ${form.objectives.includes(goal)?'selected':''}`} aria-pressed={form.objectives.includes(goal)} key={goal} onClick={()=>toggle(goal)}><span>{form.objectives.includes(goal)?<Check size={12}/>:<Plus size={12}/>}</span>{goal}</button>)}</div><div className="custom-goal"><input aria-label="Custom objective" placeholder="Something else on your mind?" value={custom} onChange={event=>setCustom(event.target.value)} onKeyDown={event=>{if(event.key==='Enter'){event.preventDefault();add()}}}/><button type="button" onClick={add} disabled={!custom.trim()} aria-label="Add custom objective"><Plus size={15}/></button></div></div><div className="form-submit-row"><span><ShieldCheck size={14}/> Your vision stays yours.</span><small className="submit-time-note">{RUN_TIME_NOTE}</small><Button type="submit">Find my cultural edge <ArrowUpRight size={17}/></Button></div></form><aside className="creation-aside"><ExamplePicker onRun={runExample}/><div className="brief-preview panel"><span className="small-cap"><span className="orange-dot"/> YOUR EXPLORATION, AT A GLANCE</span><div className="brief-art"><Fingerprint size={52} strokeWidth={1}/><span/><span/></div><h3>A little context.<br/><em>A lot of possibility.</em></h3><dl><div><dt>Business</dt><dd>{form.businessIdea || form.businessType}</dd></div><div><dt>Location</dt><dd>{form.location || 'Your neighborhood'}</dd></div><div><dt>Budget</dt><dd>{form.budget}</dd></div></dl><div className="brief-deliverables"><span><Check size={13}/> Up to 3 concept directions</span><span><Check size={13}/> Cultural signals & evidence</span><span><Check size={13}/> Audience scenario comparison</span></div></div><div className="curiosity-note"><Lightbulb size={18}/><p><strong>Get specific. Stay curious.</strong>The most interesting connections often start with the smallest details.</p></div></aside></div></div>
}
export function Progress({project,runId,onComplete,onClarify,onGiveUp,onRetry,onChangeLocation,onOpenPartial,autoOpenPartial}:{project:ProjectRequest;runId?:string;autoOpenPartial?:boolean;onComplete?:(result:GenerateResponse)=>void;onClarify?:(ask:ClarificationAsk)=>void;onGiveUp?:()=>void;onRetry?:()=>void;onChangeLocation?:()=>void;onOpenPartial?:(result:GenerateResponse)=>void}) {
  // The steps are lit by the agent's real events, not by a timer. A run that
  // takes twenty-five seconds must not show every step as complete.
  return <div className="progress-page"><span className="small-cap"><span className="orange-dot pulse"/> AGENT WORKSPACE</span><div className="agent-orbit"><div className="orbit-outer"/><div className="orbit-middle"/><span className="orbit-icon"><Waves size={35}/></span><span className="satellite sat-one"><Coffee size={17}/></span><span className="satellite sat-two"><AudioLines size={17}/></span><span className="satellite sat-three"><Leaf size={17}/></span></div><h1>Curiosity is<br/><em>connecting the dots.</em></h1><p>Completed evidence appears here as it arrives. Optional analysis continues in the background.</p><div className="progress-context"><span><BusinessIcon type={project.businessType} size={13}/>{project.businessType}</span><span><MapPin size={13}/>{project.location}</span></div><RunExpectation runId={runId}/>{runId&&<AgentTrace key={runId} runId={runId} onComplete={onComplete as (r:GenerateResponse)=>void} onClarify={onClarify as (a:ClarificationAsk)=>void} onGiveUp={onGiveUp} onRetry={onRetry} onChangeLocation={onChangeLocation} onOpenPartial={onOpenPartial} autoOpenPartial={autoOpenPartial}/>}<span className="progress-footnote"><ShieldCheck size={13}/> {runId?'A real research run. The trace shows retrieval, composition, and any bounded model steps that actually ran.':'Waiting for the backend. The answer comes back with the Qloo calls that produced it, and what it cost.'}</span></div>
}

/**
 * The empty studio.
 *
 * There is no sample exploration to show here. The studio opens on whatever
 * real answer this browser holds, and when it holds none it says so, and
 * offers the one thing that can change that: a real run.
 */
export function NoExploration({ start, runExample }: { start: () => void; runExample: (project: ProjectRequest) => void }) {
  return <div className="results-page"><div className="empty-state panel"><Search size={30}/><h3>No exploration yet.</h3><p>Every direction in this studio is composed from Qloo evidence, so there is nothing to show until one has been researched. Give it a brief and the real research runs — you can watch every Qloo call it makes.</p><Button onClick={start}>Start an exploration <ArrowRight size={15}/></Button></div><DemoShowcase onRun={runExample}/></div>
}

