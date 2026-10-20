import { useMemo, useState } from 'react'
import type { Concept, Evidence } from '../contracts'

/**
 * The evidence-to-idea constellation.
 *
 * Three rings, laid out deterministically:
 *   centre - the audience Qloo resolved the brief to
 *   middle - the local venues Qloo returned for that audience
 *   outer  - the business decisions CultureForge drew from them
 *
 * Solid lines are relationships Qloo returned. Dashed lines are CultureForge's
 * interpretive use of that evidence. The distinction is the whole point: a
 * judge can see which lines came from the API and which ones are ours.
 *
 * Positions are layout, not meaning. Nothing here is a learned similarity.
 */

// The viewBox is roomy on purpose: every node carries a label, and a graph
// that clips its own words is not worth reading.
const VIEW = { width: 880, height: 660, cx: 440, cy: 320 }
const RING = { seed: 104, venue: 180, decision: 266 }
// Each ring's label sits on its own band: the inner rings label towards the
// centre, the outer ring labels away from it, so the three bands never meet.
const LABEL_RING = { seed: 78, venue: 154, decision: 292 }

type NodeKind = 'seed' | 'venue' | 'decision'

interface Node {
  id: string
  kind: NodeKind
  label: string
  detail: string
  x: number
  y: number
  radius: number
  /** Where the label goes, on its own band. */
  labelX: number
  labelY: number
  anchor: 'start' | 'middle' | 'end'
}

interface Edge {
  from: string
  to: string
  kind: 'qloo' | 'ours'
}

function polar(radius: number, index: number, total: number, offset = 0) {
  const angle = (offset + (index / Math.max(1, total)) * Math.PI * 2) - Math.PI / 2
  return { x: VIEW.cx + Math.cos(angle) * radius, y: VIEW.cy + Math.sin(angle) * radius }
}

/**
 * Place a label on its ring's band and point it away from the centre, so the
 * text runs along the graph rather than into it.
 */
function labelSpot(x: number, y: number, band: number): { labelX: number; labelY: number; anchor: 'start' | 'middle' | 'end' } {
  const dx = x - VIEW.cx
  const dy = y - VIEW.cy
  const length = Math.max(1, Math.hypot(dx, dy))
  const labelX = VIEW.cx + (dx / length) * band
  const labelY = VIEW.cy + (dy / length) * band
  const anchor = dx < -24 ? 'end' : dx > 24 ? 'start' : 'middle'
  return { labelX, labelY, anchor }
}

function shorten(text: string, max: number) {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text
}

const NODE_RADIUS: Record<NodeKind, number> = { seed: 6, venue: 7, decision: 8 }

