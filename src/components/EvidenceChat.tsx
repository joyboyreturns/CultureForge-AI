import { useState } from 'react'
import { LoaderCircle, MessageSquareText } from 'lucide-react'
import type { GenerateResponse } from '../contracts'
import { askTheEvidence } from '../api'
import type { ChatReply } from '../api'

const STARTERS = [
  'Which returned place best supports the leading direction, and why?',
  'What does this audience gravitate to beyond places?',
  'What would most weaken the weakest direction?',
]

/**
 * Ask the evidence.
 *
 * Follow-up questions answered only from this exploration's Qloo evidence,
 * plus at most three more Qloo workflows the model has to justify. Every
 * claim shows the Qloo entities or tags it cites. A question the evidence
 * cannot answer, such as demand or footfall, gets a refusal that says what the
 * evidence does hold, never a guess.
 */
export function EvidenceChat({ result }: { result: GenerateResponse }) {
  const [question, setQuestion] = useState('')
  const [turns, setTurns] = useState<ChatReply[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function ask(text: string) {
    const asked = text.trim()
    if (asked.length < 3 || busy) return
    setBusy(true); setError('')
    try {
      const reply = await askTheEvidence(result, asked, turns.map((turn) => ({ question: turn.question, answer: turn.answer })))
      setTurns((current) => [...current, reply]); setQuestion('')
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'The question could not be answered.')
    }
    setBusy(false)
  }

  return <section className="evidence-chat panel" aria-label="Ask the evidence">
    <span className="small-cap"><MessageSquareText size={13}/> ASK THE EVIDENCE</span>
    <p className="source-panel-note">Answers cite only Qloo entities and tags observed for this brief. A question the evidence cannot answer (demand, footfall, revenue) is refused, not guessed.</p>
    <ol className="evidence-chat-turns">
      {turns.map((turn, index) => <li key={index} className={turn.refused ? 'is-refused' : ''}>
        <strong>{turn.question}</strong>
        <p>{turn.answer}</p>
        {turn.claims.length > 0 && <ul>{turn.claims.map((claim, claimIndex) => <li key={claimIndex}>
          {claim.statement}
          <span className="agent-citations">{claim.citations.map((citation) => <code key={citation.id} title={citation.id}>{citation.label}</code>)}</span>
        </li>)}</ul>}
        <small>
          {turn.cached ? 'Held answer: no new request.' : `${turn.modelCalls} model request${turn.modelCalls === 1 ? '' : 's'} (${turn.model ?? 'model'}), ${turn.upstreamRequests} new Qloo request${turn.upstreamRequests === 1 ? '' : 's'}.`}
          {turn.steps.length > 0 && ` Steps: ${turn.steps.map((step) => `${step.tool} (${step.status})`).join(', ')}.`}
          {turn.rejectedClaims.length > 0 && ` ${turn.rejectedClaims.length} claim${turn.rejectedClaims.length === 1 ? '' : 's'} rejected by the citation check.`}
        </small>
      </li>)}
    </ol>
    {!turns.length && <div className="evidence-chat-starters">
      {STARTERS.map((starter) => <button type="button" key={starter} onClick={() => ask(starter)} disabled={busy}>{starter}</button>)}
    </div>}
    {error && <div className="api-error" role="alert">{error}</div>}
    <form onSubmit={(event) => { event.preventDefault(); ask(question) }}>
      <input aria-label="Ask a question about this evidence" value={question} maxLength={500}
        placeholder="Ask about the places, tags or directions…" onChange={(event) => setQuestion(event.target.value)}/>
      <button type="submit" className="button button-secondary" disabled={busy || question.trim().length < 3}>
        {busy ? <><LoaderCircle size={14} className="spin"/> Reading the evidence…</> : 'Ask'}
      </button>
    </form>
  </section>
}
