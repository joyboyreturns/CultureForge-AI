import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import {
  ArrowDownToLine, ArrowLeft, ArrowRight, ArrowUpRight, AudioLines, Share2,
  Bookmark, Check, CheckCheck, ChevronRight, CircleHelp, Coffee,
  Fingerprint, FlaskConical, Globe2, Layers3, LayoutGrid, Leaf, Lightbulb,
  LoaderCircle, MapPin, Menu, Moon, Play, Plus, Search, ShieldCheck, SlidersHorizontal,
  Sparkles, Sun, Target, Users, WandSparkles, Waves, X,
} from 'lucide-react'
import type { Concept, Delivery, Evidence, GenerateResponse, ProjectRequest, TraceEvent } from './contracts'
import { analyzeEvidence, compareAudience, downloadReportPdf, proposeProfile, fetchExploration, fetchHealth, fetchSnapshot, fetchUsage, heldResult, listExplorations, rememberLiveResult, resolveTaste, shareExploration, startResearch, challengeDirections } from './api'
import type { BackendStatus, ChallengeResult, EvidenceAnalysisResult, ProfileProposal, SavedExploration, TasteSeed } from './api'
import { CulturalConstellation } from './components/CulturalConstellation'
import { ProvenanceDrawer } from './components/ProvenanceDrawer'
import { AgentTrace } from './components/AgentTrace'
import { TasteSeeds } from './components/TasteSeeds'
import { AudienceComparison } from './components/AudienceComparison'
import { AnchorTournament } from './components/AnchorTournament'
import { ReplacementProbe } from './components/ReplacementProbe'
import { CulturalHeat } from './components/CulturalHeat'
import { PlaceStrip } from './components/PlaceStrip'
import { Investigation } from './components/Investigation'
import { ChallengePanel, VerdictBadge } from './components/Challenge'
import { EvidenceDependenceMap } from './components/EvidenceDependenceMap'
import type { DependenceSummary } from './components/EvidenceDependenceMap'
import { EvidenceAnalysisPanel } from './components/EvidenceAnalysis'
import { AgentOutcome } from './components/AgentOutcome'
import type { VerdictStep } from './components/Challenge'
import { citationCoverage, evidenceKindLabel } from './evidenceSummary'
import { renderBrief } from './brief'
import { ExamplePicker } from './components/ExamplePicker'
import { AudienceBridge } from './components/AudienceBridge'
import { InterestMap } from './components/InterestMap'
import { EvidenceChat } from './components/EvidenceChat'
import { ProfileChooser } from './components/ProfileChooser'
import demoBriefs from '../shared/demoBriefs.json'
import { GuidedTour } from './components/GuidedTour'
import { DecisionNotebook } from './components/DecisionNotebook'
import { notebookKey, readDecision, renderDecision } from './decisionNotebook'

 type Screen = 'home' | 'create' | 'progress' | 'results' | 'compare'
 type Theme = 'dark' | 'light'
