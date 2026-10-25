import re, sys
SEC_PER_WORD = 0.35 / 0.85   # measured: Adam at speed 1.00 read 48 words + 1.2 s of pauses in 18.0 s (0.35 s/word, 171 wpm); scaled to speed 0.85
# (file, clip length s, [(place-at s, [text | pause seconds ...])])
CLIPS = [
 ("01-landing.mp4", 22.7, "Landing page, slow scroll", [(0.4, [
   "Every business idea starts as a guess about what people in a place will love.", .4,
   "Culture Forge A.I. puts that guess on trial.", .4,
   "Describe an idea, an audience, and a city.", .4,
   "We ask Clue what that audience gravitates to, then turn those signals into directions you can challenge."])]),
 ("02-diagram-compare.mp4", 13.3, "Diagram: ordinary model vs CultureForge on Qloo", [(0.5, [
   "Ask a language model about a bakery, and you get fluent text with no sources.", .5,
   "Here, every direction must point back to evidence Clue returned."])]),
 ("03-studio.mp4", 18.0, "Studio, run the example, executive brief", [(0.5, [
   "Here's a real brief: an artisan bakery in Tokyo, for early-morning commuters.", .5,
   "This demo replays evidence Clue returned earlier, so it opens instantly.", .5,
   "Every claim traces to a Clue place or tag, never an invented score."])]),
 ("04-places.mp4", 12.0, "Places and signals, Qloo photos and numbers", [(0.5, [
   "Real places Clue returned, with its own photos and numbers.", .4,
   "The figures are Clue's. The page says what it could not verify."])]),
 ("05-directions.mp4", 11.0, "Two directions with citations and limits", [(0.5, [
   "From that evidence, Culture Forge composes directions.", .4,
   "Each names the places it rests on, what it claims, and what remains unproven."])]),
 ("06-diagram-pipeline.mp4", 15.3, "Diagram: from a brief to a verdict", [(0.7, [
   "Under the hood: Clue returns places, tags, and audiences.", .3,
   "Rules compose cited directions.", .3,
   "An optional model step comes last, and a validator rejects any claim without a Clue I.D."])]),
 ("07-map.mp4", 36.0, "Interest map, pick a venue, remove it", [
  (0.6, ["Now, the same evidence on a real map.", .8, "Venues are pinned from the addresses Clue returned."]),
  (11.6, ["Pick a venue,", .3, "and the panel says exactly how its pin was matched, and why it's connected to this audience."]),
  (21.0, ["Then ask the hard question: what happens without it?", .6,
          "Remove this bakery, and the directions are rebuilt from held evidence, with no new Clue request.", .4,
          "What changed is shown."])]),
 ("08-diagram-verdict.mp4", 15.3, "Diagram: how the evidence test can say no", [(0.4, [
   "A tool that always agrees is decoration. This test has three outcomes.", .4,
   "Both checks pass: supported.", .3,
   "A check is missing: unproven.", .3,
   "A check fails: contested.", .3,
   "Re-anchor, and test again."])]),
 ("09-test.mp4", 30.5, "Evidence test runs: contested, order changed", [(0.6, [
   "Let's run it on this brief.", .6,
   "Clue ranks the places, then compares their tags.", .5,
   "The lead direction's anchor lands in the bottom third of the places Clue ranked, so the verdict is", .3,
   "contested. And the order of directions changes.", .8,
   "It's a verdict about anchor fit in this sample, not about demand."])]),
 ("10-agent.mp4", 25.7, "Agent steps, refused steps, cited analysis", [(0.6, [
   "Behind it, a bounded agent plans up to eight steps over approved Clue workflows: tags, audiences, comparisons.", .5,
   "A step that cites anything it hasn't observed is refused, and shown as refused.", .5,
   "The final analysis must cite Clue I.D.s from this run, and says what remains unproven."])]),
 ("11-diagram-layers.mp4", 13.3, "Diagram: three layers kept apart", [(0.4, [
   "Three layers, kept apart:", .3, "what Clue returned,", .3, "what rules decided,", .3, "and what a model wrote.", .5,
   "If the model fails, the rule-based answer stands."])]),
 ("12-close.mp4", 12.2, "Landing hero, cursor to Try the demo", [(0.5, [
   "Culture Forge A.I.: Clue's cultural intelligence, as evidence that can disagree with your idea.", .4,
   "Open source. Nine Clue workflows. Try the demo."])]),
]
def words(t): return len(re.findall(r"[A-Za-z0-9'’]+", t.replace('A.I.', 'AI')))
def est(parts): return sum(words(p)*SEC_PER_WORD if isinstance(p, str) else p for p in parts)
def tts(parts):
    out = []
    for p in parts:
        if isinstance(p, str): out.append(p)
        else: out.append(f'<break time="{p:.1f}s" />')
    return ' '.join(out)
def clean(parts):   # for captions: real spellings, no pauses
    t = ' '.join(p for p in parts if isinstance(p, str))
    t = t.replace('Culture Forge A.I.', 'CultureForge AI').replace('Culture Forge', 'CultureForge').replace('Clue', 'Qloo').replace('I.D.s', 'IDs').replace('I.D.', 'ID')
    return t
