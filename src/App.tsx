import { useEffect, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight, ArrowUpRight, Bookmark, CheckCheck, ChevronRight, CircleHelp, FlaskConical, Layers3, LayoutGrid, Menu, Moon, Play, Plus, Sparkles, Sun, Waves, X } from 'lucide-react'
import type { Concept, Evidence, GenerateResponse, ProjectRequest } from './contracts'
import { analyzeEvidence, compareAudience, downloadReportPdf, proposeProfile, fetchExploration, fetchHealth, fetchSnapshot, fetchUsage, heldResult, rememberLiveResult, resolveTaste, shareExploration, startResearch, challengeDirections } from './api'
import type { BackendStatus, ChallengeResult, ClarificationAsk, EvidenceAnalysisResult, ProfileProposal, RecomposeResult, TasteSeed } from './api'
import { ProvenanceDrawer } from './components/ProvenanceDrawer'
import { Clarification } from './components/Clarification'
import { RunMonitor } from './components/RunMonitor'
import { shouldUpgradeInitial } from './initialResearch'
import { TasteSeeds } from './components/TasteSeeds'
import { Investigation } from './components/Investigation'
import { EvidenceDependenceMap } from './components/EvidenceDependenceMap'
import type { DependenceSummary } from './components/EvidenceDependenceMap'
import type { VerdictStep } from './components/Challenge'
import { renderBrief } from './brief'
import { ProfileChooser } from './components/ProfileChooser'
import { GuidedTour } from './components/GuidedTour'
import { DecisionNotebook } from './components/DecisionNotebook'
import { StudioBackdrop } from './components/StudioBackdrop'
import logoUrl from '../assets/logo.webp'
import { notebookKey, readDecision, renderDecision } from './decisionNotebook'
import { StudioNav, NavItem } from './components/StudioChrome'
import { Home, DemoShowcase, Create, Progress, NoExploration } from './components/StudioScreens'
import { Results, Compare, ConceptModal } from './components/Results'
import type { Screen, Theme, ResultsView } from './studioShared'
import { RESULT_VIEWS, initial, titles } from './studioShared'
import { readStored, writeStored } from './storage'