// The first prepared brief is the example: the landing page runs the same
// one, and scripts/prewarm.py fetches its evidence ahead of time.
const initial = demoBriefs.briefs[0].project as ProjectRequest
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
  // The studio opens on whatever real answer this browser already holds, and
  // on nothing at all when it holds none. There is no sample answer to fall
  // back to: an empty studio is honest, a fabricated one is not.
  const [result, setResult] = useState<GenerateResponse | null>(() => heldResult(initial))
  const currentResult = useRef(result)
  currentResult.current = result
  const [selected, setSelected] = useState('')
  const [backend, setBackend] = useState<BackendStatus | null>(null)
  const [saved, setSaved] = useState<string[]>(() => readStored('cultureforge-saved', []))
  const [menuOpen, setMenuOpen] = useState(false)
  const [providerError, setProviderError] = useState('')
  const [modal, setModal] = useState<Concept | null>(null)
  const [toast, setToast] = useState('')
  const [savedOnly, setSavedOnly] = useState(false)
  const [scenarioBusy, setScenarioBusy] = useState(false)
  const [provenanceId, setProvenanceId] = useState<string | null>(null)
  const [dependenceOpen, setDependenceOpen] = useState(false)
  const [dependenceSummary, setDependenceSummary] = useState<DependenceSummary | null>(null)
  const [investigating, setInvestigating] = useState<string | null>(null)
  const [researchRunId, setResearchRunId] = useState<string | null>(null)
  const [seedCandidates, setSeedCandidates] = useState<TasteSeed[] | null>(null)
  // The founder's seed choice outlives the seeds screen. If the agent has to
  // ask for clarification and sends them back to the brief, the signals they
  // already chose — and the ones they dropped — are still what they chose.
  const [seedSelection, setSeedSelection] = useState<string[] | null>(null)
  const [seedBusy, setSeedBusy] = useState(false)
  const [challenge, setChallenge] = useState<ChallengeResult | null>(null)
  const currentChallenge = useRef(challenge)
  currentChallenge.current = challenge
  // Which of Qloo's own sentences the model chose to lead with. It is a
  // display choice and nothing else, so it is asked for once the answer is
  // on screen and never blocks it.
  const [presentation, setPresentation] = useState<Record<string, { sentences?: string[] }>>({})
  const presentationAsked = useRef('')
  const [challengeHistory, setChallengeHistory] = useState<Record<string, VerdictStep[]>>({})
  const [challengeSavedAt, setChallengeSavedAt] = useState<string | null>(null)
  const [challenging, setChallenging] = useState(false)
  const [usage, setUsage] = useState<{ requests: number; upstreamCalls: number } | null>(null)
  const [challengeError, setChallengeError] = useState('')
  const [analysis, setAnalysis] = useState<EvidenceAnalysisResult | null>(null)
  const [analysisBusy, setAnalysisBusy] = useState(false)
  const [analysisError, setAnalysisError] = useState('')
  const [clarification, setClarification] = useState<{ reason: string; question: string; field: string; suggestion?: string | null } | null>(null)
  const [shareUrl, setShareUrl] = useState('')
  const [tourOpen, setTourOpen] = useState(() => new URLSearchParams(window.location.search).get('tour') === '1')
  const [notebookOpen, setNotebookOpen] = useState(false)
  useEffect(() => { setShareUrl('') }, [result, challenge])
  useEffect(() => { setDependenceSummary(null) }, [result])
  const runId = useRef(0)
  const handoffTaken = useRef(false)
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.documentElement.style.colorScheme = theme
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#141412' : '#f6f5f0')
    writeStored('cultureforge-theme', theme)
  }, [theme])
  useEffect(() => { writeStored('cultureforge-saved', saved) }, [saved])
  // A verdict belongs to the directions it judged. When the directions
  // change — a new brief, a recomposition, a saved exploration — the verdict
  // is stale and is dropped rather than shown against the wrong ideas.
  const judgedConcepts = result?.concepts.map((concept) => concept.id).join('|') ?? ''
  // The evidence a verdict was made against. The same direction ids do not
  // guarantee the same evidence: a recomposition keeps the ids and changes
  // the places behind them, and a verdict about the old places is a verdict
  // about nothing.
  const evidenceFingerprint = (result?.evidence ?? []).map((item) => `${item.id}:${item.entityId ?? ''}:${item.label}`).join('|')
  const judgedEvidence = useRef('')
  useEffect(() => {
    // A verdict belongs to the directions it judged, and to the evidence it
    // judged them against. It is dropped when either is no longer on
    // screen; a fresh verdict for what is in front of us is kept.
    if (!challenge) return
    const onScreen = new Set(result?.concepts.map((concept) => concept.id) ?? [])
    const stillOurs = challenge.directions.every((entry) => onScreen.has(entry.directionId))
    if (!stillOurs || (judgedEvidence.current && judgedEvidence.current !== evidenceFingerprint)) {
      judgedEvidence.current = ''
      setChallenge(null)
      setChallengeError('')
    }
  }, [judgedConcepts, evidenceFingerprint, challenge, result])
  useEffect(() => { setAnalysis(null); setAnalysisError('') }, [result, challenge])
  useEffect(() => {
    function startNewExploration() { setProviderError(''); setSavedOnly(false); setScreen('create') }
    window.addEventListener('cultureforge:open-create', startNewExploration)
    return () => window.removeEventListener('cultureforge:open-create', startNewExploration)
  }, [])
  useEffect(() => { if (!toast) return; const timer = window.setTimeout(() => setToast(''), 3000); return () => clearTimeout(timer) }, [toast])
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'instant' }); setMenuOpen(false) }, [screen])
  // What the backend is actually doing right now. The badge says this, not
  // what the app hopes is true.
  useEffect(() => {
    let cancelled = false
    fetchHealth()
      .then((status) => { if (!cancelled) setBackend(status) })
      .catch(() => { if (!cancelled) setBackend({ mode: 'offline', ready: false, reason: 'The backend could not be reached.', workflows: [] }) })
    return () => { cancelled = true }
  }, [])
  // The landing page can hand over an exploration it just performed, with the
  // test that was run on it. Opening it shows that, not an empty form.
  useEffect(() => {
    function apply(detail: unknown) {
      const handoff = detail as { answer?: GenerateResponse; challenge?: ChallengeResult } | null
      if (!handoff?.answer) return false
      // React runs an effect twice in development. Take the hand-over once.
      if (handoffTaken.current) return true
      handoffTaken.current = true
      setResult(handoff.answer)
      setSelected(handoff.answer.concepts?.[0]?.id ?? '')
      if (handoff.challenge) {
        setChallenge(handoff.challenge)
        setChallengeSavedAt(new Date().toLocaleString())
      }
      setScreen('results')
      return true
    }
    function takeHandoff(event: Event) { apply((event as CustomEvent).detail) }
    window.addEventListener('cultureforge:handoff', takeHandoff)
    // The studio is mounted on demand, so the hand-over may already be
    // waiting when this runs. Take it now rather than losing it.
    const waiting = (window as unknown as { __cultureforgeHandoff?: unknown }).__cultureforgeHandoff
    if (waiting) apply(waiting)
    return () => window.removeEventListener('cultureforge:handoff', takeHandoff)
  }, [])

  useEffect(() => {
    // Let the configured model choose from the returned evidence what to show
    // first. It may only return ids, so it cannot write a fact, and the
    // answer is not waited for: the rules are already on screen.
    const places = (result?.evidence ?? []).filter((item) => item.kind === 'entity')
    if (!places.length) return
    // One call per bundle of evidence. A different exploration is a
    // different bundle, and gets its own.
    const key = places.map((item) => item.entityId ?? item.id).join('|')
    if (presentationAsked.current === key) return
    presentationAsked.current = key
    setPresentation({})
    ;(async () => {
      try {
        const { selectPresentation } = await import('./api')
        const chosen = await selectPresentation(result!.evidence)
        if (currentResult.current !== result) return
        if (!chosen?.selections) return
        // The answer is only used if it is still about the evidence on
        // screen. A newer exploration has its own call.
        setPresentation((current) => {
          const stillOurs = (result!.evidence ?? [])
            .filter((item) => item.kind === 'entity')
            .every((item) => !item.entityId || Boolean(chosen.selections[item.entityId]))
          return stillOurs ? { ...current, ...chosen.selections } : current
        })
      } catch {
        // The rules stay. A model that cannot be reached is not an error the
        // founder needs to see.
      }
    })()
  }, [result])

  useEffect(() => {
    const snapshotId = new URLSearchParams(window.location.search).get('snapshot')
    if (!snapshotId) return
    let cancelled = false
    fetchSnapshot(snapshotId)
      .then((data) => {
        if (cancelled) return
        setResult(data); setSelected(data.concepts[0]?.id ?? '01'); setScreen('results')
        judgedEvidence.current = data.evidence.map((item) => `${item.id}:${item.entityId ?? ''}:${item.label}`).join('|')
        setChallenge(data.challenge ?? null)
        setChallengeHistory({})
      })
      .catch((error) => { if (!cancelled) setToast(error instanceof Error ? error.message : 'That snapshot could not be opened.') })
    return () => { cancelled = true }
  }, [])
  function navigate(next: Screen) { if (screen === 'progress') runId.current++; setMenuOpen(false); setScreen(next) }
  function closeTour() {
    setTourOpen(false)
    const url = new URL(window.location.href)
    if (url.searchParams.has('tour')) { url.searchParams.delete('tour'); history.replaceState(null, '', url.pathname + url.search + url.hash) }
  }
  // What the demo has cost the hackathon quota, counted by the server. A
  // judge can see exactly how much of the API the answer took.
  useEffect(() => {
    if (screen !== 'results') return
    let cancelled = false
    fetchUsage()
      .then((value) => { if (!cancelled) setUsage(value) })
      .catch(() => { if (!cancelled) setUsage(null) })
    return () => { cancelled = true }
  }, [screen, result?.projectId])
  // The studio is served either standalone at / or embedded in the prototype's
  // landing page. "Landing" has to work in both cases: hand control back to the
  // prototype when it is embedded, and always fall back to the app's own home
  // screen so the button can never dead-end.
  function goToLanding() {
    window.dispatchEvent(new Event('cultureforge:show-landing'))
    navigate('home')
  }
  const savedHere = result?.concepts.filter(concept => saved.includes(concept.id)) ?? []
  function save(id: string) { setSaved(current => current.includes(id) ? current.filter(value => value !== id) : [...current, id]) }
  /**
   * Answer the brief in one request.
   *
   * This is the one-click path: the example brief, and anything that does
   * not need the founder to confirm their audience seeds. It asks the
   * backend for the same evidence-backed answer the guided path produces,
   * with the same trace behind it. A brief that was researched before comes
   * straight back from the evidence store and costs nothing.
   */
  async function create(project: ProjectRequest = form) {
    const id = ++runId.current
    setProviderError(''); setForm(project); setScreen('progress'); setSavedOnly(false)
    setClarification(null); setResearchRunId(null)
    try {
      // The same research run the guided path uses, so the workspace shows the
      // agent's real steps rather than an animation pretending to be them.
      const { runId: started } = await startResearch(project, project.audience, [])
      if (id !== runId.current) return
      setResearchRunId(started)
    } catch (error) {
      if (id !== runId.current) return
      setProviderError(error instanceof Error ? error.message : 'Research could not finish. Please try again.')
      setScreen('create')
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
      setSeedSelection((current) => {
        const ids = resolution.candidates.map((candidate) => candidate.tagId)
        if (!current) return ids
        const kept = current.filter((id) => ids.includes(id))
        // A different audience resolves to different signals, so the old
        // choice does not carry over; everything is offered again.
        return kept.length ? kept : ids
      })
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
    // The run's answer is a real one, so this browser holds it too: a reload
    // paints the same exploration without asking the backend again.
    rememberLiveResult(data.project, data)
    setResult(data); setSelected(data.concepts[0]?.id ?? '01'); setResearchRunId(null); setScreen('results')
  }

  function onRunClarify(ask: { reason: string; question: string; field: string }) {
    setClarification(ask); setResearchRunId(null); setScreen('create')
  }

  async function shareThisExploration() {
    if (!result) return
    try {
      // The verdicts travel with the link. A shared exploration that arrived
      // without them would be less than what the sender saw.
      const { snapshotId } = await shareExploration(challenge ? { ...result, challenge } : result)
      if (currentResult.current !== result || currentChallenge.current !== challenge) return
      const url = `${window.location.origin}/studio/?snapshot=${encodeURIComponent(snapshotId)}`
      setShareUrl(url)
      try {
        await navigator.clipboard.writeText(url)
        setToast('Share link copied. It reopens exactly this exploration.')
      } catch {
        setToast('Share link created. Copy it from the link shown in the studio.')
      }
    } catch (error) {
      setToast(error instanceof Error ? error.message : 'This exploration could not be shared.')
    }
  }

  async function applyScenario(audience: string, alternative?: { concepts: unknown[]; evidence: Evidence[]; signals: unknown[]; trace: unknown[]; delivery: unknown; notice: string; resolvedTags: string[] }, location = result?.project.location) {
    // The scenario lab re-researches with Qloo. It never shifts a score it
    // computed itself: the new audience is measured against the old one.
    // When the comparison has already researched this audience, that answer
    // is the one applied — the same question is not asked twice.
    if (!result) return
    setScenarioBusy(true)
    try {
      const live = alternative
        ? (alternative as unknown as Awaited<ReturnType<typeof compareAudience>>)
        : await compareAudience({ ...result.project, location: location || result.project.location }, audience)
      if (currentResult.current !== result) { setScenarioBusy(false); return }
      const next: GenerateResponse = {
        ...result,
        project: { ...result.project, audience, location: location || result.project.location },
        concepts: live.concepts,
        signals: live.signals,
        evidence: live.evidence,
        trace: live.trace,
        delivery: live.delivery,
        notice: live.notice,
        // The audience changed, so the seeds changed with it. Keeping the
        // old provenance would say the new directions were retrieved for the
        // old audience's cultural signals.
        provenance: {
          source: 'Qloo API',
          endpoint: 'qloo exec find_tags → recommend',
          documentation: result.provenance?.documentation,
          resolved_tags: live.resolvedTags ?? [],
        },
      }
      setForm(next.project); setResult(next); setSelected(next.concepts[0]?.id ?? ''); setSavedOnly(false)
      setToast(`Re-researched with live Qloo evidence for ${audience} in ${location || result.project.location}.`)
    } catch (error) {
      setToast(error instanceof Error ? error.message : 'The comparison could not be completed.')
    }
    setScenarioBusy(false)
    navigate('results')
  }
  /**
   * Test the directions against the evidence.
   *
   * This is the part that can come back with a no. Qloo ranks the places for
   * this audience's signals, and compares the place each direction is built
   * on with the rest of the neighbourhood. A direction can come out
   * contested, and the order the evidence leaves them in is not always the
   * order they arrived in.
   */
  // The profile the evidence test ranks against is proposed from the brief
  // and shown before the test runs, so a default is never applied silently.
  const [profileProposal, setProfileProposal] = useState<ProfileProposal | null>(null)
  const [profileChoice, setProfileChoice] = useState('')
  const briefAudience = result?.project.audience ?? ''
  useEffect(() => {
    if (!briefAudience) { setProfileProposal(null); return }
    let live = true
    proposeProfile(briefAudience).then((proposal) => {
      if (!live) return
      setProfileProposal(proposal); setProfileChoice(proposal.demographic)
    }).catch(() => { if (live) setProfileProposal(null) })
    return () => { live = false }
  }, [briefAudience])

  async function testDirections(directionId = '', anchorEntityId = '') {
    if (!result || challenging) return
    setChallenging(true); setChallengeError('')
    try {
      // The test is about the exploration on screen, so the screen's own
      // evidence travels with the request. A recomposed brief, or a hand-
      // confirmed audience, is tested as it stands.
      const tested = await challengeDirections(result.project, directionId, anchorEntityId, {
        evidence: result.evidence,
        concepts: result.concepts,
        resolvedTags: result.provenance?.resolved_tags ?? [],
      }, profileChoice)
      if (currentResult.current !== result) { setChallenging(false); return }
      // A re-anchored direction may have changed its verdict. Say so, because
      // "change this assumption and it loses" is the point of the exercise.
      const previous = challenge?.directions.find((entry) => entry.directionId === tested.directions[0]?.directionId)
      const now = tested.directions[0]
      if (previous && now && previous.verdict !== now.verdict) {
        setToast(`Alternative anchor tested: ${now.anchor?.label ?? 'another place'} — ${previous.verdict} → ${now.verdict}. The concept itself was not rebuilt.`)
      }
      judgedEvidence.current = evidenceFingerprint
      if (directionId && challenge && now) {
        // One direction was re-tested. The other two keep their verdicts, and
        // the order is worked out again from all of them.
        const merged = challenge.directions.map((entry) =>
          entry.directionId === now.directionId ? now : entry)
        const rank: Record<string, number> = { supported: 0, unproven: 1, contested: 2 }
        const sorted = [...merged].sort((a, b) =>
          (rank[a.verdict] ?? 1) - (rank[b.verdict] ?? 1) || a.name.localeCompare(b.name))
        // What it was before, so the change is visible and not just asserted.
        // The rank is read from the order the directions were in *before*
        // this test, not from the order they are in now.
        const before = previous ?? merged.find((entry) => entry.directionId === now.directionId)
        const previousOrder = challenge.order ?? challenge.directions.map((entry) => entry.directionId)
        const previousRank = previousOrder.indexOf(now.directionId) + 1
        if (before) {
          const step: VerdictStep = {
            anchor: before.anchor?.label ?? null,
            verdict: before.verdict,
            rank: previousRank,
            at: new Date().toISOString(),
          }
          setChallengeHistory((current) => ({
            ...current,
            [now.directionId]: [...(current[now.directionId] ?? []), step],
          }))
        }
        // The directions are stored in the order the evidence leaves them in,
        // so the panel and the cards cannot disagree about it.
        setChallenge({ ...challenge, directions: sorted, order: sorted.map((entry) => entry.directionId) })
      } else {
        setChallenge(tested)
        setChallengeHistory({})
        setChallengeSavedAt(null)
      }
    } catch (error) {
      if (currentResult.current === result) setChallengeError(error instanceof Error ? error.message : 'The directions could not be tested.')
    }
    setChallenging(false)
  }

  async function analyzeCurrentEvidence() {
    if (!result || analysisBusy) return
    setAnalysisBusy(true); setAnalysisError('')
    try {
      const answer = await analyzeEvidence(result.project, result.evidence, result.concepts, challenge)
      if (currentResult.current !== result || currentChallenge.current !== challenge) { setAnalysisBusy(false); return }
      setAnalysis(answer)
    } catch (error) {
      if (currentResult.current === result && currentChallenge.current === challenge) setAnalysisError(error instanceof Error ? error.message : 'Evidence analysis could not be completed.')
    }
    setAnalysisBusy(false)
  }

  function exportBrief() {
    if (!result) return
    const entries = savedHere.length ? savedHere : result.concepts
    const notes = entries.map((concept) => {
      const draft = readDecision(notebookKey(result, concept))
      return draft ? `\n\n# Decision record: ${concept.name}\n${renderDecision(draft)}` : ''
    }).join('')
    const text = renderBrief(result, entries, challenge) + notes
    const url = URL.createObjectURL(new Blob([text], { type: 'text/markdown;charset=utf-8' }))
    const link = document.createElement('a'); link.href = url; link.download = 'cultureforge-exploration.md'; link.click(); URL.revokeObjectURL(url)
    setToast('Your exploration brief is ready.')
  }
  async function exportPdf() {
    if (!result) return
    try {
      const blob = await downloadReportPdf(result, challenge)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a'); link.href = url; link.download = `cultureforge-${result.projectId}.pdf`; link.click(); URL.revokeObjectURL(url)
      setToast('The PDF report is ready.')
    } catch (error) {
      setToast(error instanceof Error ? error.message : 'The PDF could not be built.')
    }
  }
  return <div className="studio-shell">
    {menuOpen && <button className="sidebar-backdrop" aria-label="Close navigation" onClick={() => setMenuOpen(false)} />}
    <aside className={`sidebar ${menuOpen ? 'is-open' : ''}`}>
      <button className="brand" onClick={() => navigate('home')} aria-label="CultureForge home"><span className="brand-symbol"><Waves size={21} strokeWidth={2.4}/></span><span>CultureForge<span className="brand-ai">AI</span></span></button>
      <button className="sidebar-close icon-button" aria-label="Close navigation" onClick={() => setMenuOpen(false)}><X size={19}/></button>
      <div className="workspace-switch"><span className="workspace-icon">CF</span><span><strong>Strategy workspace</strong><small>Concepts, taking shape</small></span><ChevronRight size={14}/></div>
      <p className="nav-label">WORKSPACE</p>
      <nav aria-label="Main navigation">
        <NavItem icon={<LayoutGrid size={17}/>} label="Overview" active={screen === 'home'} onClick={() => navigate('home')}/>
        <NavItem icon={<Sparkles size={17}/>} label="New exploration" active={screen === 'create' || screen === 'progress'} onClick={() => navigate('create')}/>
        <NavItem icon={<Layers3 size={17}/>} label="Concept studio" active={screen === 'results' && !savedOnly} onClick={() => { setSavedOnly(false); navigate('results') }} suffix={String(result?.concepts.length ?? 0).padStart(2,'0')}/>
        <NavItem icon={<FlaskConical size={17}/>} label="Scenario lab" active={screen === 'compare'} onClick={() => navigate('compare')}/>
      </nav>
      <div className="nav-rule"/><p className="nav-label">YOUR COLLECTION</p>
      <NavItem icon={<Bookmark size={17}/>} label="Saved concepts" active={screen === 'results' && savedOnly} onClick={() => { setSavedOnly(true); navigate('results') }} suffix={String(savedHere.length).padStart(2, '0')}/>
      <button className="mini-project" onClick={() => navigate('results')}><span className="project-color"/><span>{result ? `${result.project.location.split(',')[0]}, reimagined` : 'Your next exploration'}<small>{result ? `${result.project.businessType} · Exploration` : 'Nothing explored yet'}</small></span><ArrowUpRight size={13}/></button>
      <div className="sidebar-bottom"><div className="demo-promo"><span className="small-cap"><span className="orange-dot"/> THE CULTUREFORGE EXPERIENCE</span><h3>One idea.<br/>A world of possibilities.</h3><button onClick={() => create(initial)}>Run the example brief <Play size={13} fill="currentColor"/></button><span className="demo-promo-art"><Waves size={67} strokeWidth={1}/></span></div>
      <div className="sidebar-foot"><div className="founder-avatar">V</div><span><strong>Vincent’s workspace</strong><small>Qloo Agentic Hackathon</small></span><span className="workspace-indicator"/></div></div>
    </aside>
    <main className="main-area"><header className="topbar"><div className="topbar-left"><button className="studio-return" onClick={goToLanding}><ArrowLeft size={14}/> Landing</button><button className="mobile-menu icon-button" aria-label="Open navigation" onClick={() => setMenuOpen(true)}><Menu size={20}/></button><span className="topbar-workspace">Workspace</span><ChevronRight size={12}/><span>{titles[screen]}</span></div><div className="topbar-right"><button className="tour-launch" onClick={() => setTourOpen(true)}><CircleHelp size={16}/><span>Guided tour</span></button><span className="prototype-badge" title={backend?.reason ?? undefined}><span/> {backend === null ? 'Checking the backend…' : backend.mode === 'offline' ? 'Backend unreachable' : backend.ready ? 'Qloo configured' : 'No Qloo key — backend is not live'}</span><span className="topbar-separator"/><a className="topbar-link" href="/">Front page <ArrowUpRight size={13}/></a><button className="theme-toggle" aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`} title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`} onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>{theme === 'dark' ? <Sun size={17}/> : <Moon size={17}/>}<span>{theme === 'dark' ? 'Light' : 'Dark'} mode</span></button><button className="top-new icon-button" aria-label="Create a new exploration" onClick={() => navigate('create')}><Plus size={18}/></button></div></header>
      <div className="page-content" key={screen}>
        {screen === 'home' && <div className="tour-welcome"><div><strong>First time here?</strong><span>Follow the brief → evidence → challenge → experiment journey.</span></div><button className="text-link" onClick={() => setTourOpen(true)}>Take the guided tour <ArrowRight size={15}/></button></div>}
        {screen === 'home' && <Home start={() => navigate('create')} demo={() => create(initial)} explore={() => navigate('results')} openExploration={async (id) => { try { const record = await fetchExploration(id); const saved = (record as { challenge?: ChallengeResult }).challenge; setResult(record.result); setSelected(record.result.concepts[0]?.id ?? ''); if (saved) { setChallenge(saved); setChallengeSavedAt(new Date().toLocaleString()) } navigate('results'); setToast(saved ? 'Reopened from your saved explorations, with its evidence test.' : 'Reopened from your saved explorations.') } catch (error) { setToast(error instanceof Error ? error.message : 'That exploration could not be opened.') } }}/>}
        {screen === 'create' && (seedCandidates
          ? <TasteSeeds candidates={seedCandidates} audience={form.audience} busy={seedBusy}
              selected={seedSelection ?? seedCandidates.map((candidate) => candidate.tagId)}
              onChange={setSeedSelection}
              onConfirm={confirmSeeds} onCancel={() => setSeedCandidates(null)}/>
          : <Create form={form} setForm={setForm} submit={() => beginResearch()} runExample={(project) => create(project)} error={providerError} back={() => navigate('home')}/>)}
        {screen === 'create' && clarification && <div className="clarification" role="alert"><strong>{clarification.question}</strong><p>{clarification.reason}</p>{clarification.suggestion && <button className="clarification-suggestion" onClick={()=>{ setForm({...form, location: clarification.suggestion as string}); setClarification(null); beginResearch({...form, location: clarification.suggestion as string}) }}>Use {clarification.suggestion} instead</button>}</div>}
        {screen === 'progress' && (researchRunId
          ? <Progress project={form} runId={researchRunId} onComplete={onRunComplete} onClarify={onRunClarify} onGiveUp={() => { setResearchRunId(null); setScreen('create') }}/>
          : <Progress project={form}/>)}
        {screen === 'results' && (result
          ? <Results result={result} selected={selected} select={setSelected} saved={saved} save={save} savedOnly={savedOnly} setSavedOnly={setSavedOnly} open={setModal} compare={() => navigate('compare')} exportBrief={exportBrief} onInspect={setProvenanceId} onShare={shareThisExploration} shareUrl={shareUrl} onNotebook={() => setNotebookOpen(true)} onInvestigate={setInvestigating} onEvidenceDependence={() => setDependenceOpen(true)} challenge={challenge} challenging={challenging} challengeError={challengeError} onChallenge={() => testDirections()} onReanchor={(directionId, anchorEntityId) => testDirections(directionId, anchorEntityId)} onCloseChallenge={() => setChallenge(null)} usage={usage} onNewBrief={() => navigate('create')} challengeHistory={challengeHistory} challengeSavedAt={challengeSavedAt} analysis={analysis} analysisBusy={analysisBusy} analysisError={analysisError} onAnalyze={analyzeCurrentEvidence} dependenceSummary={dependenceSummary} onExportPdf={exportPdf} profileControl={<ProfileChooser proposal={profileProposal} chosen={profileChoice} onChoose={setProfileChoice}/>}/>
          : <NoExploration start={() => navigate('create')}/>)}
        {result && investigating && (() => { const concept = result.concepts.find((c) => c.id === investigating); if (!concept) return null; const testedAnchor = challenge?.directions.find((entry) => entry.directionId === concept.id)?.anchor?.label ?? null; return <Investigation concept={concept} project={result.project} evidence={result.evidence} testedAnchorLabel={testedAnchor} onClose={() => setInvestigating(null)}/> })()}
        {result && <ProvenanceDrawer evidence={result.evidence} concepts={result.concepts} trace={result.trace} evidenceId={provenanceId} project={result.project} selection={presentation} onClose={() => setProvenanceId(null)} onRecomposed={(next)=>{ setResult({...result, concepts:next.concepts, evidence:next.evidence}); setSelected(next.concepts[0]?.id ?? ''); setToast(next.concepts.length ? 'Rebuilt without that venue. Qloo was not called again, and no model was asked to name anything.' : 'No direction remains supported after removing that venue.') }}/>}
        {screen === 'compare' && result && <Compare result={result} back={() => navigate('results')} apply={applyScenario} busy={scenarioBusy}/> }
      </div><footer className="page-footer"><span><Waves size={13}/> CultureForge AI <i/> Built for the culturally curious.</span><span>Human ambition. Cultural intelligence.</span></footer>
    </main>
    {notebookOpen && result && result.concepts.length > 0 && <DecisionNotebook key={notebookKey(result, result.concepts.find((c) => c.id === selected) ?? result.concepts[0])} result={result} concept={result.concepts.find((c) => c.id === selected) ?? result.concepts[0]} challenge={challenge} onClose={() => setNotebookOpen(false)}/>}
    {tourOpen && <GuidedTour screen={screen} hasEvidence={Boolean(result?.evidence.length && result?.concepts.length)} onNavigate={navigate} onClose={closeTour} onInspect={() => setProvenanceId(result?.evidence.find((e) => e.kind === 'entity')?.id ?? result?.evidence[0]?.id ?? null)} onRemoval={() => setDependenceOpen(true)} onNotebook={() => setNotebookOpen(true)}/>}
    {dependenceOpen && result && <EvidenceDependenceMap baseline={result} onSummary={(summary) => { if (currentResult.current === result) setDependenceSummary(summary) }} onClose={() => setDependenceOpen(false)} onUseRebuild={(next, venueLabel) => { setResult((current) => current ? { ...current, concepts: next.concepts, evidence: next.evidence } : current); setSelected(next.concepts[0]?.id ?? ''); setChallenge(null); setChallengeError(''); setToast(`Applied the recomposition with ${venueLabel} removed. It uses held evidence and was not re-tested.`) }} onRestoreBaseline={(original) => { setResult(original); setSelected(original.concepts[0]?.id ?? ''); setChallenge(null); setChallengeError(''); setToast('Restored the original answer.') }}/ >}
    {modal && <ConceptModal concept={modal} saved={saved.includes(modal.id)} save={() => save(modal.id)} close={() => setModal(null)}/ >}
    {toast && <div className="toast" role="status"><CheckCheck size={17}/>{toast}</div>}
  </div>
}
function NavItem({ icon, label, active, onClick, suffix }: { icon: ReactNode; label: string; active: boolean; onClick: () => void; suffix?: string }) {
  return <button className={`nav-item ${active ? 'active' : ''}`} onClick={onClick} aria-current={active ? 'page' : undefined}>{icon}<span>{label}</span>{suffix && <small>{suffix}</small>}</button>
}
function BusinessIcon({type,size=14}:{type:ProjectRequest['businessType'];size?:number}) { const Icon = {'Food & beverage':Coffee,Retail:Layers3,Hospitality:Globe2,Wellness:Leaf,Entertainment:AudioLines}[type]; return <Icon size={size}/> }
function Eyebrow({ children }: { children: ReactNode }) { return <div className="eyebrow"><span/>{children}</div> }
function Button({ children, onClick, variant = 'primary', type = 'button', disabled = false, 'data-tour': tourTarget }: { 'data-tour'?: string; children: ReactNode; onClick?: () => void; variant?: 'primary' | 'secondary' | 'text'; type?: 'button' | 'submit'; disabled?: boolean }) { return <button data-tour={tourTarget} type={type} className={`button button-${variant}`} onClick={onClick} disabled={disabled}>{children}</button> }

