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
| `backend/providers.py` | The Qloo provider. One request builder per workflow, because Qloo rejects fields it does not know. |
| `backend/investigation.py` | The decision loop: the questions a direction has not answered, each one a named workflow. |
| `backend/platform.py` | The licensable layer: workspaces, issued keys, saved explorations, metering. SQLite. |
| `backend/evidence_store.py` | The durable evidence cache. A held answer costs nothing; a failure is never cached. |
| `backend/concept_composer.py` | The rules that turn evidence into directions. Every proposal names its evidence. |
| `src/wildroot.css` | The editorial layer. Imported last, so it wins over the dashboard styles. |

Three rules the codebase holds to, and the tests pin them:

1. **Never show a number Qloo did not return.** No invented fit scores, and no
   borrowed durations — a reused step reports zero and states the original.
2. **Never let a malformed request through.** Every route that takes a body
   takes a typed one, so a string where a list was meant is a 422.
3. **Never fail silently.** A rate limit or an exhausted budget becomes a
   stated limitation in the report, not a crash and not a blank panel.

## Qloo live data — spend quota carefully

- The key lives in the Qloo CLI's private store (`~/.qloo/config`, mode 0600) and in the gitignored `.env`. **Never** commit it, print it, or put it in a tracked file.
- Hackathon keys work only against `https://hackathon.api.qloo.com` (set via `qloo config set base-url ...`). The wrong host returns 401.
- Rate and monthly limits are unpublished and reset monthly. Assume the quota is finite.
- `scripts/check_api.py` is read-only by default. Use `--live` to spend a request; never run it in a loop.
- The backend enforces a local budget (`QLOO_MAX_CALLS_PER_HOUR`, `QLOO_MAX_CALLS_PER_DAY`) checked *before* each request. Don't raise the limits to work around a failure.
- Prefer the mock provider for anything that does not need live signals — it makes zero API calls.
- `scripts/qloo_exec.mjs` exists because the stock `qloo exec` client caps requests at 20s while `/v2/insights` needs ~25s, which turned every live request into three failed attempts. Keep using it rather than the raw `qloo` binary.

## Delegation protocol
- Do **not** spawn a subagent without explicit user permission, every time. No self-authorized escalation.
- When a task is difficult, ambiguous, or beyond this model's capability, stop and report back: state what was attempted, what is blocked, and why a higher-intelligence model would help.
- End that report with a direct request for permission to delegate, naming the agent role and the specific scope of work.
- Wait for an explicit yes. If the user says no, continue with the best available approach and state the remaining limitation.
- Delegation is for a well-scoped slice of work, not a blind handoff of the whole task.
