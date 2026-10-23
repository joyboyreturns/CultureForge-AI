import type { ResearchRun } from './api'

/** Only a running, evidence-bearing preview may replace the waiting screen. */
export function shouldOpenInitial(run: Pick<ResearchRun, 'status' | 'partialResult'>, enabled: boolean, alreadyOpened: boolean) {
  return enabled && !alreadyOpened && run.status === 'running' && Boolean(run.partialResult?.evidence.length)
}

/** Upgrade only the preview still being read, never an unrelated exploration. */
export function shouldUpgradeInitial(preview: import('./contracts').GenerateResponse | null, completed: import('./contracts').GenerateResponse, previewId: string | null, viewingResults: boolean) {
  if (!viewingResults || !previewId || preview?.projectId !== previewId) return false
  const key = (project: import('./contracts').ProjectRequest) => JSON.stringify([
    project.businessType, project.businessIdea ?? '', project.audience, project.location,
    project.budget, [...project.objectives].sort(),
  ])
  return key(preview.project) === key(completed.project)
}