function Home({ start, demo, explore, openExploration }: { start: () => void; demo: () => void; explore: () => void; openExploration: (id: string) => void }) {
  return <div className="home-page studio-home" data-tour="overview">
    <div className="welcome-row"><span>THE CULTURAL HYPOTHESIS STUDIO</span><span className="edition-tag">EVIDENCE · INTERPRETATION · CHALLENGE</span></div>
    <section className="hero studio-hero">
      <div className="hero-copy">
        <Eyebrow>DON’T JUST COLLECT SIGNALS</Eyebrow>
        <h1>Make an idea<br/>answer to its <em>evidence.</em></h1>
        <p>CultureForge turns cultural context into a local venture hypothesis, then gives you ways to challenge the place and assumptions behind it.</p>
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

function SavedExplorations({ onOpen }: { onOpen: (id: string) => void }) {
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
      <div><Eyebrow>YOUR SAVED EXPLORATIONS</Eyebrow><h2>Still here,<br/><em>even after a restart.</em></h2></div>
      <span className="sample-label">SAVED TO THIS WORKSPACE</span>
    </div>
    <ul className="saved-exploration-list">
      {items.slice(0, 6).map((item) => <li key={item.id}>
        <button onClick={() => onOpen(item.id)}>
          <span className="saved-exploration-title">{item.title}</span>
          <span className="saved-exploration-meta">
            {String((item.brief as { location?: string })?.location ?? 'exploration')} · {item.versions.length} version{item.versions.length === 1 ? '' : 's'}
          </span>
          <ArrowUpRight size={16}/>
        </button>
      </li>)}
    </ul>
  </section>
}

function Create({ form, setForm, submit, runExample, error, back }: { form: ProjectRequest; setForm: (project: ProjectRequest) => void; submit: () => void; runExample: (project: ProjectRequest) => void; error: string; back: () => void }) {
  const [custom, setCustom] = useState('')
  const types = [{label:'Food & beverage',icon:Coffee},{label:'Retail',icon:Layers3},{label:'Hospitality',icon:Globe2},{label:'Wellness',icon:Leaf},{label:'Entertainment',icon:AudioLines}] as const
  const allGoals = [...new Set([...objectives, ...form.objectives])]
  function toggle(goal: string) { setForm({...form, objectives: form.objectives.includes(goal) ? form.objectives.filter(value => value !== goal) : [...form.objectives, goal]}) }
  const add = () => { const value=custom.trim(); if(value && !form.objectives.includes(value)) toggle(value); setCustom('') }
  return <div className="create-page" data-tour="brief"><button className="back-link" onClick={back}><ArrowLeft size={14}/> Back to overview</button><div className="page-heading"><div><Eyebrow>THE BEGINNING OF SOMETHING GOOD</Eyebrow><h1>Tell us what you’re<br/><em>dreaming of.</em></h1><p>You bring the ambition. We’ll find the cultural connections.</p></div><span className="page-index">EXPLORATION / 001</span></div><div className="create-layout"><form className="creation-form panel" onSubmit={event => { event.preventDefault(); submit() }}>{error && <div className="api-error" role="alert">{error}</div>}<div className="form-section"><div className="form-section-title"><span>01</span><div><h3>What are you building?</h3><p>Choose the world your idea belongs in.</p></div></div><div className="business-types">{types.map(({label,icon:Icon})=><button type="button" className={form.businessType===label?'business-tile selected':'business-tile'} aria-pressed={form.businessType===label} key={label} onClick={()=>setForm({...form,businessType:label})}><Icon size={20}/><span>{label}</span>{form.businessType===label&&<Check size={12}/>}</button>)}</div></div><div className="form-section"><div className="form-section-title"><span>02</span><div><h3>Who do you want to move?</h3><p>Describe the people at the heart of your idea.</p></div></div><label className="field"><span>Target audience</span><div className="input-with-icon"><Users size={16}/><input required minLength={2} maxLength={240} value={form.audience} onChange={event=>setForm({...form,audience:event.target.value})}/></div></label><div className="preset-row"><span>TRY</span>{audiencePresets.slice(0,3).map(preset=><button type="button" key={preset} onClick={()=>setForm({...form,audience:preset})}>{preset}<Plus size={10}/></button>)}</div><div className="field-grid"><label className="field"><span>Location</span><div className="input-with-icon"><MapPin size={16}/><input required minLength={2} maxLength={160} value={form.location} onChange={event=>setForm({...form,location:event.target.value})}/></div></label><label className="field"><span>Starting budget</span><select value={form.budget} onChange={event=>setForm({...form,budget:event.target.value})}>{['Under $25k','$25k – $50k','$50k – $100k','$100k+','Still figuring it out'].map(budget=><option key={budget}>{budget}</option>)}</select></label></div></div><div className="form-section"><div className="form-section-title"><span>03</span><div><h3>What would success feel like?</h3><p>Select the things that matter to you.</p></div></div><div className="goal-grid">{allGoals.map(goal=><button type="button" className={`goal-chip ${form.objectives.includes(goal)?'selected':''}`} aria-pressed={form.objectives.includes(goal)} key={goal} onClick={()=>toggle(goal)}><span>{form.objectives.includes(goal)?<Check size={12}/>:<Plus size={12}/>}</span>{goal}</button>)}</div><div className="custom-goal"><input aria-label="Custom objective" placeholder="Something else on your mind?" value={custom} onChange={event=>setCustom(event.target.value)} onKeyDown={event=>{if(event.key==='Enter'){event.preventDefault();add()}}}/><button type="button" onClick={add} disabled={!custom.trim()} aria-label="Add custom objective"><Plus size={15}/></button></div></div><div className="form-submit-row"><span><ShieldCheck size={14}/> Your vision stays yours.</span><Button type="submit">Find my cultural edge <ArrowUpRight size={17}/></Button></div></form><aside className="creation-aside"><ExamplePicker onRun={runExample}/><div className="brief-preview panel"><span className="small-cap"><span className="orange-dot"/> YOUR EXPLORATION, AT A GLANCE</span><div className="brief-art"><Fingerprint size={52} strokeWidth={1}/><span/><span/></div><h3>A little context.<br/><em>A lot of possibility.</em></h3><dl><div><dt>Business</dt><dd>{form.businessType}</dd></div><div><dt>Location</dt><dd>{form.location || 'Your neighborhood'}</dd></div><div><dt>Budget</dt><dd>{form.budget}</dd></div></dl><div className="brief-deliverables"><span><Check size={13}/> 3 original concept directions</span><span><Check size={13}/> Cultural signals & evidence</span><span><Check size={13}/> Audience scenario comparison</span></div></div><div className="curiosity-note"><Lightbulb size={18}/><p><strong>Get specific. Stay curious.</strong>The most interesting connections often start with the smallest details.</p></div></aside></div></div>
}
function Progress({project,runId,onComplete,onClarify,onGiveUp}:{project:ProjectRequest;runId?:string;onComplete?:(result:GenerateResponse)=>void;onClarify?:(ask:{reason:string;question:string;field:string})=>void;onGiveUp?:()=>void}) {
  // The steps are lit by the agent's real events, not by a timer. A run that
  // takes twenty-five seconds must not show every step as complete.
  const [stage,setStage]=useState(0)
  useEffect(()=>{
    if (runId) return
    const timers=[window.setTimeout(()=>setStage(1),850),window.setTimeout(()=>setStage(2),1800),window.setTimeout(()=>setStage(3),2850)]
    return()=>timers.forEach(clearTimeout)
  },[runId])
  const steps=[{icon:Search,title:'Understand the audience',detail:'Resolving interests, place, and cultural context.'},{icon:Fingerprint,title:'Connect the cultural dots',detail:'Finding meaningful affinities across culture.'},{icon:WandSparkles,title:'Shape three possibilities',detail:'Bringing the connections into concept directions.'}]
  return <div className="progress-page"><span className="small-cap"><span className="orange-dot pulse"/> AGENT WORKSPACE</span><div className="agent-orbit"><div className="orbit-outer"/><div className="orbit-middle"/><span className="orbit-icon"><Waves size={35}/></span><span className="satellite sat-one"><Coffee size={17}/></span><span className="satellite sat-two"><AudioLines size={17}/></span><span className="satellite sat-three"><Leaf size={17}/></span></div><h1>Curiosity is<br/><em>connecting the dots.</em></h1><p>Your brief is becoming a world of possibilities.</p><div className="progress-context"><span><BusinessIcon type={project.businessType} size={13}/>{project.businessType}</span><span><MapPin size={13}/>{project.location}</span></div><div className="agent-steps panel" aria-live="polite">{steps.map(({icon:Icon,title,detail},index)=><div className={`agent-step ${stage>index?'complete':stage===index?'working':'pending'}`} key={title}><span className="agent-step-icon">{stage>index?<Check size={17}/>:<Icon size={17}/>}</span><div><strong>{title}</strong><small>{detail}</small></div><span className="step-status">{stage>index?'Complete':stage===index?<><LoaderCircle size={12} className="spin"/> Working</>:'Up next'}</span></div>)}<div className="agent-progress-track"><i style={{width:`${Math.min(100,18+stage*29)}%`}}/></div></div>{runId&&<AgentTrace runId={runId} onComplete={onComplete as (r:GenerateResponse)=>void} onClarify={onClarify as (a:{reason:string;question:string;field:string})=>void} onGiveUp={onGiveUp} onProgress={setStage}/>}<span className="progress-footnote"><ShieldCheck size={13}/> {runId?'A real research run. The trace shows retrieval, composition, and any bounded model steps that actually ran.':'Waiting for the backend. The answer comes back with the Qloo calls that produced it, and what it cost.'}</span></div>
}

/**
 * The empty studio.
 *
 * There is no sample exploration to show here. The studio opens on whatever
 * real answer this browser holds, and when it holds none it says so, and
 * offers the one thing that can change that: a real run.
 */
function NoExploration({ start }: { start: () => void }) {
  return <div className="results-page"><div className="empty-state panel"><Search size={30}/><h3>No exploration yet.</h3><p>Every direction in this studio is composed from Qloo evidence, so there is nothing to show until one has been researched. Give it a brief and the real research runs — you can watch every Qloo call it makes.</p><Button onClick={start}>Start an exploration <ArrowRight size={15}/></Button></div></div>
}

function DecisionComparison({result,analysis,challenge,dependence,onChallenge,onDependence}:{result:GenerateResponse;analysis:EvidenceAnalysisResult|null;challenge:ChallengeResult|null|undefined;dependence:DependenceSummary|null;onChallenge?:()=>void;onDependence?:()=>void}) {
  const counts = (id:string) => {
    const concept = result.concepts.find((item) => item.id === id)
    return concept ? citationCoverage(concept, result.evidence) : undefined
  }
  const verdict = (id:string) => challenge?.directions.find((item)=>item.directionId===id)
  const recipe = (concept:Concept) => [...new Set(concept.decisions.map((item)=>item.ruleId).filter(Boolean))].sort().join('|') || concept.id
  return <section className="decision-comparison panel" aria-label="Comparative decision intelligence"><header><span className="small-cap">COMPARATIVE DECISION INTELLIGENCE</span><h2>Which direction is most defensible?</h2><p>Evidence strength inside this retrieved sample. This does not estimate demand, revenue, or business success.</p></header><div className="decision-grid"><div className="decision-dimension"><strong>Evidence coverage</strong><small>Citation attachment only; not factual correctness</small>{result.concepts.map((concept)=>{const c=counts(concept.id);return <p key={concept.id}><b>{concept.name}</b><span>{c?`${c.numerator} / ${c.denominator} decisions · ${c.decisionEvidenceIds.length} source IDs`:'No composer decisions attached'}</span></p>})}</div><div className="decision-dimension"><strong>Evidence dependence</strong><small>One returned venue removed at a time; held evidence only</small>{result.concepts.map((concept)=>{const c=dependence?.[recipe(concept)];return <p key={concept.id}><b>{concept.name}</b><span>{c?`${c.unchanged} unchanged · ${c.sources} source changes · ${c.changed} answer changes · ${c.disappeared} disappeared · ${c.unknown} unevaluated`:'Not tested'}</span></p>})}<button className="text-action" onClick={onDependence}>Run removal test</button></div><div className="decision-dimension"><strong>Contradictions</strong><small>Qloo checks against this sample; missing data is not negative affinity</small>{result.concepts.map((concept)=>{const v=verdict(concept.id);const failed=v?.checks.filter((check)=>check.result==='fail').length??0;const mixed=v?.checks.filter((check)=>check.result==='mixed').length??0;return <p key={concept.id}><b>{concept.name}</b><span>{v?`${v.verdict.toUpperCase()} · ${failed} checks failed · ${mixed} mixed`:'Not tested'}</span></p>})}<button className="text-action" onClick={onChallenge}>Test directions</button></div><div className="decision-dimension"><strong>Sensitivity</strong><small>Explicitly changed assumptions</small>{result.concepts.map((concept)=>{const steps=challenge?.directions.find((v)=>v.directionId===concept.id);return <p key={concept.id}><b>{concept.name}</b><span>{steps?.isCounterfactual?`Alternative anchor: ${steps.anchor?.label??'unnamed'}; original: ${steps.originalAnchor?.label??'unnamed'}; concept not recomposed`:challenge?'No alternative-anchor result in this challenge':'Audience, location, and anchor changes not tested'}</span></p>})}<button className="text-action" onClick={onChallenge}>Test an anchor</button></div></div>{analysis&&<footer><b>Model recommendation</b><p>{analysis.recommendedDirectionId?result.concepts.find((c)=>c.id===analysis.recommendedDirectionId)?.name??'No matching direction':'No single direction'} — {analysis.recommendationRationale}</p><small>Interpretation only: {analysis.whatWouldChangeTheConclusion}</small></footer>}</section>
}

function Results({result,selected,select,saved,save,savedOnly,setSavedOnly,open,compare,exportBrief,onInspect,onShare,shareUrl,onNotebook,onInvestigate,onEvidenceDependence,challenge,challenging,challengeError,onChallenge,onCloseChallenge,onReanchor,usage,onNewBrief,challengeHistory,challengeSavedAt,analysis,analysisBusy,analysisError,onAnalyze,dependenceSummary,profileControl,onExportPdf}:{result:GenerateResponse;selected:string;select:(id:string)=>void;saved:string[];save:(id:string)=>void;savedOnly:boolean;setSavedOnly:(value:boolean)=>void;open:(concept:Concept)=>void;compare:()=>void;exportBrief:()=>void;onInspect?:(evidenceId:string)=>void;onShare?:()=>void;shareUrl?:string;onNotebook:()=>void;onInvestigate?:(conceptId:string)=>void;onEvidenceDependence?:()=>void;challenge?:ChallengeResult|null;challenging?:boolean;challengeError?:string;onChallenge?:()=>void;onCloseChallenge?:()=>void;onReanchor?:(directionId:string,anchorEntityId:string)=>void;usage?:{requests:number;upstreamCalls:number}|null;onNewBrief?:()=>void;challengeHistory?:Record<string,VerdictStep[]>;challengeSavedAt?:string|null;analysis:EvidenceAnalysisResult|null;analysisBusy:boolean;analysisError:string;onAnalyze:()=>void;dependenceSummary:DependenceSummary|null;profileControl?:ReactNode;onExportPdf?:()=>void}) {
  const [view,setView]=useState<'cards'|'matrix'>('cards')
  const [insightTab,setInsightTab]=useState<'signals'|'bridge'|'map'|'constellation'|'heat'|'anchors'|'blueprint'|'source'>('signals')
  const [whyOpen,setWhyOpen]=useState<string|null>(null)
  const chosen=result.concepts.find(concept=>concept.id===selected)??result.concepts[0]
  const noDirections=result.concepts.length===0
  // Once the directions have been tested, the order is the one the evidence
  // leaves them in — not the one the first pass produced.
  const verdictFor=(id:string)=>challenge?.directions.find(entry=>entry.directionId===id)
  const matrixSources=(concept:Concept)=>concept.evidenceIds.map(id=>result.evidence.find(item=>item.id===id)?.label).filter(Boolean).join(', ')||'No cited source'
  const matrixVerdict=(concept:Concept)=>verdictFor(concept.id)
  const ordered=challenge
    ? [...result.concepts].sort((a,b)=>(challenge.order.indexOf(a.id)===-1?99:challenge.order.indexOf(a.id))-(challenge.order.indexOf(b.id)===-1?99:challenge.order.indexOf(b.id)))
    : result.concepts
  const filtered=savedOnly?ordered.filter(concept=>saved.includes(concept.id)):ordered
  const hasScores=result.concepts.length>0&&result.concepts.every(concept=>typeof concept.audienceFit==='number')
  const livePlaces=result.evidence.filter(item=>item.kind==='entity').length
  // The cultural signals are the audience seeds Qloo resolved, not the
  // places it returned. The places have their own strip, with their own
  // photographs and measurements.
  const seeds=result.evidence.filter(item=>item.kind==='tag')
  // The photograph on a card is a real Qloo place photo. Say whose it is,
  // rather than letting an uncredited picture stand in for evidence.
  const creditFor=(concept:Concept)=>{
    const place=result.evidence.find(item=>item.kind==='entity'&&item.image&&item.image===concept.image)
    return place?`QLOO PHOTOGRAPH · ${place.label.toUpperCase()}`:(concept.personality?.toUpperCase()??'CONCEPT DIRECTION')
  }
  return <div className="results-page"><div className="results-masthead results-title-row"><div><Eyebrow>YOUR AMBITION, SEEN THROUGH CULTURE</Eyebrow><h1>{result.concepts.length} directions.<br/><em>Assumptions to test.</em></h1><p>Different expressions of the same vision. Find the one that feels like you.</p></div><div className="heading-actions"><Button data-tour="pilot" variant="secondary" onClick={onNotebook} disabled={!result.concepts.length}><Bookmark size={15}/> Decision notebook</Button><Button variant="secondary" onClick={exportBrief}><ArrowDownToLine size={15}/> Export brief</Button>{onExportPdf&&<Button variant="secondary" onClick={onExportPdf}><ArrowDownToLine size={15}/> PDF report</Button>}{onShare&&<Button variant="secondary" onClick={onShare}><Share2 size={15}/> Share</Button>}<Button variant="secondary" onClick={()=>onInvestigate?.(selected)}><FlaskConical size={15}/> Investigate</Button><Button data-tour="challenge" variant="secondary" onClick={onChallenge} disabled={challenging}>{challenging?<><LoaderCircle size={15} className="spin"/> Testing…</>:<><ShieldCheck size={15}/> Test the evidence</>}</Button>{result.dataMode==='live'&&result.conceptMode==='evidence_composed'&&<Button data-tour="removal" variant="secondary" onClick={onEvidenceDependence}><Fingerprint size={15}/> Trace evidence dependence</Button>}<Button onClick={compare}>Compare audiences <ArrowUpRight size={16}/></Button></div></div><div className="exploration-context"><span><BusinessIcon type={result.project.businessType}/>{result.project.businessType}</span><span><MapPin size={14}/>{result.project.location}</span><span><Users size={14}/>{result.project.audience}</span><span className="context-budget">{result.project.budget}</span></div>
    {shareUrl && <div className="share-record panel" role="status"><strong>Frozen exploration link</strong><p>Includes the evidence and verdict recorded when you shared it.</p><a href={shareUrl} target="_blank" rel="noreferrer">{shareUrl}</a></div>}
    <div className="evidence-summary"><ShieldCheck size={18}/><div><strong>{result.conceptMode==='evidence_composed'?'Directions composed from live Qloo evidence':'Directions from an earlier session'}</strong><p className="brief-notice">{result.notice}</p><ResearchTrace trace={result.trace} delivery={result.delivery}/>{usage && <p className="usage-line">This answer cost {result.delivery?.transportRequests ?? 0} upstream Qloo requests.</p>}</div></div>{result.dataMode==='live'&&result.conceptMode==='evidence_composed'&&profileControl}{challengeError&&<div className="api-error" role="alert">{challengeError}</div>}{challenge&&<ChallengePanel challenge={challenge} onClose={()=>onCloseChallenge?.()} onReanchor={onReanchor} history={challengeHistory} savedAt={challengeSavedAt}/>}<div className="results-summary"><div><span className="metric-icon"><Layers3 size={19}/></span><span><strong>{String(result.concepts.length).padStart(2,'0')}</strong><small>Distinct concept directions</small></span></div><div><span className="metric-icon"><Target size={19}/></span><span><strong>{hasScores?<>{Math.max(...result.concepts.map(concept=>concept.audienceFit as number))}<em>/100</em></>:<>{String(livePlaces).padStart(2,'0')}</>}</strong><small>{hasScores?'Highest fit score':'Live Qloo places'}</small></span></div><div><span className="metric-icon"><Fingerprint size={19}/></span><span><strong>{String(result.evidence.filter((item) => item.kind === 'entity').length).padStart(2,'0')}</strong><small>Places Qloo returned</small></span></div><div><span className="metric-icon"><Bookmark size={19}/></span><span><strong>{String(result.concepts.filter(concept=>saved.includes(concept.id)).length).padStart(2,'0')}</strong><small>Ideas in your collection</small></span></div></div><PlaceStrip evidence={result.evidence} onInspect={(id)=>onInspect?.(id)}/>
    <div className="concept-toolbar"><div className="section-inline-heading"><h2>{savedOnly?'Your collection':'Meet the possibilities'}</h2><span className="count-badge">{filtered.length}</span></div><div className="concept-toolbar-actions"><button className={`filter-button ${savedOnly?'is-active':''}`} aria-pressed={savedOnly} onClick={()=>setSavedOnly(!savedOnly)}><Bookmark size={14}/> Saved</button><div className="view-switch" role="group" aria-label="Concept display"><button aria-label="Card view" aria-pressed={view==='cards'} className={view==='cards'?'active':''} onClick={()=>setView('cards')}><LayoutGrid size={14}/></button><button aria-label="Comparison matrix view" aria-pressed={view==='matrix'} className={view==='matrix'?'active':''} onClick={()=>setView('matrix')}><BarIcon/></button></div></div></div>
    {noDirections?<div className="empty-state panel"><Search size={30}/><h3>No direction remains supported by the evidence.</h3><p>{result.notice} You can revise the audience or location and run a new exploration.</p><Button variant="secondary" onClick={()=>onNewBrief?.()}>Try a different brief <ArrowRight size={15}/></Button></div>:filtered.length===0?<div className="empty-state panel"><Bookmark size={30}/><h3>Good ideas deserve a place.</h3><p>Save a concept in this exploration to start your collection.</p><Button variant="secondary" onClick={()=>setSavedOnly(false)}>Explore the concepts <ArrowRight size={15}/></Button></div>:view==='cards'?<div className="concept-grid">{filtered.map((concept,index)=><article className={`concept-card ${selected===concept.id?'is-selected':''}`} key={concept.id}><div className={`concept-photo photo-${concept.id}${concept.image ? "" : " has-no-image"}`}>{concept.image && <img src={concept.image} alt={concept.imageAlt ?? `Qloo place behind this ${result.project.businessType.toLowerCase()} direction`} loading="lazy" onError={(event) => { event.currentTarget.style.display = 'none'; event.currentTarget.parentElement?.classList.add('has-no-image') }} />}{!concept.image && <span className="concept-photo-fallback" aria-hidden="true">{concept.name.slice(0, 2).toUpperCase()}</span>}<div className="concept-photo-shade"/><span className="concept-id">DIRECTION {String(index+1).padStart(2,'0')}{concept.direction && concept.direction !== String(index+1).padStart(2,'0') ? ` · WAS ${concept.direction}` : ''}</span><button className={`save-button ${saved.includes(concept.id)?'saved':''}`} aria-label={`${saved.includes(concept.id)?'Unsave':'Save'} ${concept.name}`} aria-pressed={saved.includes(concept.id)} onClick={()=>save(concept.id)}><Bookmark size={16} fill={saved.includes(concept.id)?'currentColor':'none'}/></button><span className="concept-photo-bottom"><span>{creditFor(concept)}</span><ArrowUpRight size={19}/></span></div><div className="concept-card-content"><div className="concept-name-row"><h3>{concept.name}</h3>{verdictFor(concept.id)?<VerdictBadge verdict={verdictFor(concept.id)!.verdict}/>:concept.audienceFit!=null?<span className="mini-score">{concept.audienceFit}<small>FIT SCORE</small></span>:<span className="mini-score is-evidence">EVIDENCE<small>BASED</small></span>}</div>{verdictFor(concept.id)?.isCounterfactual&&<p className="concept-counterfactual">Alternative anchor tested: {verdictFor(concept.id)!.anchor?.label}. Original concept reference: {verdictFor(concept.id)!.originalAnchor?.label ?? 'the place it was built around'}. The concept was not recomposed.</p>}<p className="concept-tagline">{concept.tagline}</p><p className="concept-description">{concept.description}</p><div className="taste-tags">{concept.signals.map(signal=><span key={signal}>{signal}</span>)}</div><div className="concept-card-foot"><span><small>{result.conceptMode==='evidence_composed'?`BUILT FROM ${concept.evidenceIds.length} PIECES OF QLOO EVIDENCE`:'ILLUSTRATIVE PILOT'}</small><strong>{concept.investment}</strong></span><button aria-label={`Explore ${concept.name}`} onClick={()=>{select(concept.id);open(concept)}}>Explore concept <ArrowUpRight size={15}/></button></div>{concept.decisions.length>0&&<><button className="why-toggle" onClick={()=>setWhyOpen(whyOpen===concept.id?null:concept.id)} aria-expanded={whyOpen===concept.id}>Why this direction? <ChevronRight size={13} className={whyOpen===concept.id?'is-open':''}/></button>{whyOpen===concept.id&&<EvidencePanel concept={concept} evidence={result.evidence}/>}</>}</div><button className="investigate-button" onClick={()=>onInvestigate?.(concept.id)} aria-label={`Investigate ${concept.name}`}><FlaskConical size={13}/> Investigate this direction</button><button className="select-concept" aria-label={`Select ${concept.name} insights`} aria-pressed={selected===concept.id} onClick={()=>select(concept.id)}>{selected===concept.id?<><Check size={12}/> Currently exploring</>:<>View supporting insights <ArrowRight size={12}/></>}</button></article>)}</div>:<div className="matrix-container panel"><table className="concept-matrix"><caption>Compare each direction by its tested anchor, cited Qloo sources and the strongest remaining unknown.</caption><thead><tr><th>CONCEPT</th><th>ANCHOR TEST</th><th>CITED EVIDENCE</th><th>LIMIT / NEXT UNKNOWN</th><th>INVESTMENT</th><th/></tr></thead><tbody>{filtered.map(concept=><tr key={concept.id}><td><strong>{concept.name}</strong><small>{concept.tagline}</small></td><td>{matrixVerdict(concept)?<><b>{matrixVerdict(concept)!.verdict}</b><small>{matrixVerdict(concept)!.anchor?.label??matrixVerdict(concept)!.scope}</small></>:<b className="is-null">Not tested</b>}</td><td>{matrixSources(concept)}</td><td>{matrixVerdict(concept)?.unprovenIf??concept.limitations[0]??'Test the evidence to reveal what remains unknown.'}</td><td>{concept.investment}</td><td><button className="icon-button" aria-label={`Explore ${concept.name}`} onClick={()=>open(concept)}><ArrowUpRight size={17}/></button></td></tr>)}</tbody></table></div>}
    {result.dataMode==='live'&&result.conceptMode==='evidence_composed'&&selected&&<ReplacementProbe key={JSON.stringify([selected,result.project.location,result.provenance?.resolved_tags??[],result.concepts.find(concept=>concept.id===selected)?.evidenceIds.map(id=>{const item=result.evidence.find(entry=>entry.id===id);return[item?.entityId,item?.label]})])} project={result.project} directionId={selected} concepts={result.concepts} evidence={result.evidence} resolvedTags={result.provenance?.resolved_tags??[]}/>}<AgentOutcome report={result.agent} concepts={result.concepts}/>{result.dataMode==='live'&&result.conceptMode==='evidence_composed'&&result.concepts.length>0&&<EvidenceChat key={result.projectId} result={result}/>}<DecisionComparison result={result} analysis={analysis} challenge={challenge} dependence={dependenceSummary} onChallenge={onChallenge} onDependence={onEvidenceDependence}/><section className="analysis-launch panel"><div><span className="small-cap"><span className="orange-dot"/> COMPARE THE HYPOTHESES</span><h2>What does the evidence defend?</h2><p>One bounded model analysis over this exploration. It costs no Qloo requests; claims cite only the evidence shown here.</p></div><Button variant="secondary" onClick={onAnalyze} disabled={analysisBusy||result.concepts.length===0}>{analysisBusy?<><LoaderCircle size={15} className="spin"/> Analyzing…</>:analysis?<>Analyze again <ArrowUpRight size={15}/></>:<>Analyze this evidence <ArrowUpRight size={15}/></>}</Button></section>{analysisError&&<div className="api-error" role="alert">{analysisError}</div>}{analysis&&<EvidenceAnalysisPanel analysis={analysis} concepts={result.concepts} evidence={result.evidence} onInspect={onInspect}/>}
    <div className={`insight-workspace${insightTab==='constellation'||insightTab==='heat'||insightTab==='anchors'||insightTab==='map'?' is-wide':''}`}><div className="insight-main panel"><div className="insight-header"><span className="small-cap"><span className="orange-dot"/> BEHIND THE IDEA</span><span className="sample-label">{result.dataMode==='live'?'AUDIENCE SEEDS QLOO RETURNED':'CULTURAL SIGNALS'}</span></div><div className="insight-title"><h2>Every good idea<br/>has <em>interesting roots.</em></h2><span className="circle-arrow"><Fingerprint size={28} strokeWidth={1}/></span></div><div className="insight-tabs" role="tablist" aria-label="Concept insights">{([{id:'signals',label:'Cultural signals'},{id:'bridge',label:'Beyond places'},{id:'map',label:'Interest map'},{id:'constellation',label:'Constellation'},{id:'heat',label:'Cultural heat'},{id:'anchors',label:'Anchor tournament'},{id:'blueprint',label:'Blueprint'},{id:'source',label:'Evidence & source'}] as const).map(tab=><button key={tab.id} role="tab" aria-selected={insightTab===tab.id} className={insightTab===tab.id?'active':''} disabled={tab.id==='blueprint'&&!chosen} onClick={()=>setInsightTab(tab.id)}>{tab.label}</button>)}</div><div className="insight-tab-content" role="tabpanel">{insightTab==='signals'?<>{seeds.length?seeds.map((seed,index)=><SeedRow seed={seed} index={index} key={seed.id}/>):<p className="source-panel-note">The audience did not resolve into cultural seeds for this brief, so there is nothing here to show.</p>}</>:insightTab==='map'?<InterestMap evidence={result.evidence} concepts={result.concepts} selectedId={selected} location={result.project.location}/>:insightTab==='bridge'?<AudienceBridge evidence={result.evidence} trace={result.trace} onInspect={(id)=>onInspect?.(id)}/>:insightTab==='constellation'?<CulturalConstellation evidence={result.evidence} concepts={result.concepts} selectedId={selected} onSelect={select} onInspect={(id)=>onInspect?.(id)}/>:insightTab==='heat'?<CulturalHeat evidence={result.evidence} onInspect={(id)=>onInspect?.(id)}/>:insightTab==='anchors'?<AnchorTournament evidence={result.evidence} audience={result.project.audience} location={result.project.location}/>:insightTab==='blueprint'?(chosen?<div className="blueprint-preview"><span className="tiny-cap">{chosen.name.toUpperCase()} · EXPERIENCE BLUEPRINT</span><h3>{chosen.tagline}</h3><p>{chosen.description}</p><div className="blueprint-points">{chosen.moments?.map(moment=><span key={moment.title}><Lightbulb size={16}/>{moment.title}</span>)}</div><button className="text-link" onClick={()=>open(chosen)}>Open the full concept <ArrowUpRight size={14}/></button></div>:<p className="source-panel-note">A blueprint appears when a direction is supported by the evidence.</p>):<div className="source-panel"><ShieldCheck size={25}/><h3>Clear about what’s behind the idea.</h3><p>{result.notice}</p><p>The cultural evidence — the venues, the signals, the affinities — is Qloo’s. The business directions, the budget bands and the implementation notes are CultureForge’s reading of that evidence.</p><a href={result.provenance?.documentation??'https://github.com/qloo/qloo-hackathon-kit'} target="_blank" rel="noreferrer">Explore the Qloo Hackathon Kit <ArrowUpRight size={13}/></a></div>}</div></div><aside className="decision-card"><span className="small-cap">A DIFFERENT AUDIENCE.<br/>A DIFFERENT POSSIBILITY.</span><div className="decision-art"><Users size={32} strokeWidth={1}/><span/><span/></div><h3>What if you<br/><em>changed the lens?</em></h3><p>See how a new audience could reshape the opportunity.</p><Button variant="secondary" onClick={compare}>Open scenario lab <ArrowUpRight size={16}/></Button><span className="decision-foot">SMALL SHIFTS. INTERESTING CONSEQUENCES.</span></aside></div><div className="evidence-footnote"><ShieldCheck size={14}/><p>Live Qloo aggregate signals are connected. Fit scores are not shown for these directions, because affinity does not measure business fit; the budget band is a CultureForge planning assumption, and launch costs have not been estimated.</p><span>CURIOSITY, WITH CONTEXT.</span></div>
  </div>
}
function BarIcon(){return <svg width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden="true"><path d="M2 3h11M2 7.5h11M2 12h11" stroke="currentColor" strokeWidth="1.5"/></svg>}
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
              <b>{evidenceKindLabel(item).toUpperCase()}</b>
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
  const label=kind==='cache'?(delivery?.cachedIn==='browser'?'Held in this browser':'Cached Qloo evidence'):kind==='fresh'?'Fresh Qloo evidence':kind==='snapshot'?'Saved Qloo snapshot':'Qloo evidence'
  const stamp=delivery?.acquiredAt?new Date(delivery.acquiredAt).toLocaleTimeString():null
  const spent=delivery?.transportRequests
  return <details className="research-trace">
    <summary><span className={`trace-badge is-${kind??'fresh'}`}>{label}</span>How this was researched{stamp&&<em>acquired {stamp}</em>}{spent===0&&<em className="trace-free">0 upstream requests</em>}</summary>
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


/**
 * One audience seed, exactly as Qloo returned it.
 *
 * The seed is shown by its own URN and its own popularity. It is not a
 * cultural signal the app inferred, and it is not a place.
 */
function SeedRow({seed,index}:{seed:Evidence;index:number}){return <div className="evidence-row"><span className="evidence-index">0{index+1}</span><div><strong>{seed.label}</strong><p>{seed.tagId}</p></div><span className="evidence-value">{seed.popularity!=null?<>{seed.popularity.toFixed(3)}<small>QLOO POPULARITY</small></>:<ArrowUpRight size={17}/>}</span></div>}

function Compare({result,back,apply,busy}:{result:GenerateResponse;back:()=>void;apply:(audience:string, alternative?: never, location?: string)=>void;busy?:boolean}) {
  const startingProfile=result.project.audience==='Independent creatives'?'Mindful professionals':'Independent creatives'
  const [draft,setDraft]=useState(startingProfile)
  const [location,setLocation]=useState(result.project.location)
  const [preset,setPreset]=useState(startingProfile)
  const unchanged=draft.trim()===result.project.audience.trim() && location.trim()===result.project.location.trim()
  function chooseProfile(profile:string){setPreset(profile);setDraft(profile)}
  return <div className="compare-page"><button className="back-link" onClick={back}><ArrowLeft size={14}/> Back to concept studio</button><div className="page-heading"><div><Eyebrow>A NEW LENS ON YOUR NEXT MOVE</Eyebrow><h1>Same vision.<br/><em>New possibilities.</em></h1><p>Change the audience or location, and let Qloo measure what actually changes.</p></div><span className="scenario-pill"><FlaskConical size={14}/> SCENARIO LAB <i/> LIVE QLOO COMPARISON</span></div><div className="scenario-layout"><aside className="scenario-controls panel"><label className="scenario-location">Research location<input value={location} onChange={(event)=>setLocation(event.target.value)} aria-label="Scenario location" placeholder="City, region"/></label><div className="controls-heading"><span className="feature-icon"><SlidersHorizontal size={19}/></span><h3>Shift your perspective.</h3></div><label className="field"><span>New target audience</span><textarea maxLength={240} rows={2} value={draft} onChange={event=>{setDraft(event.target.value);setPreset('')}} placeholder="Describe an audience to explore…"/></label><div className="scenario-presets">{audiencePresets.map(profile=><button className={preset===profile?'selected':''} aria-pressed={preset===profile} key={profile} onClick={()=>chooseProfile(profile)}>{profile}{preset===profile?<Check size={12}/>:<Plus size={12}/>}</button>)}</div><div className="controls-rule"/><span className="small-cap">WHAT QLOO WILL DO</span><ol className="scenario-steps"><li><span>01</span><p><strong>Research the new audience.</strong>Qloo resolves it into cultural signals and returns the venues that carry them.</p></li><li><span>02</span><p><strong>Compare the two groups.</strong>Qloo's own A/B reports the cultural tags the audiences share, and the ones that set them apart.</p></li><li><span>03</span><p><strong>Recompose the directions.</strong>The new evidence becomes the next set of directions. Valid held evidence is reused without another Qloo call.</p></li></ol><div className="sample-model-note"><CircleHelp size={14}/><p>Qloo supplies the venue comparison. CultureForge composes the proposed directions using rules.</p></div></aside><div className="scenario-output"><div className="scenario-audience-cards"><div><span className="small-cap">ORIGINAL AUDIENCE</span><h3>{result.project.audience}</h3><span><MapPin size={12}/>{result.project.location}</span></div><span className="scenario-flow-arrow"><ArrowRight size={17}/></span><div><span className="small-cap"><span className="orange-dot"/> YOUR NEW SCENARIO</span><h3>{draft||'Your next audience'}</h3><span><MapPin size={12}/>{location.trim()||'Location required'}</span><span>{unchanged?'Same scenario — change the audience or location':'Qloo will research this audience and location against your brief'}</span></div></div>{location.trim()===result.project.location.trim()?<AudienceComparison project={result.project} currentAudience={result.project.audience} alternativeAudience={draft.trim()||result.project.audience} currentEvidence={result.evidence} busy={busy} onApply={(audience)=>apply(audience, undefined, location.trim())}/>:<p className="audience-comparison-note">The current evidence belongs to {result.project.location}. Run the new-location scenario to retrieve a fresh evidence set; the audience-pair comparison will be available from that result.</p>}<div className="scenario-apply"><button className="text-link" onClick={()=>{setDraft(result.project.audience);setLocation(result.project.location);setPreset('')}}>Reset scenario</button><Button disabled={draft.trim().length<2||unchanged} onClick={()=>apply(draft.trim(), undefined, location.trim())}>Re-research this scenario <ArrowUpRight size={16}/></Button>{busy&&<span className="scenario-busy">Re-researching with Qloo… this may resolve audience tags and retrieve places; held evidence is reused.</span>}</div></div></div></div>
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

  return <div className="modal-backdrop" onClick={close}><div className="concept-modal" ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="concept-modal-title" onClick={event=>event.stopPropagation()}><div className={`modal-cover${concept.image ? '' : ' has-no-image'}`} style={concept.image ? { backgroundImage: `linear-gradient(0deg,rgba(0,0,0,.75),rgba(0,0,0,.1)),url(${concept.image})` } : undefined}><button className="modal-close" onClick={close} aria-label="Close concept blueprint"><X size={19}/></button><span className="small-cap">DIRECTION {concept.direction??'01'} / EXPERIENCE BLUEPRINT</span><h2 id="concept-modal-title">{concept.name}</h2><p>{concept.tagline}</p></div><div className="modal-content"><div className="modal-intro"><span className="sample-label">{concept.evidenceIds.length?'COMPOSED FROM QLOO EVIDENCE':'DIRECTION FROM THIS EXPLORATION'}</span><button className={`filter-button ${saved?'is-active':''}`} onClick={save}><Bookmark size={14} fill={saved?'currentColor':'none'}/>{saved?'Saved to collection':'Save concept'}</button></div><h3>The idea, in a little more color.</h3><p className="modal-description">{concept.description}</p><div className="personalization-note"><strong>Why this direction?</strong><p>{concept.audienceRationale}</p><p>{concept.implementationNote}</p></div><div className="modal-stats"><div><small>{concept.audienceFit!=null?'AUDIENCE FIT':'BUILT FROM'}</small><b>{concept.audienceFit!=null?<>{concept.audienceFit}<em>/100</em></>:<>{concept.evidenceIds.length}<em>pieces of Qloo evidence</em></>}</b></div><div><small>CULTUREFORGE PLANNING BAND · NOT FROM QLOO</small><b>{concept.investment}</b></div><div><small>EXPERIENCE PERSONALITY</small><b>{concept.personality??'Audience-led pilot'}</b></div></div><h3>Proposed experience moments.</h3><div className="ritual-grid">{rituals.map((ritual,index)=><div key={ritual.title}><span>0{index+1}</span><strong>{ritual.title}</strong><p>{ritual.description}</p></div>)}</div><div className="modal-themes"><span className="small-cap">CULTURAL THEMES TO EXPLORE</span><div className="taste-tags">{concept.signals.map(signal=><span key={signal}>{signal}</span>)}</div></div><div className="launch-roadmap"><div><span className="small-cap">YOUR FIRST 30 DAYS</span><h3>Start small. Learn something.</h3></div><ol><li><span>01</span><p><strong>Talk to your audience.</strong>Interview five people about the rituals, places, and experiences they return to.</p></li><li><span>02</span><p><strong>Prototype the signature moment.</strong>Run a small pop-up or invite-only session to test the experience.</p></li><li><span>03</span><p><strong>Follow the signals.</strong>Gather feedback and refine what people wanted to come back for.</p></li></ol></div><div className="modal-bottom"><span><ShieldCheck size={14}/> A starting point for research, not a validated business plan.</span><Button variant="secondary" onClick={close}>Back to the possibilities <ArrowRight size={15}/></Button></div></div></div></div>
}
