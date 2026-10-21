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

## The free naming layer

`backend/llm.py` lets a free model name the directions. Three rules, and the
tests pin all three:

1. **The model writes words, never facts.** It is given the audience signals
   and the venues a direction is built from, and *no numbers at all* — so it
   cannot quote one. The rules keep the tags, the venues, the facet and the
   evidence. A number in the model's answer that Qloo did not return is
   dropped, and the rule engine's wording is used instead.
2. **Free only, and it stays free.** The fallback chain is free-only, because
   OpenRouter bills a paid model that appears in a `models` array. A paid
   `OPENROUTER_MODEL` is refused. The free tier is 50 requests a day, so the
   model is a cache: one call per brief, held in the evidence store, and a
   local guard (20/hour, 50/day) sits at the tier's own limit.
3. **Never on the critical path.** No key, no allowance, or a late answer and
   the rule engine's wording is used. The trace says which happened.
4. **Cap the thinking.** Most free models are reasoning models, and one given
   the whole token budget answers with nothing. The request caps
   `reasoning.max_tokens` and leaves the room the answer needs. A model that
   is gone (404), busy (429) or answers with nothing falls through to the
   next in the chain — and a field that says nothing (`...`) is dropped.
5. **Do not leave the routing to chance.** `openrouter/free` picks a free
   model at random, and some of them take twenty seconds to think. So a
   refusal is remembered (15 minutes for a rate limit, the day for a
   withdrawn model), the model the router actually chose is asked directly
   next time, and the models that answered well and quickly come first. The
   switch is a local file read, so it is instant; one attempt is capped at
   fourteen seconds and the whole naming at twenty-two.

A failure is never held: an empty naming is discarded from the evidence
store, so the next run tries again instead of being told for a day that the
brief has no name.

If you add to it: give it a payload builder, hold the answer in the evidence
store like everything else, and keep the rule engine's wording available as
the fallback.

## Caching, and what it costs

Two caches, both holding real answers:

- **The server's evidence store** (`backend/evidence_store.py`) keeps every
  workflow envelope on disk for 24 hours, keyed by the canonical workflow
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
- The backend enforces a local budget (`QLOO_MAX_CALLS_PER_HOUR`, `QLOO_MAX_CALLS_PER_DAY`) checked *before* each request. A brief costs two calls, so the current caps (30 an hour, 150 a day) are fifteen briefs an hour and seventy-five a day for a room of judges. Don't raise them to work around a failure.
- Prefer the held evidence over a new call — that is what the store and the
  browser cache are for. The mock provider is the test fixture, not a way to
  avoid the quota.
- The free model has its own budget (`LLM_MAX_CALLS_PER_HOUR`,
  `LLM_MAX_CALLS_PER_DAY`) and its own free-only chain. Don't raise those
  either, and never put a paid model in the chain.
- `scripts/qloo_exec.mjs` exists because the stock `qloo exec` client caps requests at 20s while `/v2/insights` needs ~25s, which turned every live request into three failed attempts. Keep using it rather than the raw `qloo` binary.

## Delegation protocol
- Do **not** spawn a subagent without explicit user permission, every time. No self-authorized escalation.
- When a task is difficult, ambiguous, or beyond this model's capability, stop and report back: state what was attempted, what is blocked, and why a higher-intelligence model would help.
- End that report with a direct request for permission to delegate, naming the agent role and the specific scope of work.
- Wait for an explicit yes. If the user says no, continue with the best available approach and state the remaining limitation.
- Delegation is for a well-scoped slice of work, not a blind handoff of the whole task.
