// State that belongs together with the effect that keeps it true, lifted out of App so the studio's
// component reads as the flow of the screens rather than as bookkeeping.
import { useEffect, useRef, useState } from 'react'
import type { Dispatch, SetStateAction } from 'react'
import type { GenerateResponse, ProjectRequest } from './contracts'
import { analyzeEvidence, fetchHealth } from './api'
import type { BackendStatus, ChallengeResult, EvidenceAnalysisResult } from './api'
import { readStored, writeStored } from './storage'
import type { Theme } from './studioShared'

/** The colour scheme, remembered in this browser and applied to the document. */
export function useTheme(): [Theme, Dispatch<SetStateAction<Theme>>] {
  const [theme, setTheme] = useState<Theme>(() => readStored('cultureforge-theme', 'dark'))
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.documentElement.style.colorScheme = theme
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#07070b' : '#f5f1f3')
    writeStored('cultureforge-theme', theme)
  }, [theme])
  return [theme, setTheme]
}

/** The directions the reader saved, remembered in this browser. */
export function useSavedConcepts(): [string[], Dispatch<SetStateAction<string[]>>] {
  const [saved, setSaved] = useState<string[]>(() => readStored('cultureforge-saved', []))
  useEffect(() => { writeStored('cultureforge-saved', saved) }, [saved])
  return [saved, setSaved]
}

/** A short confirmation that clears itself after three seconds. */
export function useToast(): [string, Dispatch<SetStateAction<string>>] {
  const [toast, setToast] = useState('')
  useEffect(() => {
    if (!toast) return
    const timer = window.setTimeout(() => setToast(''), 3000)
    return () => clearTimeout(timer)
  }, [toast])
  return [toast, setToast]
}

/** Remember the brief behind the last live answer, so a reload reopens it from this browser's copy. */
export function useRememberedBrief(result: GenerateResponse | null): void {
  const brief: ProjectRequest | null = result?.dataMode === 'live' ? result.project : null
  useEffect(() => { if (brief) writeStored('cultureforge-last-brief', brief) }, [brief])
}

/** What the backend is actually doing right now. The badge says this, not what the app hopes is true. */
export function useBackendStatus(): BackendStatus | null {
  const [backend, setBackend] = useState<BackendStatus | null>(null)
  useEffect(() => {
    let cancelled = false
    fetchHealth()
      .then((status) => { if (!cancelled) setBackend(status) })
      .catch(() => { if (!cancelled) setBackend({ mode: 'offline', ready: false, reason: 'The backend could not be reached.', workflows: [] }) })
    return () => { cancelled = true }
  }, [])
  return backend
}

/**
 * The bounded analysis of the evidence on screen.
 *
 * It belongs to one answer and one verdict: when either changes, it is dropped, and an answer that
 * arrives after that is discarded rather than shown against the wrong evidence.
 */
export function useEvidenceAnalysis(result: GenerateResponse | null, challenge: ChallengeResult | null) {
  const [analysis, setAnalysis] = useState<EvidenceAnalysisResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const latest = useRef({ result, challenge })
  latest.current = { result, challenge }
  useEffect(() => { setAnalysis(null); setError('') }, [result, challenge])

  async function analyze() {
    if (!result || busy) return
    const stillCurrent = () => latest.current.result === result && latest.current.challenge === challenge
    setBusy(true); setError('')
    try {
      const answer = await analyzeEvidence(result.project, result.evidence, result.concepts, challenge)
      if (!stillCurrent()) { setBusy(false); return }
      setAnalysis(answer)
    } catch (caught) {
      if (stillCurrent()) setError(caught instanceof Error ? caught.message : 'Evidence analysis could not be completed.')
    }
    setBusy(false)
  }
  return { analysis, analysisBusy: busy, analysisError: error, analyze }
}