export default function App() {
  const [screen, setScreen] = useState<Screen>(() => window.location.hash === '#workspace/create' ? 'create' : 'home')
  const [theme, setTheme] = useState<Theme>(() => readStored('cultureforge-theme', 'dark'))
  const [form, setForm] = useState<ProjectRequest>(initial)
  // The studio opens on whatever real answer this browser already holds, and
  // on nothing at all when it holds none. There is no sample answer to fall
  // back to: an empty studio is honest, a fabricated one is not.
  // A reload reopens the exploration the reader last had open, from this browser's copy of it.
  const [result, setResult] = useState<GenerateResponse | null>(() => heldResult(readStored<ProjectRequest>('cultureforge-last-brief', initial)) ?? heldResult(initial))
  const currentResult = useRef(result)
  currentResult.current = result
  // The provenance drawer belongs to one screen and one exploration: it closes when either changes.
  useEffect(() => { setProvenanceId(null) }, [screen, result?.projectId])
  const [selected, setSelected] = useState('')
  const [backend, setBackend] = useState<BackendStatus | null>(null)
  const [saved, setSaved] = useState<string[]>(() => readStored('cultureforge-saved', []))
  const [menuOpen, setMenuOpen] = useState(false)
  const [providerError, setProviderError] = useState('')
  const [modal, setModal] = useState<Concept | null>(null)
  const [toast, setToast] = useState('')
  const [savedOnly, setSavedOnly] = useState(false)
  const [resultsView, setResultsView] = useState<ResultsView>(() => window.location.hash.startsWith('#map=') ? 'roots' : 'brief')
  // The guided tour asks for the section that holds the element it points at.
  useEffect(() => {
    const show = (event: Event) => {
      const target = (event as CustomEvent<string | undefined>).detail ?? ''
      setResultsView(target.includes('qloo-difference') || target.includes('exec-brief') ? 'brief' : 'places')
    }
    window.addEventListener('cultureforge:show-workbench', show)
    return () => window.removeEventListener('cultureforge:show-workbench', show)
  }, [])
  // A different exploration opens on its answer, not on the section the last one was left on.
  const shownProject = useRef(result?.projectId ?? '')
  useEffect(() => {
    const id = result?.projectId ?? ''
    if (shownProject.current && id && id !== shownProject.current) setResultsView('brief')
    if (id) shownProject.current = id
  }, [result?.projectId])
  const [scenarioBusy, setScenarioBusy] = useState(false)
  const [provenanceId, setProvenanceId] = useState<string | null>(null)
  const [dependenceOpen, setDependenceOpen] = useState(false)
  const [dependenceSummary, setDependenceSummary] = useState<DependenceSummary | null>(null)
  // The answer as it was before a removal was applied from the map, so it can be undone there.
  const [mapUndo, setMapUndo] = useState<{ original: GenerateResponse; label: string } | null>(null)
  const [investigating, setInvestigating] = useState<string | null>(null)
  const [researchRunId, setResearchRunId] = useState<string | null>(null)
  // A run that was set aside because the reader started something else. It keeps
  // being followed, so nothing they asked for is lost.
  const [parked, setParked] = useState<{ runId: string; project: ProjectRequest } | null>(null)
  // The project id of an initial answer opened while its run is still going; cleared when the full results open.
  const [partialId, setPartialId] = useState<string | null>(null)
  const openedInitialRuns = useRef(new Set<string>())
  useEffect(() => {
    const active = readStored<{ runId: string; project: ProjectRequest } | null>('cultureforge-active-run', null)
    if (active?.runId && active.project) { setForm(active.project); setResearchRunId(active.runId); setScreen('progress') }
  }, [])
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
  const [clarification, setClarification] = useState<ClarificationAsk | null>(null)
  const [shareUrl, setShareUrl] = useState('')
  const [tourOpen, setTourOpen] = useState(() => new URLSearchParams(window.location.search).get('tour') === '1')
  const [notebookOpen, setNotebookOpen] = useState(false)
  useEffect(() => { setShareUrl('') }, [result, challenge])
  useEffect(() => { setDependenceSummary(null) }, [result])
  useEffect(() => { setMapUndo(null) }, [result?.projectId])
  const runId = useRef(0)
  const handoffTaken = useRef(false)
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.documentElement.style.colorScheme = theme
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#07070b' : '#f5f1f3')
    writeStored('cultureforge-theme', theme)
  }, [theme])
  useEffect(() => { writeStored('cultureforge-saved', saved) }, [saved])
  const lastBrief = result?.dataMode === 'live' ? result.project : null
  useEffect(() => { if (lastBrief) writeStored('cultureforge-last-brief', lastBrief) }, [lastBrief])
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
          const entityIds = new Set(
            (result!.evidence ?? []).flatMap((item) => (item.kind === 'entity' && item.entityId ? [item.entityId] : [])),
          )
          const stillOurs = Object.keys(chosen.selections).every((id) => entityIds.has(id))
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
  // Leaving a screen closes the provenance drawer, so it never floats over a screen that has no such evidence.
  function navigate(next: Screen) { setMenuOpen(false); setProvenanceId(null); setScreen(next) }
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
  // Applying a one-venue rebuild, and going back. The dependence test and the
  // map's removal experiment share these, so both say and do the same thing.
  function applyRebuild(next: RecomposeResult, venueLabel: string) {
    setResult((current) => current ? { ...current, concepts: next.concepts, evidence: next.evidence, trace: next.trace ?? current.trace, delivery: next.delivery ?? current.delivery, signals: current.signals.filter(signal => next.evidence.some(item => item.entityId === signal.provenance_id)), agent: null, notice: next.notice } : current)
    setSelected(next.concepts[0]?.id ?? ''); setChallenge(null); setChallengeError('')
    setToast(`Applied the recomposition with ${venueLabel} removed. It uses held evidence and was not re-tested.`)
  }
  function restoreBaseline(original: GenerateResponse) {
    setResult(original); setSelected(original.concepts[0]?.id ?? ''); setChallenge(null); setChallengeError('')
    setToast('Restored the original answer.')
  }
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
  function parkCurrentRun() {
    if (researchRunId) setParked({ runId: researchRunId, project: form })
  }
  async function create(project: ProjectRequest = form) {
    const id = ++runId.current
    parkCurrentRun()
    setProviderError(''); setForm(project); setScreen('progress'); setSavedOnly(false)
    setClarification(null); setResearchRunId(null); setSeedCandidates(null); setSeedSelection(null)
    try {
      // The same research run the guided path uses, so the workspace shows the
      // agent's real steps rather than an animation pretending to be them.
      const { runId: started } = await startResearch(project, project.audience, [])
      if (id !== runId.current) return
      writeStored('cultureforge-active-run', { runId: started, project })
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
    if (project.audience.trim().length < 2) {
      setProviderError('Describe who this is for, using at least two characters beyond spaces.')
      document.getElementById('brief-audience')?.focus()
      return
    }
    if (project.location.trim().length < 2) {
      setProviderError('Enter a city or location, using at least two characters beyond spaces.')
      document.getElementById('brief-location')?.focus()
      return
    }
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
    setSeedCandidates(null); parkCurrentRun(); setScreen('progress'); setClarification(null)
    try {
      const { runId: started } = await startResearch(form, form.audience, tagIds)
      writeStored('cultureforge-active-run', { runId: started, project: form })
      setResearchRunId(started)
    } catch (error) {
      setProviderError(error instanceof Error ? error.message : 'The research could not be started.')
      setScreen('create')
    }
  }

  function onRunComplete(data: GenerateResponse) {
    writeStored('cultureforge-active-run', null); setPartialId(null)
    // The run's answer is a real one, so this browser holds it too: a reload
    // paints the same exploration without asking the backend again.
    rememberLiveResult(data.project, data)
    setResult(data); setSelected(data.concepts[0]?.id ?? '01'); setResearchRunId(null); setScreen('results')
  }

  // Opening a finished run that was followed from another screen. The run on
  // the workspace, if any, keeps going where it was.
  function openParked(data: GenerateResponse) {
    const active = readStored<{ runId: string } | null>('cultureforge-active-run', null)
    if (active?.runId === parked?.runId) writeStored('cultureforge-active-run', null)
    setPartialId(null)
    rememberLiveResult(data.project, data)
    setResult(data); setSelected(data.concepts[0]?.id ?? '01'); setParked(null); setScreen('results')
  }

  // The initial rule composition, opened before the agent has finished. It is not remembered in this
  // browser (it is not the finished answer); the run keeps going and the monitor offers the full results.
  function openPartial(data: GenerateResponse) {
    if (researchRunId) {
      openedInitialRuns.current.add(researchRunId)
      setParked({ runId: researchRunId, project: form })
    }
    setResearchRunId(null); setPartialId(data.projectId)
    setResult(data); setSelected(data.concepts[0]?.id ?? '01')
    setResultsView(data.concepts.length ? 'brief' : 'places'); setScreen('results')
  }

  function watchParked() {
    if (!parked) return
    setForm(parked.project); setResearchRunId(parked.runId); setParked(null); setScreen('progress')
  }

  function onRunClarify(ask: ClarificationAsk) {
    writeStored('cultureforge-active-run', null)
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
      setResultsView('brief')
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
      }, profileChoice === profileProposal?.demographic ? '' : profileChoice)
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
      // In the workbench, the verdict is what the reader asked to see.
      setResultsView((view) => view === 'brief' ? view : 'test')
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
    <StudioBackdrop/>
    {menuOpen && <button className="sidebar-backdrop" aria-label="Close navigation" onClick={() => setMenuOpen(false)} />}
    <aside className={`sidebar ${menuOpen ? 'is-open' : ''}`}>
      <button className="brand" onClick={() => navigate('home')} aria-label="CultureForge home"><span className="brand-symbol"><img src={logoUrl} alt="" width="34" height="34"/></span><span>CultureForge<span className="brand-ai">AI</span></span></button>
      <button className="sidebar-close icon-button" aria-label="Close navigation" onClick={() => setMenuOpen(false)}><X size={19}/></button>
      <div className="workspace-switch"><span className="workspace-icon">CF</span><span><strong>Strategy workspace</strong><small>Concepts, taking shape</small></span><ChevronRight size={14}/></div>
      <p className="nav-label">WORKSPACE</p>
      <nav aria-label="Main navigation">
        <NavItem icon={<LayoutGrid size={17}/>} label="Overview" active={screen === 'home'} onClick={() => navigate('home')}/>
        <NavItem icon={<Sparkles size={17}/>} label="New exploration" active={screen === 'create' || screen === 'progress'} onClick={() => navigate('create')}/>
        <NavItem icon={<Layers3 size={17}/>} label="Concept studio" active={screen === 'results' && !savedOnly} onClick={() => { setSavedOnly(false); navigate('results') }} suffix={String(result?.concepts.length ?? 0).padStart(2,'0')}/>
        {result && <div className="nav-sub" role="group" aria-label="Concept studio sections">
          {RESULT_VIEWS.map((view, index) => {
            const count = view.id === 'places' ? result.evidence.filter((item) => item.kind === 'entity').length
              : view.id === 'directions' ? result.concepts.length : null
            const here = screen === 'results' && resultsView === view.id
            return <button key={view.id} className={`nav-subitem${here ? ' active' : ''}`} aria-current={here ? 'page' : undefined} title={view.hint}
              onClick={() => { if (view.id === 'directions') setSavedOnly(false); setResultsView(view.id); navigate('results') }}>
              <span className="nav-subindex">{String(index + 1).padStart(2, '0')}</span><span className="nav-sublabel">{view.label}</span>
              {view.id === 'test' && challenge ? <span className="nav-subdot" aria-label="Tested"/> : count != null ? <small>{String(count).padStart(2, '0')}</small> : null}
            </button>
          })}
        </div>}
        <NavItem icon={<FlaskConical size={17}/>} label="Scenario lab" active={screen === 'compare'} onClick={() => navigate('compare')}/>
      </nav>
      <div className="nav-rule"/><p className="nav-label">YOUR COLLECTION</p>
      <NavItem icon={<Bookmark size={17}/>} label="Saved concepts" active={screen === 'results' && savedOnly} onClick={() => { setSavedOnly(true); setResultsView('directions'); navigate('results') }} suffix={String(savedHere.length).padStart(2, '0')}/>
      <button className="mini-project" onClick={() => navigate('results')}><span className="project-color"/><span>{result ? `${result.project.location.split(',')[0]}, reimagined` : 'Your next exploration'}<small>{result ? `${result.project.businessType} · Exploration` : 'Nothing explored yet'}</small></span><ArrowUpRight size={13}/></button>
      <div className="sidebar-bottom"><div className="demo-promo"><span className="small-cap"><span className="orange-dot"/> THE CULTUREFORGE EXPERIENCE</span><h3>One idea.<br/>A world of possibilities.</h3><button onClick={() => create(initial)}>Run the example brief <Play size={13} fill="currentColor"/></button><span className="demo-promo-art"><Waves size={67} strokeWidth={1}/></span></div>
      <div className="sidebar-foot"><div className="founder-avatar">CF</div><span><strong>Shared workspace</strong><small>Use non-confidential briefs</small></span><span className="workspace-indicator"/></div></div>
    </aside>
    <main className="main-area"><header className="topbar"><div className="topbar-left"><button className="studio-return" onClick={goToLanding}><ArrowLeft size={14}/> Landing</button><button className="mobile-menu icon-button" aria-label="Open navigation" onClick={() => setMenuOpen(true)}><Menu size={20}/></button><span className="topbar-workspace">Workspace</span><ChevronRight size={12}/><span>{titles[screen]}</span></div><div className="topbar-right"><button className="tour-launch" onClick={() => setTourOpen(true)}><CircleHelp size={16}/><span>Guided tour</span></button><span className="prototype-badge" title={backend?.reason ?? undefined}><span/> {backend === null ? 'Checking the backend…' : backend.mode === 'offline' ? 'Backend unreachable' : backend.ready ? 'Qloo configured' : 'No Qloo key — backend is not live'}</span><span className="topbar-separator"/><a className="topbar-link" href="/">Front page <ArrowUpRight size={13}/></a><button className="theme-toggle" aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`} title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`} onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>{theme === 'dark' ? <Sun size={17}/> : <Moon size={17}/>}<span>{theme === 'dark' ? 'Light' : 'Dark'} mode</span></button><button className="top-new icon-button" aria-label="Create a new exploration" onClick={() => navigate('create')}><Plus size={18}/></button></div></header>
      <div className="page-content" key={screen}>
        {screen === 'home' && <div className="tour-welcome"><div><strong>First time here?</strong><span>Follow the brief → evidence → challenge → experiment journey.</span></div><button className="text-link" onClick={() => setTourOpen(true)}>Take the guided tour <ArrowRight size={15}/></button></div>}
        {screen === 'home' && <Home start={() => navigate('create')} demo={() => create(initial)} runExample={(project) => create(project)} explore={() => navigate('results')} openExploration={async (id) => { try { const record = await fetchExploration(id); const saved = (record as { challenge?: ChallengeResult }).challenge; setResult({ ...record.result, delivery: { ...record.result.delivery, kind: 'snapshot', servedAt: new Date().toISOString(), transportRequests: 0 } }); setSelected(record.result.concepts[0]?.id ?? ''); if (saved) { setChallenge(saved); setChallengeSavedAt(new Date().toLocaleString()) } navigate('results'); setToast(saved ? 'Reopened from your saved explorations, with its evidence test.' : 'Reopened from your saved explorations.') } catch (error) { setToast(error instanceof Error ? error.message : 'That exploration could not be opened.') } }}/>}
        {screen === 'create' && (seedCandidates
          ? <TasteSeeds candidates={seedCandidates} audience={form.audience} busy={seedBusy}
              selected={seedSelection ?? seedCandidates.map((candidate) => candidate.tagId)}
              onChange={setSeedSelection}
              onConfirm={confirmSeeds} onCancel={() => setSeedCandidates(null)}/>
          : <Create form={form} setForm={setForm} submit={() => beginResearch()} runExample={(project) => create(project)} error={providerError} back={() => navigate('home')}/>)}
        {screen === 'create' && clarification && <Clarification ask={clarification} idea={form.businessIdea ?? ''}
          onUseIdea={(value) => { const next = {...form, businessIdea: value}; setForm(next); setClarification(null); beginResearch(next) }}
          onUseLocation={(value) => { const next = {...form, location: value}; setForm(next); setClarification(null); beginResearch(next) }}
          onEditField={(field) => { setClarification(null); window.setTimeout(() => document.getElementById(field === 'location' ? 'brief-location' : field === 'audience' ? 'brief-audience' : 'brief-idea')?.focus(), 0) }}/>}
        {screen === 'progress' && (researchRunId
          ? <Progress project={form} runId={researchRunId} autoOpenPartial={!openedInitialRuns.current.has(researchRunId)} onOpenPartial={openPartial} onComplete={onRunComplete} onClarify={onRunClarify} onGiveUp={() => { writeStored('cultureforge-active-run', null); setResearchRunId(null); setScreen('create') }} onRetry={() => { writeStored('cultureforge-active-run', null); void confirmSeeds(seedSelection ?? []) }} onChangeLocation={() => { writeStored('cultureforge-active-run', null); setResearchRunId(null); setScreen('create'); window.setTimeout(() => document.getElementById('brief-location')?.focus(), 50) }}/>
          : <Progress project={form}/>)}
        {(screen === 'results' || screen === 'compare') && <StudioNav
          back={screen === 'compare' ? { label: 'Back to concept studio', go: () => navigate('results') } : { label: 'Back to overview', go: () => navigate('home') }}
          overview={screen === 'compare' ? () => navigate('home') : undefined}
          switchIdea={() => navigate('create')}
          examples={() => document.getElementById('demo-showcase-title')?.scrollIntoView({ behavior: 'smooth', block: 'center' })}/>}
        {screen === 'results' && result && partialId === result.projectId && !result.agent && <div className="partial-banner panel" role="status"><strong>First evidence is ready · research continues in the background.</strong> This is an initial answer from the Qloo records received so far. Further research and optional model analysis are still running. The status card shows real progress. This view updates automatically when the full report is ready; its conclusions may change.</div>}
        {screen === 'results' && (result
          ? <><Results view={resultsView} onView={setResultsView} result={result} selected={selected} select={setSelected} saved={saved} save={save} savedOnly={savedOnly} setSavedOnly={setSavedOnly} open={setModal} compare={() => navigate('compare')} exportBrief={exportBrief} onInspect={setProvenanceId} onShare={shareThisExploration} shareUrl={shareUrl} onNotebook={() => setNotebookOpen(true)} onInvestigate={setInvestigating} onEvidenceDependence={() => setDependenceOpen(true)} challenge={challenge} challenging={challenging} challengeError={challengeError} onChallenge={() => testDirections()} onReanchor={(directionId, anchorEntityId) => testDirections(directionId, anchorEntityId)} onCloseChallenge={() => setChallenge(null)} usage={usage} onNewBrief={() => navigate('create')} onRewordIdea={(idea) => { void create({ ...result.project, businessIdea: idea }) }} challengeHistory={challengeHistory} challengeSavedAt={challengeSavedAt} analysis={analysis} analysisBusy={analysisBusy} analysisError={analysisError} onAnalyze={analyzeCurrentEvidence} dependenceSummary={dependenceSummary} onExportPdf={exportPdf} onApplyRebuild={(next, label) => { if (result) setMapUndo({ original: result, label }); applyRebuild(next, label) }} mapUndo={mapUndo ? { label: mapUndo.label, run: () => { restoreBaseline(mapUndo.original); setMapUndo(null) } } : null} profileControl={<ProfileChooser proposal={profileProposal} chosen={profileChoice} onChoose={setProfileChoice} testedWith={challenge?.profile.demographic}/>}/><DemoShowcase onRun={(project) => create(project)} title="Explore another example"/></>
          : <NoExploration start={() => navigate('create')} runExample={(project) => create(project)}/>)}
        {result && investigating && (() => { const concept = result.concepts.find((c) => c.id === investigating); if (!concept) return null; const verdict = challenge?.directions.find((entry) => entry.directionId === concept.id); /* Only an alternative anchor is named as one; the original anchor is the place the direction is built around. */ const testedAnchor = verdict?.isCounterfactual ? verdict.anchor?.label ?? null : null; return <Investigation concept={concept} project={result.project} evidence={result.evidence} seedTagIds={result.provenance?.resolved_tags} testedAnchorLabel={testedAnchor} onClose={() => setInvestigating(null)}/> })()}
        {result && <ProvenanceDrawer evidence={result.evidence} concepts={result.concepts} trace={result.trace} evidenceId={provenanceId} project={result.project} selection={presentation} onClose={() => setProvenanceId(null)} onRecomposed={(next)=>{ setResult({...result, concepts:next.concepts, evidence:next.evidence, trace:next.trace ?? result.trace, delivery:next.delivery ?? result.delivery, signals:result.signals.filter(signal => next.evidence.some(item => item.entityId === signal.provenance_id)), agent:null, notice:next.notice}); setSelected(next.concepts[0]?.id ?? ''); setToast(next.concepts.length ? 'Rebuilt without that venue. Qloo was not called again, and no model was asked to name anything.' : 'No direction remains supported after removing that venue.') }}/>}
        {screen === 'compare' && (result
          ? <><Compare result={result} apply={applyScenario} busy={scenarioBusy}/><DemoShowcase onRun={(project) => create(project)} title="Compare with another example"/></>
          : <NoExploration start={() => navigate('create')} runExample={(project) => create(project)}/>)}
      </div><footer className="page-footer"><span><Waves size={13}/> CultureForge AI <i/> A prototype for location and concept strategists. Where Qloo doesn’t have enough data, it says so instead of guessing.</span><span>Human ambition. Cultural intelligence.</span></footer>
    </main>
    {notebookOpen && result && result.concepts.length > 0 && <DecisionNotebook key={notebookKey(result, result.concepts.find((c) => c.id === selected) ?? result.concepts[0])} result={result} concept={result.concepts.find((c) => c.id === selected) ?? result.concepts[0]} challenge={challenge} onClose={() => setNotebookOpen(false)}/>}
    {tourOpen && <GuidedTour screen={screen} hasEvidence={Boolean(result?.evidence.length && result?.concepts.length)} onNavigate={navigate} onClose={closeTour} onInspect={() => setProvenanceId(result?.evidence.find((e) => e.kind === 'entity')?.id ?? result?.evidence[0]?.id ?? null)} onRemoval={() => setDependenceOpen(true)} onNotebook={() => setNotebookOpen(true)}/>}
    {dependenceOpen && result && <EvidenceDependenceMap baseline={result} onSummary={(summary) => { if (currentResult.current === result) setDependenceSummary(summary) }} onClose={() => setDependenceOpen(false)} onUseRebuild={applyRebuild} onRestoreBaseline={restoreBaseline}/ >}
    {modal && <ConceptModal concept={modal} saved={saved.includes(modal.id)} save={() => save(modal.id)} close={() => setModal(null)}/ >}
    {(() => {
      const foreground = researchRunId && screen !== 'progress' && !seedCandidates ? { runId: researchRunId, project: form } : null
      if (!foreground && !parked) return null
      return <div className="run-dock" data-tour-skip>
        {parked && <RunMonitor key={parked.runId} runId={parked.runId} project={parked.project} earlier={Boolean(researchRunId)}
          onOpen={openParked}
          onReady={(data) => {
            if (shouldUpgradeInitial(result, data, partialId, screen === 'results')) {
              openParked(data)
              setToast('Research complete — full evidence and report ready.')
            }
          }}
          onClarify={(ask) => { setForm(parked.project); setClarification(ask); setParked(null); setScreen('create') }}
          onWatch={watchParked}
          onDismiss={() => setParked(null)}/>}
        {foreground && <RunMonitor key={foreground.runId} runId={foreground.runId} project={foreground.project}
          onOpen={onRunComplete} onClarify={onRunClarify}
          onWatch={() => setScreen('progress')}
          onDismiss={() => { writeStored('cultureforge-active-run', null); setResearchRunId(null) }}/>}
      </div>
    })()}
    {toast && <div className="toast" role="status"><CheckCheck size={17}/>{toast}</div>}
  </div>
}
