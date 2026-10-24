# CultureForge AI — demo video: edit order and narration

Total: **2 min 48 s** of picture. Eight clips, already trimmed, in `clips/`. Put them on the timeline in
this order, with no gaps. Each clip has no audio; lay the AI voice over it.

Everything on screen is the real app running the held Tokyo bakery example (Qloo evidence returned
earlier, model layer on, held agent report). Nothing is mocked and no new Qloo request was made while
recording. The clips are 1920×1080, 30 fps, H.264.

| # | File | Length | What is on screen | Voice-over (read it exactly) |
|---|------|--------|-------------------|------------------------------|
| 1 | `01-landing.mp4` | 22.7 s | Landing page, slow scroll | **Every business idea starts as a guess about what people in a place will love. CultureForge AI puts that guess on trial. Describe an idea, an audience and a city. We ask Qloo what that audience actually gravitates to there, then turn those signals into directions you can challenge.** |
| 2 | `02-studio.mp4` | 18.0 s | Studio, click "Run the example brief", executive brief | **Here's a real brief: an artisan bakery in Tokyo for early-morning commuters. This demo replays evidence Qloo returned earlier, so it opens instantly. Every claim traces to a real Qloo place or tag, never an invented score.** |
| 3 | `03-places.mp4` | 12.0 s | Places & signals, Qloo photos and numbers | **Real places Qloo returned, with its own photos and numbers. A language model can describe a bakery; only Qloo knows which ones this audience connects to.** |
| 4 | `04-directions.mp4` | 11.0 s | Two directions with photos, citations, limits | **From that evidence, CultureForge composes directions. Each names the places it rests on, what it claims, and what remains unproven.** |
| 5 | `05-map.mp4` | 36.0 s | Interest map, click a venue, "What happens without this evidence?" | **Now the same evidence on a real map. Venues are pinned from the addresses Qloo returned, and the panel says exactly how each pin was matched. Pick a venue and see why it's connected to this audience. Then ask the hard question: what happens without it? Remove this bakery, and the directions are rebuilt from what's left, using held evidence, with no new Qloo request. What changed is shown, and what survives.** |
| 6 | `06-test.mp4` | 30.5 s | Evidence test runs, "contested. The order changed." | **A tool that always agrees is decoration, so this one can say no. The evidence test asks Qloo to rank the same places for a demographic profile, then compares the anchor's tags with every other place. Here, the lead direction's anchor lands in the bottom third. The verdict: contested, and the order of directions changes. It's a verdict about anchor fit in this sample, not about demand.** |
| 7 | `07-agent.mp4` | 25.7 s | Decision: agent steps, refused steps, cited analysis | **Behind it, a bounded agent plans up to eight steps over approved Qloo workflows: tags, audiences, comparisons. Steps citing anything it hasn't observed are refused, and shown as refused. The final analysis must cite Qloo IDs from this run, and says what remains unproven. If the model fails, the rule-based answer stands, and says so.** |
| 8 | `08-close.mp4` | 12.2 s | Landing hero, cursor to "Try the demo" | **CultureForge AI: Qloo's cultural intelligence, used as evidence that can disagree with your idea. Open source, nine Qloo workflows, and a demo you can try yourself.** |

Word count is about 365, which a normal AI voice reads in roughly 2 min 30 s at a natural pace. That
leaves about 18 s of breathing room, so the voice does not need to be sped up.

## Edit notes

- **Voice:** generate each paragraph as its own audio file and place it at the start of its clip. If a
  line runs a little short or long, nudge the audio, not the picture. If a line runs more than ~1.5 s long,
  slow the clip to 90% before cutting words.
- **Pronunciation:** "Qloo" is *"clue"*. If your voice says it wrongly, write it as "Clue" in the TTS text
  only, never on screen.
- **Captions:** burn the narration in as captions. Judges often watch muted.
- **Title card (optional, 3 s before clip 1):** "CultureForge AI — Qloo Agentic Hackathon 2026".
- **End card (optional, 4 s after clip 8):** your public demo URL and the GitHub URL
  (`github.com/joyboyreturns/CultureForge-AI`). Add the demo URL only once it is live.
- **Music:** none, or royalty-free quiet and low. Check the rules for third-party audio. Do not add any
  sound effects over the narration.
- **Do not** add claims the picture does not show, such as demand, revenue, "supported" verdicts, or
  numbers. The evidence test in this recording returned **contested** and **unproven**, and that is the
  honest result; keep it.

## What the clips do not show (say it if asked)

- The first run of a brand-new brief takes about two minutes, mostly from the model gateway's rate limit.
  The video starts from held evidence on purpose. The landing and studio say this evidence is "held".
- The map pins are address or name matches from OpenStreetMap, not surveyed points. The panel says so.
- The evidence-test verdict is about anchor fit within the retrieved places only.

## Re-recording

`tools/record.cjs` (Playwright; it borrows the copy in `~/Documents/AccessRipple/node_modules`) records the
clips from a running studio, and `tools/convert.sh` trims and encodes them. Start the backend with
`QLOO_LIVE_ENABLED=false`, a `vite preview` pointed at it with `CULTUREFORGE_API_TARGET`, and set `BASE`.
Then: `node tools/record.cjs <outDir> [clip ...]`. To redo a clip, ask for it by name.