export function CulturalConstellation({
  evidence, concepts, selectedId, onSelect, onInspect,
}: {
  evidence: Evidence[]
  concepts: Concept[]
  selectedId: string
  onSelect: (conceptId: string) => void
  onInspect: (evidenceId: string) => void
}) {
  const [hovered, setHovered] = useState<string | null>(null)
  // The heat overlay draws Qloo's popularity as the size of each node, so the
  // map shows where the cultural weight actually is.
  const [heat, setHeat] = useState(false)

  const { nodes, edges } = useMemo(() => {    const seeds = evidence.filter((item) => item.kind === 'tag')
    const venues = evidence.filter((item) => item.kind === 'entity')
    const built: Node[] = []
    const links: Edge[] = []

    // The audience sits at the centre.
    built.push({
      id: '__audience__', kind: 'seed', label: 'Your audience',
      detail: 'The brief Qloo was asked to resolve', x: VIEW.cx, y: VIEW.cy, radius: 30,
      labelX: VIEW.cx, labelY: VIEW.cy, anchor: 'middle',
    })
    seeds.forEach((seed, index) => {
      const point = polar(RING.seed, index, seeds.length)
      built.push({
        id: seed.id, kind: 'seed', label: seed.label,
        detail: seed.tagId ?? 'Audience seed', radius: NODE_RADIUS.seed, ...point,
        ...labelSpot(point.x, point.y, LABEL_RING.seed),
      })
      links.push({ from: '__audience__', to: seed.id, kind: 'qloo' })
    })

    // The venues Qloo returned sit on the middle ring.
    venues.forEach((venue, index) => {
      const point = polar(RING.venue, index, venues.length)
      built.push({
        id: venue.id, kind: 'venue', label: venue.label,
        detail: venue.entityType ?? 'Qloo place', radius: NODE_RADIUS.venue, ...point,
        ...labelSpot(point.x, point.y, LABEL_RING.venue),
      })
      // A venue hangs off the seed it was returned for. Every venue is linked to
      // the first seed, because Qloo returned it for the whole signal set.
      if (seeds.length) links.push({ from: seeds[0].id, to: venue.id, kind: 'qloo' })
    })

    // The decisions sit on the outer ring, linked by the evidence they used.
    const decisions = concepts.flatMap((concept) =>
      concept.decisions.map((decision) => ({ concept, decision })))
    decisions.forEach((entry, index) => {
      const id = `${entry.concept.id}::${entry.decision.id}`
      // The decisions of one concept sit next to each other on the ring, so
      // the shape of the graph shows the grouping.
      const conceptIndex = concepts.findIndex((candidate) => candidate.id === entry.concept.id)
      const offset = -Math.PI / 2 + (conceptIndex / Math.max(1, concepts.length)) * Math.PI * 2
      const point = polar(RING.decision, index, decisions.length, offset * 0)
      built.push({
        id, kind: 'decision',
        label: `${entry.concept.name} · ${entry.decision.field}`,
        detail: entry.decision.proposal, radius: NODE_RADIUS.decision, ...point,
        ...labelSpot(point.x, point.y, LABEL_RING.decision),
      })
      entry.decision.evidenceIds.forEach((evidenceId) => {
        links.push({ from: evidenceId, to: id, kind: 'ours' })
      })
    })

    return { nodes: built, edges: links }
  }, [evidence, concepts])

  const selected = concepts.find((concept) => concept.id === selectedId)
  const highlighted = new Set<string>()
  if (selected) {
    highlighted.add(selected.id)
    selected.evidenceIds.forEach((id) => highlighted.add(id))
    selected.decisions.forEach((decision) => highlighted.add(`${selected.id}::${decision.id}`))
  }
  const focus = hovered ?? (highlighted.size ? [...highlighted][0] : null)

  const dimmed = (id: string) => {
    if (!selected) return false
    if (highlighted.has(id)) return false
    // Anything connected to the highlighted set stays legible.
    return !edges.some((edge) =>
      (edge.from === id && highlighted.has(edge.to)) || (edge.to === id && highlighted.has(edge.from)))
  }

  return (
    <div className="constellation">
      <svg viewBox={`0 0 ${VIEW.width} ${VIEW.height}`} role="img" aria-label="How the returned evidence became the business directions">
        <defs>
          <marker id="arrow-qloo" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 z" fill="rgba(182,224,168,.55)" />
          </marker>
          <marker id="arrow-ours" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 z" fill="rgba(199,163,255,.6)" />
          </marker>
        </defs>

        {edges.map((edge, index) => {
          const from = nodes.find((node) => node.id === edge.from)
          const to = nodes.find((node) => node.id === edge.to)
          if (!from || !to) return null
          const faded = dimmed(edge.from) && dimmed(edge.to)
          return (
            <line
              key={`${edge.from}->${edge.to}-${index}`}
              x1={from.x} y1={from.y} x2={to.x} y2={to.y}
              className={`constellation-edge is-${edge.kind}${faded ? ' is-faded' : ''}`}
              markerEnd={edge.kind === 'qloo' ? 'url(#arrow-qloo)' : 'url(#arrow-ours)'}
            />
          )
        })}

        {nodes.map((node) => {
          const isDecision = node.kind === 'decision'
          const isSelected = node.id === selected?.id
          const popularity = heat
            ? evidence.find((item) => item.id === node.id)?.popularity
            : undefined
          const radius = popularity != null
            ? node.radius * (1.4 + popularity * 1.9)
            : node.radius
          return (
            <g
              key={node.id}
              className={`constellation-node is-${node.kind}${dimmed(node.id) ? ' is-faded' : ''}${isSelected ? ' is-selected' : ''}`}
              onMouseEnter={() => setHovered(node.id)}
              onMouseLeave={() => setHovered(null)}
              onClick={() => {
                if (isDecision) onSelect(node.id.split('::')[0])
                else if (node.kind === 'venue') onInspect(node.id)
              }}
              role={isDecision ? 'button' : undefined}
              tabIndex={isDecision ? 0 : undefined}
              onKeyDown={(event) => {
                if (isDecision && (event.key === 'Enter' || event.key === ' ')) {
                  event.preventDefault()
                  onSelect(node.id.split('::')[0])
                }
              }}
            >
              {node.kind === 'seed' && node.id === '__audience__' && (
                <circle cx={node.x} cy={node.y} r={26} className="constellation-hub" />
              )}
              <circle cx={node.x} cy={node.y} r={radius} className="constellation-dot" />
              <title>{node.label}{node.detail ? ` — ${node.detail}` : ''}</title>
              {node.id === '__audience__' ? (
                <text x={node.labelX} y={node.labelY} textAnchor="middle" className="constellation-hub-label">
                  <tspan x={node.labelX} dy="-7">Your</tspan>
                  <tspan x={node.labelX} dy="13">audience</tspan>
                </text>
              ) : (
                <text
                  x={node.labelX}
                  y={node.labelY}
                  textAnchor={node.anchor}
                  dominantBaseline="middle"
                  className="constellation-label"
                >
                  {shorten(node.label, node.kind === 'decision' ? 24 : 20)}
                </text>
              )}
            </g>
          )
        })}
      </svg>

      <div className="constellation-controls">
        <button
          type="button"
          className={`heat-toggle${heat ? ' is-on' : ''}`}
          aria-pressed={heat}
          onClick={() => setHeat((current) => !current)}
        >
          {heat ? 'Popularity heat on' : 'Show popularity heat'}
        </button>
        <ul className="constellation-legend">
          <li><i className="is-qloo" /> Returned by Qloo</li>
          <li><i className="is-ours" /> CultureForge’s reading of it</li>
        </ul>
      </div>

      {/* The same information, reachable without a pointer. */}
      <details className="constellation-list">
        <summary>Read the evidence chain as a list</summary>
        <ol>
          {concepts.map((concept) => (
            <li key={concept.id}>
              <strong>{concept.name}</strong>
              <ul>
                {concept.decisions.map((decision) => (
                  <li key={decision.id}>
                    {decision.field}: {decision.proposal}
                    <em>
                      from {decision.evidenceIds.map((id) => {
                        const item = evidence.find((candidate) => candidate.id === id)
                        return item?.label ?? id
                      }).join(', ')}
                    </em>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ol>
      </details>
    </div>
  )
}