rows = []; bad = []
for fn, dur, desc, segs in CLIPS:
    row = []
    for at, parts in segs:
        e = est(parts); row.append((at, e, parts))
    end = max(at + e for at, e, _ in row); slack = dur - end
    rows.append((fn, dur, desc, row, end, slack))
    if slack < 1.0: bad.append((fn, slack))
    for (a1, e1, _), (a2, _, _) in zip(row, row[1:]):
        if a1 + e1 > a2 - 0.3: bad.append((fn, 'segments overlap'))
total_words = sum(words(clean(p).replace('CultureForge AI','CultureForge A I')) for *_, segs in CLIPS for _, p in segs)

md = ["# CultureForge AI — ElevenLabs voice-over (Adam)", "",
 "Clip order is the file order in `clips/` (01 → 12, about 3:45). Each block below is **one audio file**: paste the text",
 "exactly as shown (the `<break … />` tags are pauses), generate it, then place the audio on the timeline at the",
 "**Place at** time. Clip 7 has three blocks, because the map needs time to load between them.", "",
 "## Settings for Adam", "",
 "| Setting | Value |", "|---|---|",
 "| Model | **Multilingual v2** (or Turbo v2.5). `<break>` tags work on both. *Not* Eleven v3, which ignores them: there, replace each break with ` ... ` |",
 "| Stability | 60 (steady, announcer-like; lower sounds more dramatic and less consistent between clips) |",
 "| Similarity | 80 |", "| Style exaggeration | 10 (higher can make Adam over-act) |",
 "| Speaker boost | On |", "| Speed | **0.85** for every clip (measured, see below) |", "",
 "## Spelling used in the voice text (so Adam says it right)", "",
 "- **Qloo → \"Clue\"** (that is how it is pronounced). Use the real spelling in captions: see `CAPTIONS.md`.",
 "- **CultureForge AI → \"Culture Forge A.I.\"**, **IDs → \"I.D.s\"**.",
 "- Pauses: commas are a short breath; `<break time=\"0.4s\" />` is a clean beat; a longer one (0.8 s) is placed before a key",
 "  idea. There are no filler sounds (\"um\", \"hmm\"): on a judging video they read as unsure. Ask if you want them.", "",
 "## Pace (measured)", "",
 "Adam at speed 1.00 read clip 1 in **18.0 s**: 48 words plus 1.2 s of pauses, about 171 words a minute. That is faster than the",
 "clip needs, so every block below is timed for **speed 0.85** (about 145 words a minute). Use the same speed on all twelve clips",
 "so the voice sounds consistent.", "",
 "Generate clip 1 again at 0.85. It should come out near **21 s**. Then:", "",
 "- Within ±1 s of the *Voice length* shown: carry on with the rest.",
 "- Still too short: try 0.80, but check the tightest clips (see the slack line under each block).",
 "- Too long: use 0.90.",
 "- Anything else: tell me the length and I will rescale every block.", "",
 "Slack is the silence left at the end of the clip. Every clip keeps at least 1 s of slack at 0.85, and the pauses are fixed",
 "lengths, so they do not change with speed.", "", "---", ""]
for i, (fn, dur, desc, row, end, slack) in enumerate(rows, 1):
    md += [f"## {i}. `{fn}` — {dur:.1f} s", f"*On screen: {desc}.*", ""]
    for j, (at, e, parts) in enumerate(row):
        label = f" — block {'ABC'[j]}" if len(row) > 1 else ""
        md += [f"**Place at {at:.1f} s{label}** · voice length ≈ {e:.1f} s" + (f" · ends ≈ {at+e:.1f} s" if len(row) > 1 else ""), "", "```", tts(parts), "```", ""]
    md += [f"Ends at ≈ {end:.1f} s of {dur:.1f} s · slack ≈ {slack:.1f} s", "", "---", ""]
open('/Users/vincent/Documents/CultureForge AI/artifacts/demo-video/VOICEOVER_ELEVENLABS.md', 'w').write('\n'.join(md))

cap = ["# CultureForge AI — captions text (real spellings)", "",
       "Use this for burned-in captions or subtitles. It is the same words as `VOICEOVER.md`, with the real spellings and no pauses.", ""]
for i, (fn, dur, desc, row, end, slack) in enumerate(rows, 1):
    cap += [f"**{i}. `{fn}`**", ""] + [clean(p) for _, _, p in row] + [""]
open('/Users/vincent/Documents/CultureForge AI/artifacts/demo-video/CAPTIONS_ELEVENLABS.md', 'w').write('\n'.join(cap))

print(f"{'clip':26} {'len':>5} {'ends':>6} {'slack':>6}")
for fn, dur, desc, row, end, slack in rows: print(f"{fn:26} {dur:5.1f} {end:6.1f} {slack:6.1f}" + ("   <-- TIGHT" if slack < 1.0 else ""))
print('problems:', bad or 'none')
print('total words ~', total_words)
