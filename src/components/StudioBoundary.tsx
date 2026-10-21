import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'

export class StudioBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error('Studio rendering failed', error, info.componentStack) }
  render() {
    if (!this.state.failed) return this.props.children
    return <main className="studio-shell"><section className="empty-state panel" role="alert">
      <h1>The studio could not display this exploration.</h1>
      <p>Reload to reopen the studio. Previously held Qloo evidence remains available in this browser.</p>
      <button className="primary-button" onClick={() => window.location.reload()}>Reload the studio</button>
      <p><a href="/studio/">Start from the studio overview</a></p>
    </section></main>
  }
}
