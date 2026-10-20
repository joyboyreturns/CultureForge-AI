---
tags:
  - cultureforge
  - graphify
---

# Graphify workflow for CultureForge AI

Use the Graphify graph as a compact index before opening lots of source files. The current benchmark estimates about **2,200 tokens per query** versus **17,266 tokens** for a naive full-corpus read (about **7.8× fewer** for the benchmark questions). These are estimates, not a guarantee for every question.

## Ask focused questions

From the project folder, run:

```sh
graphify query "what connects the data layer to the API" --budget 1500
graphify path "App()" "CultureProvider"
graphify explain "QlooHarnessProvider"
```

Start with a specific question and a small budget. If results are sparse, use terms from node labels in `graphify-out/graph.json`. Open only the source files that the graph points to when you need exact implementation details or are changing code.

In Antigravity, the project also exposes the graph through the `cultureforge-graph` MCP server. Ask it a focused question and use `query_graph` or `get_node` to retrieve only the relevant part of the map. The workspace rule tells Antigravity not to load the full graph or vault into context.

## Keep it current

After substantial code or documentation changes, refresh the graph from the project root:

```sh
graphify . --update
graphify export obsidian --dir "CultureForge AI"
```

The graph and its notes help navigate the project; source files remain the authority for current behavior.

## Browse this vault

Explore the generated graph notes and `graph.canvas` in Obsidian. Useful starting points include [[App()]], [[CultureProvider]], [[QlooHarnessProvider]], and [[CultureForge AI Prototype]].
