#!/usr/bin/env python3
"""vault_query.py - scoped retrieval over the CultureForge Obsidian vault.

The vault is a first-class retrieval source, not just a browsing surface.
Every note carries YAML frontmatter (source_file, type, community, location)
and a `## Connections` list of wikilinks, so one note is enough to orient
around a node and jump straight to its real source location.

Stdlib only. Nothing here loads the whole vault into context.

Usage:
  vault_query.py "<label>"              # best-match note, compact
  vault_query.py "<label>" --code       # ...plus the source excerpt at its location
  vault_query.py --search "<text>"      # content search across notes
  vault_query.py --source "<path>"      # every note derived from a source file
  vault_query.py --list [--community X] # note index
  vault_query.py --stats                # vault statistics

Options:
  --max-chars N   output cap (default 2400)
  --json          machine-readable output
  --limit N       max notes returned for --search/--source (default 10)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "CultureForge AI"
CACHE = ROOT / "graphify-out" / "cache" / "vault_index.json"

FM_RE = re.compile(r"^---\n(.*?)\n---\n?", re.S)
KV_RE = re.compile(r'^([A-Za-z_][\w-]*):\s*(.*)$')
LOC_RE = re.compile(r"^L(\d+)(?:\s*-\s*L?(\d+))?$")


# --------------------------------------------------------------------------- #
# index
# --------------------------------------------------------------------------- #
def _parse_frontmatter(raw: str) -> dict:
    """Minimal YAML-subset reader: scalars, inline lists, and `- item` blocks."""
    meta: dict = {}
    key = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if line.startswith(("  - ", "- ")):
            if key:
                meta.setdefault(key, [])
                if isinstance(meta[key], list):
                    meta[key].append(line[2:].strip().strip("\"'"))
            continue
        m = KV_RE.match(line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val.startswith("[") and val.endswith("]"):
            meta[key] = [v.strip().strip("\"'") for v in val[1:-1].split(",") if v.strip()]
        elif val:
            meta[key] = val.strip("\"'")
        else:
            meta[key] = []
    return meta


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _build_index() -> dict:
    notes: dict = {}
    if not VAULT.is_dir():
        return {"vault": str(VAULT), "exists": False, "notes": {}}

    for path in sorted(VAULT.glob("*.md")):
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        fm_match = FM_RE.match(raw)
        meta = _parse_frontmatter(fm_match.group(1)) if fm_match else {}
        body = raw[fm_match.end():] if fm_match else raw

        title = ""
        t = re.search(r"^#\s+(.+)$", body, re.M)
        if t:
            title = t.group(1).strip()

        conns = []
        in_conn = False
        for line in body.splitlines():
            if line.startswith("## "):
                in_conn = line.strip().lower().startswith("## connections")
                continue
            if not in_conn:
                continue
            c = re.match(r"^-\s*\[\[(.+?)\]\]\s*[-—]?\s*`?([A-Za-z_]+)?`?", line)
            if c:
                conns.append({"target": c.group(1), "rel": c.group(2) or ""})

        notes[path.stem] = {
            "file": path.name,
            "title": title or path.stem,
            "source_file": meta.get("source_file", ""),
            "type": meta.get("type", ""),
            "community": meta.get("community", ""),
            "location": meta.get("location", ""),
            "tags": meta.get("tags", []),
            "connections": conns,
            "body": body.strip(),
            "size": path.stat().st_size,
        }

    return {
        "vault": str(VAULT),
        "exists": True,
        "count": len(notes),
        "notes": notes,
    }


def load_index(force: bool = False) -> dict:
    """Cached index, rebuilt when the vault changes."""
    try:
        vault_mtime = VAULT.stat().st_mtime
    except OSError:
        vault_mtime = 0

    if not force and CACHE.is_file():
        try:
            cached = json.loads(CACHE.read_text(encoding="utf-8"))
            if cached.get("vault_mtime") == vault_mtime:
                return cached
        except (OSError, json.JSONDecodeError, KeyError):
            pass

    idx = _build_index()
    idx["vault_mtime"] = vault_mtime
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(idx, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return idx


# --------------------------------------------------------------------------- #
# matching
# --------------------------------------------------------------------------- #
def _score(query: str, note: dict) -> float:
    q = query.lower()
    label = note["title"].lower()
    if label == q:
        return 1000.0
    if _norm(label) == _norm(query):
        return 900.0
    if q in label:
        return 500.0 + len(label) - len(q)
    if _norm(query) and _norm(query) in _norm(label):
        return 400.0
    blob = " ".join(
        [note["title"], note["source_file"], note["community"], note["type"]]
        + [c["target"] for c in note["connections"]]
    ).lower()
    if q in blob:
        return 150.0
    if _norm(query) and _norm(query) in _norm(blob):
        return 100.0
    return 0.0


def find_notes(query: str, idx: dict, limit: int = 10) -> list:
    scored = []
    for label, note in idx.get("notes", {}).items():
        s = _score(query, note)
        if s > 0:
            scored.append((s, label, note))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [(lbl, n) for _, lbl, n in scored[:limit]]


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #
def _code_excerpt(note: dict, before: int = 2, after: int = 6) -> str:
    src = note.get("source_file")
    loc = note.get("location") or ""
    if not src or not loc:
        return ""
    m = LOC_RE.match(loc.strip())
    if not m:
        return ""
    path = ROOT / src
    if not path.is_file():
        return ""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    start = max(1, int(m.group(1)) - before)
    end = int(m.group(2)) if m.group(2) else int(m.group(1)) + after
    end = min(end, len(lines))
    if start > len(lines):
        return ""
    out = [f"--- {src} L{start}-{end} ---"]
    for i in range(start, end + 1):
        out.append(f"{i:>5} | {lines[i - 1]}")
    return "\n".join(out)


def render_note(label: str, note: dict, max_chars: int, with_code: bool) -> str:
    out: list[str] = []
    meta_bits = []
    for k in ("source_file", "location", "type", "community"):
        v = note.get(k)
        if v:
            meta_bits.append(f"{k}={v}")
    out.append(f"# {note['title']}   ({', '.join(meta_bits)})")
    out.append(f"note: CultureForge AI/{note['file']}")

    conns = note.get("connections", [])
    if conns:
        out.append(f"## Connections ({len(conns)})")
        for c in conns:
            out.append(f"  - {c['target']}  ({c['rel']})")

    if with_code:
        code = _code_excerpt(note)
        if code:
            out.append("## Source")
            out.append(code)

    text = "\n".join(out)
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n...[truncated at {max_chars} chars]"
    return text


def render_search(matches: list, idx: dict, max_chars: int) -> str:
    out: list[str] = [f"vault search: {len(matches)} note(s)"]
    for label, note in matches:
        out.append("")
        out.append(f"--- {label}  [{note.get('community','')}]  {note.get('source_file','')}")
        body = note.get("body", "")
        body = re.sub(r"^#\s+.*$", "", body, count=1, flags=re.M)
        body = re.sub(r"^#graphify/.*$", "", body, flags=re.M)
        body = body.strip()
        out.append(body[:600] if body else "(empty)")

    text = "\n".join(out)
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n...[truncated at {max_chars} chars]"
    return text


def render_list(idx: dict, community: str | None, max_chars: int) -> str:
    notes = idx.get("notes", {})
    if community:
        notes = {k: v for k, v in notes.items() if v.get("community", "").lower() == community.lower()}
    grouped: dict = {}
    for label, note in notes.items():
        grouped.setdefault(note.get("community") or "(ungrouped)", []).append(label)
    out = []
    for comm in sorted(grouped):
        out.append(f"## {comm} ({len(grouped[comm])})")
        out.append("  " + ", ".join(sorted(grouped[comm])))
    text = "\n".join(out)
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n...[truncated at {max_chars} chars]"
    return text


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(add_help=True, description=__doc__)
    ap.add_argument("query", nargs="?", help="note label to look up")
    ap.add_argument("--search", metavar="TEXT", help="search note contents")
    ap.add_argument("--source", metavar="PATH", help="notes derived from a source file")
    ap.add_argument("--list", action="store_true", help="list the note index")
    ap.add_argument("--stats", action="store_true", help="vault statistics")
    ap.add_argument("--community", metavar="NAME", help="filter --list by community")
    ap.add_argument("--code", action="store_true", help="include the source excerpt")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--max-chars", type=int, default=2400, help="output cap")
    ap.add_argument("--limit", type=int, default=10, help="max notes returned")
    ap.add_argument("--rebuild", action="store_true", help="force index rebuild")
    args = ap.parse_args()

    idx = load_index(force=args.rebuild)
    if not idx.get("exists"):
        print(f"vault not found at {VAULT}", file=sys.stderr)
        return 2

    notes = idx.get("notes", {})

    if args.stats:
        comms: dict = {}
        for n in notes.values():
            comms[n.get("community") or "(ungrouped)"] = comms.get(n.get("community") or "(ungrouped)", 0) + 1
        if args.json:
            print(json.dumps({"notes": len(notes), "communities": comms}, indent=2))
        else:
            print(f"vault: {VAULT}")
            print(f"notes: {len(notes)}  communities: {len(comms)}")
            for c, k in sorted(comms.items(), key=lambda x: -x[1]):
                print(f"  {k:>4}  {c}")
        return 0

    if args.list:
        if args.json:
            sel = (
                {k: v for k, v in notes.items() if not args.community or v.get("community", "").lower() == args.community.lower()}
                if args.community
                else notes
            )
            print(json.dumps(sel, indent=2, ensure_ascii=False))
        else:
            print(render_list(idx, args.community, args.max_chars))
        return 0

    if args.source:
        q = args.source.replace("\\", "/")
        matches = [
            (lbl, n)
            for lbl, n in notes.items()
            if n.get("source_file", "").replace("\\", "/").endswith(q) or q in n.get("source_file", "")
        ]
        matches.sort(key=lambda x: x[0])
        if args.json:
            print(json.dumps([{ "label": l, **n} for l, n in matches], indent=2, ensure_ascii=False))
        else:
            print(f"source {args.source}: {len(matches)} note(s)")
            for lbl, n in matches:
                print(f"  {lbl}  [{n.get('community','')}]  {n.get('location','')}")
        return 0

    if args.search:
        term = args.search.lower()
        hits = []
        for lbl, n in notes.items():
            body = n.get("body", "").lower()
            if term in body or term in lbl.lower():
                hits.append((lbl, n))
        hits.sort(key=lambda x: -_score(args.search, x[1]))
        hits = hits[: args.limit]
        if args.json:
            print(json.dumps([{ "label": l, **n} for l, n in hits], indent=2, ensure_ascii=False))
        else:
            print(render_search(hits, idx, args.max_chars))
        return 0

    if args.query:
        matches = find_notes(args.query, idx, limit=max(1, args.limit))
        if not matches:
            print(f"no vault note matches {args.query!r}", file=sys.stderr)
            return 4
        label, note = matches[0]
        if args.json:
            print(json.dumps({"label": label, **note}, indent=2, ensure_ascii=False))
        else:
            print(render_note(label, note, args.max_chars, args.code))
            if len(matches) > 1:
                others = ", ".join(l for l, _ in matches[1:6])
                print(f"\nother matches: {others}")
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
