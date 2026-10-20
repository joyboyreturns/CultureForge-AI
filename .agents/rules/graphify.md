---
trigger: always_on
description: Consult the graphify knowledge graph at graphify-out/ for codebase and architecture questions.
---

## graphify

This project has a graphify knowledge graph at `graphify-out/` and an Obsidian vault of per-node notes at `CultureForge AI/`. Both are scoped retrieval sources — never load the raw graph, `GRAPH_REPORT.md`, or the whole vault into context.

Rules:
- For codebase or architecture questions, when `graphify-out/graph.json` exists, first run `graphify query "<question>" --budget 1500` (CLI) or `query_graph` (MCP). Use `graphify path "<A>" "<B>"` / `shortest_path` for relationships and `graphify explain "<concept>"` / `get_node` for focused concepts. These return a scoped subgraph, usually much smaller than `GRAPH_REPORT.md` or raw grep output.
- Prefer the MCP tools (`query_graph`, `get_node`, `get_neighbors`, `get_community`, `shortest_path`, `god_nodes`, `graph_stats`) with an explicit `token_budget` and, where useful, `context_filter` (e.g. `["call"]`).
- For a single node, read its Obsidian note: `python3 scripts/vault_query.py "<label>"` (add `--code` for the source excerpt). The note carries `source_file`, `location`, `community` and the node's connections — cheaper than grepping raw files.
- If `graphify-out/wiki/index.md` exists, navigate it instead of reading raw files.
- Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost), then `graphify export obsidian --dir "CultureForge AI"` to refresh the vault.
- Never remove `/CultureForge AI/` from `.graphifyignore`. The vault is an export, not an input; re-ingesting it feeds the graph its own output.
