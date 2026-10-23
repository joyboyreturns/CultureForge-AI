# Project knowledge workflow

Two retrieval surfaces: a **graphify** knowledge graph over the code, and an **Obsidian vault** of per-node notes. Both are scoped queries — never load `graph.json`, `GRAPH_REPORT.md`, or the whole vault into context.

## Tools

| Surface | How to reach it |
|---|---|
| Graph MCP (OpenCode) | `mcp.servers.cultureforge-graph` in `opencode.json` → `scripts/graphify_mcp.sh`. Tools: `query_graph`, `get_node`, `get_neighbors`, `get_community`, `shortest_path`, `god_nodes`, `graph_stats`. |
| Graph CLI (fallback / Antigravity) | `graphify query "..." --budget 1500`, `graphify explain "X"`, `graphify path "A" "B"`, `graphify god-nodes --top 5` |
| Obsidian vault (retrieval) | `python3 scripts/vault_query.py "<label>" [--code]` — one note, scoped, with frontmatter + connections. |

## Retrieval ladder

Climb and stop at the first rung that answers the question.

1. **`query_graph(question, token_budget=1500, context_filter=[...])`** — scoped subgraph. Use `context_filter` (`["call"]`, `["def"]`) to cut noise. Drop to `token_budget=700` for narrow questions.
2. **`get_node(label)` / `get_neighbors(label, token_budget=800)`** — one concept and its edges.
3. **`get_community(community_id, token_budget=1200)`** — one cluster. Use `god_nodes(top_n=5)` and `graph_stats()` to orient first.
4. **`shortest_path(source, target)`** — how two concepts connect, without pulling in either neighborhood.
5. **`scripts/vault_query.py "<label>"`** — the Obsidian note for a node: frontmatter (`source_file`, `location`, `community`) plus its `## Connections`. Add `--code` to append the exact source excerpt. Other modes: `--search "<text>"`, `--source "<path>"`, `--list [--community X]`, `--stats`, `--json`.
6. **Source file** — only when exact behavior or an edit matters. Use `rg` with a tight pattern; read only the cited line range.

The vault is a retrieval source *and* a human browsing surface. Prefer a vault note over grepping raw files: it is smaller and already normalized to graph structure.

## Maintenance

- The graph (`graphify-out/`), the vault (`CultureForge AI/`), `.graphifyignore`, `opencode.json`, `.agents/` and `.opencode/` are **local only** and gitignored. On a fresh clone, create them with `graphify update .` and `graphify export obsidian --dir "CultureForge AI"` before using the retrieval ladder.

- Refresh the graph after substantial source changes: `graphify update .` (AST-only, no API cost).
- Re-export the vault: `graphify export obsidian --dir "CultureForge AI"`.
- Re-label communities after a major refactor: `graphify label . --missing-only`.
- `graphify label` needs an LLM backend (a Gemini key, or a logged-in `claude` CLI). With neither available it falls back to hub-derived names like `main.py` or `providers.py`, which are not useful labels. In that case, write the names by hand: put them in `graphify-out/.graphify_labels.json` keyed by community index, then set each node's `community_name` in `graphify-out/graph.json` to match, and re-run `graphify export obsidian --dir "CultureForge AI"`. The MCP reads `community_name` off the node, not the labels file, so editing only the labels file changes nothing.
- The vault is an **export**, not a graph input. `.graphifyignore` excludes `/CultureForge AI/` from the scan — do not remove it. Re-ingesting the vault feeds the graph its own output and inflates every query.
- Keep `scripts/vault_query.py`'s index fresh automatically; it rebuilds on vault mtime change.

## The shape of the codebase

