# CultureForge AI — demo video: edit order and narration

Total: **3 min 45 s** of picture. Twelve clips, already trimmed and numbered in `clips/`. Put them on the
timeline in file order, with no gaps. The clips have no audio; lay the AI voice over them.

- **Screen clips** (landing, studio, places, directions, map, test, agent, close) are the real app running
  the held Tokyo bakery example: Qloo evidence returned earlier, model layer on, held agent report. Nothing
  is mocked and no new Qloo request was made while recording.
- **Diagram clips** (`*-diagram-*`) are four animated explainers drawn in the studio's own colours. Every
  label comes from the README and `docs/EVIDENCE_POLICY.md`; they claim nothing the product does not do.
  Peach = returned by Qloo, lavender = decided by rules, mint = written by the model (optional).

All clips are 1920×1080, 30 fps, H.264.

| # | File | Length | On screen |
|---|------|--------|-----------|
| 1 | `01-landing.mp4` | 22.7 s | Landing page, slow scroll |
| 2 | `02-diagram-compare.mp4` | 13.3 s | **Diagram:** an ordinary language model vs CultureForge on Qloo |
| 3 | `03-studio.mp4` | 18.0 s | Studio, "Run the example brief", executive brief |
| 4 | `04-places.mp4` | 12.0 s | Places & signals, Qloo photos and numbers |
| 5 | `05-directions.mp4` | 11.0 s | Two directions with photos, citations, limits |
| 6 | `06-diagram-pipeline.mp4` | 15.3 s | **Diagram:** from a brief to a verdict |
| 7 | `07-map.mp4` | 36.0 s | Interest map, click a venue, "What happens without this evidence?" |
| 8 | `08-diagram-verdict.mp4` | 15.3 s | **Diagram:** how the evidence test can say no |
| 9 | `09-test.mp4` | 30.5 s | Evidence test runs, "contested. The order changed." |
| 10 | `10-agent.mp4` | 25.7 s | Decision: agent steps, refused steps, cited analysis |
| 11 | `11-diagram-layers.mp4` | 13.3 s | **Diagram:** three layers kept apart |
| 12 | `12-close.mp4` | 12.2 s | Landing hero, cursor to "Try the demo" |

**The words to read are in `VOICEOVER.md`** (ElevenLabs-ready, with pauses and the exact time to place each audio
file) and **`CAPTIONS.md`** (the same words with the real spellings, for burned-in captions). They replace the
narration that used to be in this file. The voice text is about 420 words and is timed (for Adam at speed 0.85) so that every clip keeps at
least 1 s of silence at the end.

## If you need it shorter

3:45 is long for a hackathon video. Each cut below is clean (the narration for the neighbours still makes
sense):

| Cut | Saves | New total |
|-----|-------|-----------|
| Drop `11-diagram-layers` | 13 s | 3:32 |
| …and `06-diagram-pipeline` | 15 s | 3:17 |
| …and `04-places` + `05-directions` | 23 s | 2:54 |

Keep `02-diagram-compare` (the hook) and `08-diagram-verdict` (the proof the test can say no) whatever you
cut. If you drop `11`, move its last sentence ("If the model fails or is switched off, the rule-based answer
stands, and says so") onto the end of clip 10's voice-over.

## Edit notes

- **Voice:** generate each paragraph as its own audio file and place it at the start of its clip. If a
  line runs a little long, nudge the audio rather than the picture; if it is more than ~1.5 s long, slow
  that clip to 90%. The diagrams build in steps, so start the voice about 0.5 s in.
- **Pronunciation:** "Qloo" is *"clue"*. If your voice says it wrongly, write it as "Clue" in the TTS text
  only, never on screen.
- **Captions:** burn the narration in as captions. Judges often watch muted.
- **Transitions:** a 0.3 s cross-dissolve between a screen clip and a diagram clip looks cleanest. Nothing
  fancier is needed.
- **Title card (optional, 3 s before clip 1):** "CultureForge AI — Qloo Agentic Hackathon 2026".
- **End card (optional, 4 s after clip 12):** your public demo URL and
  `github.com/joyboyreturns/CultureForge-AI`. Add the demo URL only once it is live.
- **Music:** none, or royalty-free and low. Check the rules for third-party audio.
- **Do not** add claims the picture does not show, such as demand, revenue, "supported" verdicts, or
  numbers. The evidence test in this recording returned **contested** and **unproven**, and that is the
  honest result; keep it.

## What the clips do not show (say it if asked)

- The first run of a brand-new brief takes about two minutes, mostly from the model gateway's rate limit.
  The video starts from held evidence on purpose, and says so.
- The map pins are address or name matches from OpenStreetMap, not surveyed points. The panel says so.
- The evidence-test verdict is about anchor fit within the retrieved places only.
- The diagrams are simplified: the real pipeline has more branches (caching, a kill switch, run profiles).
  See the README and `docs/ARCHITECTURE.md`.

## Re-recording or editing

- `tools/record.cjs` records the screen clips from a running studio; `tools/record_diagrams.cjs` records the
  diagram scenes; `tools/convert.sh` trims and encodes the screen clips. They borrow Playwright from
  `~/Documents/AccessRipple/node_modules`.
- `diagrams/diagrams.html` holds the four scenes as data (`SCENES`): change a label, a time or a colour
  there and re-run `node tools/record_diagrams.cjs <outDir> [compare|pipeline|verdict|layers]`.
- Start the backend with `QLOO_LIVE_ENABLED=false`, a `vite preview` pointed at it with
  `CULTUREFORGE_API_TARGET`, and set `BASE` for the screen clips.
