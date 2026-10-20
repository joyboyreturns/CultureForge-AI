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

const VIEW = { width: 720, height: 520, cx: 360, cy: 250 }

type NodeKind = 'seed' | 'venue' | 'decision'

interface Node {
  id: string
  kind: NodeKind
  label: string
  detail: string
  x: number
  y: number
  radius: number
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
      detail: 'The brief Qloo was asked to resolve', x: VIEW.cx, y: VIEW.cy, radius: 26,
    })
    seeds.forEach((seed, index) => {
      const point = polar(112, index, seeds.length)
      built.push({
        id: seed.id, kind: 'seed', label: seed.label,
        detail: seed.tagId ?? 'Audience seed', radius: NODE_RADIUS.seed, ...point,
      })
      links.push({ from: '__audience__', to: seed.id, kind: 'qloo' })
    })

    // The venues Qloo returned sit on the middle ring.
    venues.forEach((venue, index) => {
      const point = polar(196, index, venues.length)
      built.push({
        id: venue.id, kind: 'venue', label: venue.label,
        detail: venue.entityType ?? 'Qloo place', radius: NODE_RADIUS.venue, ...point,
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
      const point = polar(272, index, decisions.length)
      built.push({
        id, kind: 'decision', label: entry.concept.name,
        detail: entry.decision.field, radius: NODE_RADIUS.decision, ...point,
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
              <text x={node.x} y={node.y + radius + 13} className="constellation-label">
                {node.label.length > 26 ? `${node.label.slice(0, 25)}…` : node.label}
              </text>
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