| Module | What it owns |
|---|---|
| `backend/main.py` | The HTTP surface. Typed requests, one error envelope, status codes that mean something. |
| `backend/intent.py` / `backend/intent_report.py` | The idea read into typed components (hybrids, specialisations, disclosed simplifications) and the per-business evidence found for each. Tags still come only from returned `find_tags` envelopes. |
| `backend/providers.py` | The Qloo provider. One request builder per workflow, because Qloo rejects fields it does not know. |
| `backend/investigation.py` | The decision loop: the questions a direction has not answered, each one a named workflow. |
| `backend/agent.py` | The bounded agent loop inside a research run: up to eight plan-act-observe steps over allowlisted Qloo workflows (server-built requests, observed IDs only), then an analysis whose every claim must cite an entity ID or tag URN from the run's envelopes. Falls back to the rule composer, and says so. |
| `backend/research.py` | The observable run state machine: Qloo retrieval, deterministic composition, then the bounded AI controller when configured. |
| `backend/platform.py` | The licensable layer: workspaces, issued keys, saved explorations, metering. SQLite. |
| `backend/evidence_store.py` | The durable evidence cache. A held answer costs nothing; a failure is never cached. |
| `backend/concept_composer.py` | The rules that turn evidence into directions. Every proposal names its evidence. |
| `src/wildroot.css` | The editorial layer, over the dashboard styles. |
| `src/dusk.css` | The landing page's look for the studio (tokens, type, pills, glass, the section navigation). Imported last, so it wins. |

Three rules the codebase holds to, and the tests pin them:

1. **Never show a number Qloo did not return.** No invented fit scores, and no
   borrowed durations — a reused step reports zero and states the original.
2. **Never let a malformed request through.** Every route that takes a body
   takes a typed one, so a string where a list was meant is a 422.
3. **Never fail silently.** A rate limit or an exhausted budget becomes a
   stated limitation in the report, not a crash and not a blank panel.

A fourth, newer: **never show mock data.** The studio has no mock path at
all. `get_provider()` in `auto` mode requires a Qloo key and refuses to answer
without one; `MockCultureProvider` is the pytest fixture and is reachable only
when `CULTUREFORGE_PROVIDER=mock` is set by name. The frontend has no
fallback either — `src/api.ts` throws a readable error instead of inventing an
answer, and `scripts/verify_contracts.mjs` fails if a mock reference ever
comes back.

A fifth: **the test must be able to fail.** `backend/challenge.py` puts a
direction on trial against the local evidence, and a direction can come out
`contested`. If every direction ever passes, the feature is decoration — the
verdict has to be able to disagree with the composer, and the order the
directions are shown in has to be allowed to change. The verdicts are about
local cultural fit and say so on the screen: not demand, competition, rent or
willingness to pay. A tag counts as a cultural signal by its Qloo family, and
an unknown family counts as plain, so the rule can say no.

A sixth: **a verdict is a verdict about something.** The scope is stated on
the screen — *anchor fit within the retrieved sample*, not "the business" — and
every direction carries its claim, its falsifier and its unproven condition,
plus the policy version that produced it. A direction can be held to a
different anchor and re-tested, so the reader can see the answer depend on
the assumption rather than take it on trust. Keep the scope narrow: a check
that does not say what it is about reads as a check that says more than it
does.

And say what the check *did*, not what it sounds like it did. The ranking
request sends a demographic profile and a location, not the audience's own
cultural tags, so the reason must not say "for this audience's cultural
signals" — and the profile was proposed by CultureForge from the brief, not
inferred by Qloo, so it must not say Qloo inferred it either. A comparison
is against **every other place that was returned**, cited or not, so that
changing the anchor changes one assumption and not two. A tag returned for
the anchor is never called exclusive: the comparison response is a bounded
list, and absence is not proof. One passing check and one missing check is
not a verdict — it is half an answer, and it is `unproven`. When the policy's
logic or wording changes, the policy version changes with it.

And when a direction is held to a different place, say so. The verdict then
answers for that place and the concept was not rebuilt, so the screen states
the alternative anchor, the original reference, and that nothing was
recomposed. A badge beside a description and a photograph that belong to a
different place is a contradiction a judge can see.

And let the evidence go. Removing a place must rebuild the answer from what
is left — out of the description, the photograph, the citations and the
anchor — not merely out of the evidence list. A recomposition that claims to
have rebuilt while the removed venue is still the anchor is the worst kind
of lie this product could tell.

A seventh: **never strand the reader.** Every state that can fail must offer a
way out. An audience that resolves to nothing, a run that cannot finish, a
place with no photograph, a brief that supported no direction, a verdict that
does not belong to the directions on screen — each has a stated state and a
way forward. A judge who cannot get out of a screen will not try the next
thing.

## The Vercel model layer

