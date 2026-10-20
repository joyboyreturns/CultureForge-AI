import type { GenerateResponse, ProjectRequest } from './contracts'
import { mockGenerate } from './mockData'
/** Provider boundary: replace MockCultureProvider with a documented Qloo adapter when credentials/API access are ready. */
export async function generateConcepts(project: ProjectRequest): Promise<GenerateResponse> {
  let response: Response
  try { response = await fetch('/api/projects/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(project) }) }
  catch { return mockGenerate(project) }
  // Vite uses 503 only when its FastAPI proxy cannot connect; provider errors
  // (including a configured Qloo failure) remain visible to the user.
  if (response.status === 503) return mockGenerate(project)
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { detail?: string }
    throw new Error(body.detail ?? `API returned ${response.status}`)
  }
  return await response.json() as GenerateResponse
}
