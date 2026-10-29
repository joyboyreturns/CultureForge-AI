// Small, failure-tolerant wrappers over localStorage: storage can be disabled or full.
export function readStored<T,>(key: string, fallback: T): T {
  try { const value = localStorage.getItem(key); return value ? JSON.parse(value) as T : fallback } catch { return fallback }
}
export function writeStored(key: string, value: unknown) { try { localStorage.setItem(key, JSON.stringify(value)) } catch { /* Storage can be disabled in private browser sessions. */ } }