`backend/llm.py` is the only transport for optional wording and evidence analysis. All model traffic goes through Vercel AI Gateway using the server-only `AI_GATEWAY_API_KEY` and `AI_GATEWAY_MODEL`; `AI_GATEWAY_ENABLED=true` is the explicit opt-in. Never add another provider, provider fallback, or client-side key.

- The model writes bounded direction names/taglines or selects existing evidence strings; deterministic rules retain all factual claims, Qloo evidence, verdicts, and citations. Reject unsupported numbers and malformed output.
- Naming makes one bounded request and never retries or switches providers. Missing credentials, budget exhaustion, timeout, or invalid output leaves the rule-based wording intact and reports the state in the trace.
- The local naming allowance is `LLM_MAX_CALLS_PER_HOUR` / `LLM_MAX_CALLS_PER_DAY` (defaults 20/50, enforced in the dev profile only). Do not raise these limits to work around a failure.
- Evidence analysis uses the same Vercel gateway, with its own bounded daily allowance. Keep its reasoning and response budgets capped and never put provider credentials in browser code.
- Cache successful model-derived results with the evidence they depend on. Do not cache failures or empty output as a successful answer.

## Caching, and what it costs

Two caches, both holding real answers:

- **The server's evidence store** (`backend/evidence_store.py`) keeps every
  workflow envelope on disk for 24 hours (30 days in the judging profile), keyed by the canonical workflow
  input. A repeated brief is served from it for zero upstream requests.
- **The browser's copy** (`src/api.ts`) keeps the composed answer for 12
  hours, so a reload paints instantly. The UI says which one served it:
  `Cached Qloo evidence` for the server, `Held in this browser` for the client.

Caching is what keeps the demo from spending the quota. When you add a
workflow, give it a payload builder and let it go through
`run_workflow_cached` — never call the CLI directly, or the answer will not
be held and the next run will pay for it again.

## Qloo live data — spend quota carefully

- The key lives in the Qloo CLI's private store (`~/.qloo/config`, mode 0600) and in the gitignored `.env`. **Never** commit it, print it, or put it in a tracked file.
- Hackathon keys work only against `https://hackathon.api.qloo.com` (set via `qloo config set base-url ...`). The wrong host returns 401.
- Rate and monthly limits are unpublished and reset monthly. Assume the quota is finite.
- `scripts/check_api.py` is read-only by default. Use `--live` to spend a request; never run it in a loop.
- `RUN_PROFILE` (`backend/config.py`) is the one switch. In `dev` (the default) the backend enforces a local budget (`QLOO_MAX_CALLS_PER_HOUR`, `QLOO_MAX_CALLS_PER_DAY`, default 20 and 100) checked *before* each request; a brief costs two calls. `judging` lifts every call-count budget, deliberately, and keeps the timeouts, the 429 cool-down, single-flight and the cache. Don't raise the dev caps to work around a failure, and don't switch profiles for that reason either.
- `QLOO_LIVE_ENABLED=false` is the kill switch: held evidence only, no new Qloo request.
- `scripts/prewarm.py` is read-only by default; `--live` fetches the prepared briefs in `shared/demoBriefs.json` through the serving instance. Run it deliberately, not in a loop.
- Prefer the held evidence over a new call — that is what the store and the
  browser cache are for. The mock provider is the test fixture, not a way to
  avoid the quota.
- Model calls via Vercel have a separate local budget (`LLM_MAX_CALLS_PER_HOUR`,
  `LLM_MAX_CALLS_PER_DAY`). Do not raise those limits to work around a failure.
- `scripts/qloo_exec.mjs` exists because the stock `qloo exec` client caps requests at 20s while `/v2/insights` needs ~25s, which turned every live request into three failed attempts. Keep using it rather than the raw `qloo` binary.

## Delegation protocol
- Do **not** spawn a subagent without explicit user permission, every time. No self-authorized escalation.
- When a task is difficult, ambiguous, or beyond this model's capability, stop and report back: state what was attempted, what is blocked, and why a higher-intelligence model would help.
- End that report with a direct request for permission to delegate, naming the agent role and the specific scope of work.
- Wait for an explicit yes. If the user says no, continue with the best available approach and state the remaining limitation.
- Delegation is for a well-scoped slice of work, not a blind handoff of the whole task.
