#!/usr/bin/env bash
# graphify_mcp.sh - start the graphify MCP server for this project.
#
# Portable wrapper: resolves the graphify interpreter for the current machine
# instead of hardcoding an absolute path, then serves the local knowledge graph
# over MCP stdio. Used by opencode.json -> mcp.servers.cultureforge-graph.
#
# Requirements: graphify installed (`uv tool install graphifyy --with mcp`),
# and a graph built at graphify-out/graph.json
# (run `graphify update .` if it is missing).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/graphify-out"
GRAPH="$OUT/graph.json"

if [[ ! -f "$GRAPH" ]]; then
  echo "graphify_mcp.sh: no graph at $GRAPH - run 'graphify update .' first" >&2
  exit 1
fi

# 1. Interpreter pinned by a previous graphify run (most reliable).
PY=""
if [[ -f "$OUT/.graphify_python" ]]; then
  CANDIDATE="$(cat "$OUT/.graphify_python" 2>/dev/null || true)"
  if [[ -n "$CANDIDATE" && -x "$CANDIDATE" ]]; then
    PY="$CANDIDATE"
  fi
fi

# 2. Shebang of the graphify binary (uv tool / pipx / system install).
if [[ -z "$PY" ]]; then
  BIN="$(command -v graphify 2>/dev/null || true)"
  if [[ -n "$BIN" ]]; then
    CANDIDATE="$(head -1 "$BIN" | tr -d '#!')"
    if [[ "$CANDIDATE" != *[!a-zA-Z0-9/_.@-]* && -x "$CANDIDATE" ]]; then
      PY="$CANDIDATE"
    fi
  fi
fi

# 3. Fall back to uv, which can materialise the tool on demand.
if [[ -z "$PY" ]]; then
  PY="$(uv tool run --from graphifyy python -c 'import sys; print(sys.executable)' 2>/dev/null || true)"
fi

if [[ -z "$PY" || ! -x "$PY" ]]; then
  echo "graphify_mcp.sh: could not locate a graphify interpreter." >&2
  echo "  install with: uv tool install graphifyy --with mcp" >&2
  exit 1
fi

# The MCP server needs the 'mcp' package in the same environment.
if ! "$PY" -c 'import mcp' >/dev/null 2>&1; then
  echo "graphify_mcp.sh: 'mcp' missing from $PY - run: uv tool install graphifyy --with mcp --force" >&2
  exit 1
fi

exec "$PY" -m graphify.serve "$GRAPH"
