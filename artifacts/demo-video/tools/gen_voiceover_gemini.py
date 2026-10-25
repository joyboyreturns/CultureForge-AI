import re
R = 0.375                      # s/word: Gemini read clip 1 (48 words) in ~18 s as pasted; treated as all-in speech with no pauses
P = {'S': 0.25, 'M': 0.5, 'L': 1.0}   # [short pause] ~250 ms, [medium pause] ~500 ms, [long pause] ~1 s (per the Replicate model page)
TAG = {'S': '[short pause]', 'M': '[medium pause]', 'L': '[long pause]'}
# Parts: text strings, or 'S' / 'M' / 'L' pauses, or a literal '[tag]' expressive tag (kept to a minimum).
CLIPS = [
 ("01-landing.mp4", 22.7, "Landing page, slow scroll", [(0.4, [
   "Every business idea starts as a guess,", 'S', "about what people in a place will love.", 'L',
   "Culture Forge A.I. puts that guess on trial.", 'M',
   "Describe an idea,", 'S', "an audience,", 'S', "and a city.", 'M',
   "We ask Kloo what that audience gravitates to,", 'S', "then turn those signals into directions you can challenge."])]),
 ("02-diagram-compare.mp4", 13.3, "Diagram: ordinary model vs CultureForge on Qloo", [(0.5, [
   "Ask a language model about a bakery,", 'S', "and you get fluent text with no sources.", 'L',
   "Here,", 'S', "every direction must point back to evidence Kloo returned."])]),
 ("03-studio.mp4", 18.0, "Studio, run the example, executive brief", [(0.5, [
   "Here's a real brief:", 'S', "an artisan bakery in Tokyo,", 'S', "for early-morning commuters.", 'M',
   "This demo replays evidence Kloo returned earlier,", 'S', "so it opens instantly.", 'M',
   "Every claim traces to a Kloo place or tag,", 'S', "never an invented score."])]),
 ("04-places.mp4", 12.0, "Places and signals, Qloo photos and numbers", [(0.5, [
   "Real places Kloo returned,", 'S', "with its own photos and numbers.", 'L',
   "The figures are Kloo's.", 'S', "The page says what it could not verify."])]),
 ("05-directions.mp4", 11.0, "Two directions with citations and limits", [(0.5, [
   "From that evidence,", 'S', "Culture Forge composes directions.", 'M',
   "Each names the places it rests on,", 'S', "what it claims,", 'S', "and what remains unproven."])]),
 ("06-diagram-pipeline.mp4", 15.3, "Diagram: from a brief to a verdict", [(0.7, [
   "Under the hood:", 'S', "Kloo returns places, tags,", 'S', "and audiences.", 'M',
   "Rules compose cited directions.", 'M',
   "An optional model step comes last,", 'S', "and a validator rejects any claim without a Kloo I.D."])]),
 ("07-map.mp4", 36.0, "Interest map, pick a venue, remove it", [
  (0.6, ["Now,", 'S', "the same evidence on a real map.", 'M', "Venues are pinned from the addresses Kloo returned.", 'M',
         "Nine of ten were placed.", 'S', "One wasn't, and says why."]),
  (12.4, ["Pick a venue,", 'S', "and the panel says how its pin was matched,", 'S', "and why it's connected to this audience."]),
  (21.0, ["Then ask the hard question:", 'S', "what happens without it?", 'L',
          "Remove this bakery,", 'S', "and the directions are rebuilt from held evidence,", 'S', "with no new Kloo request.", 'M',
          "What changed is shown."])]),
 ("08-diagram-verdict.mp4", 15.3, "Diagram: how the evidence test can say no", [(0.4, [
   "A tool that always agrees is decoration.", 'S', "This test has three outcomes.", 'M',
   "Both checks pass:", 'S', "supported.", 'S',
   "A check is missing:", 'S', "unproven.", 'S',
   "A check fails:", 'S', "contested.", 'S',
   "Re-anchor,", 'S', "and test again."])]),
 ("09-test.mp4", 30.5, "Evidence test runs: contested, order changed", [(0.6, [
   "Let's run it on this brief.", 'M', "Kloo ranks the places,", 'S', "then compares their tags.", 'M',
   "The lead direction's anchor,", 'S', "The Little Bakery,", 'S', "ranks eighth of ten.", 'M',
   "So the verdict is,", 'M', "contested.", 'S', "And the order of directions changes.", 'L',
   "The brief named no demographic,", 'S', "so the test uses a default one.", 'M',
   "It's a verdict about anchor fit in this sample,", 'S', "not about demand."])]),
 ("10-agent.mp4", 25.7, "Agent steps, refused steps, cited analysis", [(0.6, [
   "Behind it,", 'S', "a bounded agent plans up to eight steps over approved Kloo workflows:", 'S', "tags, audiences, comparisons.", 'M',
   "Six ran.", 'S', "Two cited things it had not observed,", 'S', "so they were refused.", 'M',
   "The final analysis must cite Kloo I.D.s from this run.", 'M',
   "Its conclusion is modest:", 'S', "the evidence supports only a category-level reading."])]),
 ("11-diagram-layers.mp4", 13.3, "Diagram: three layers kept apart", [(0.4, [
   "Three layers,", 'S', "kept apart:", 'M', "what Kloo returned,", 'M', "what rules decided,", 'M', "and what a model wrote.", 'M',
   "If the model fails,", 'S', "the rule-based answer stands."])]),
 ("12-close.mp4", 12.2, "Landing hero, cursor to Try the demo", [(0.5, [
   "Culture Forge A.I.:", 'S', "Kloo's cultural intelligence,", 'S', "as evidence that can disagree with your idea.", 'M',
   "Open source.", 'S', "Nine Kloo workflows.", 'S', "Try the demo."])]),
]
def words(t): return len(re.findall(r"[A-Za-z0-9'’\-]+", t.replace('A.I.', 'AI')))
def est(parts): return sum(words(p) * R if (p not in P and not p.startswith('[')) else (P.get(p, 0)) for p in parts)
def tts(parts):
    out = []
    for p in parts: out.append(TAG[p] if p in P else p)
    return ' '.join(out)
def check_tags(parts):
    prev_tag = False
    for p in parts:
        is_tag = p in P or p.startswith('[')
        assert not (is_tag and prev_tag), 'two tags next to each other: ' + str(parts)
        prev_tag = is_tag
def clean(parts):
    t = ' '.join(p for p in parts if p not in P and not p.startswith('['))
    t = re.sub(r'\s+([,:.])', r'\1', t)
    for a, b in (('Culture Forge A.I.', 'CultureForge AI'), ('Culture Forge', 'CultureForge'), ('Kloo', 'Qloo'), ('I.D.s', 'IDs'), ('I.D.', 'ID')): t = t.replace(a, b)
    return t
rows = []; bad = []
for fn, dur, desc, segs in CLIPS:
    for at, parts in segs: check_tags(parts)
    row = [(at, est(p), p) for at, p in segs]
    end = max(at + e for at, e, _ in row); slack = dur - end
    rows.append((fn, dur, desc, row, end, slack))
    if slack < 1.0: bad.append((fn, round(slack, 2)))
    for (a1, e1, _), (a2, _, _) in zip(row, row[1:]):
        if a1 + e1 > a2 - 0.3: bad.append((fn, 'blocks overlap'))
PROMPT = ('A deep, confident radio announcer: calm, warm and authoritative, like a documentary narrator introducing a serious new product. '
          'Pace: deliberate and unhurried, about 125 words a minute, with a clear breath between sentences. Never rushed. '
          'Pronounce the brand name "Kloo" (written Qloo in captions) exactly as "kloo", rhyming with "blue". It is never "Claude" and never "clue". '
          'Say "A.I." as the two letters A and I.')
OUT = '/Users/vincent/Documents/CultureForge AI/artifacts/demo-video/'
md = ["# CultureForge AI — voice-over for Google Gemini TTS", "",
 "For **Gemini Flash TTS**. The tag rules below come from Google's documentation for **Gemini 3.1 Flash TTS**, the newest I could find; you are on 3.8, which I",
 "could not find documentation for, so run the tag test below before relying on anything. The earlier ElevenLabs script is kept as `VOICEOVER_ELEVENLABS.md`; do not mix them,",
 "because ElevenLabs `<break>` tags are not Google's syntax.", "",
 "Clip order is the file order in `clips/` (01 → 12, about 3:45). Each block is **one audio file**: paste the text exactly as shown into the",
 "text box, put the style prompt below into the prompt (style instructions) box, generate, and place the audio on the timeline at **Place at**.",
 "Clip 7 has three blocks, because the map needs time to load between them.", "",
 "## Tag rules (from Google's documentation)", "",
 "- Tags go in **square brackets**, in English, exactly where the effect should happen.",
 "- **Never put two tags next to each other**; there is always text between them. Every block below follows this.",
 "- Pauses used here: `[short pause]` (about 0.25 s), `[medium pause]` (about 0.5 s), `[long pause]` (about 1 s). These lengths come from the Replicate model",
 "  page, not from Google; the first clip will show if they hold.",
 "- Also available, and not used on purpose in a judging video: `[laughs]`, `[whispers]`, `[gasp]`, mood tags such as `[determination]` and `[seriousness]`,",
 "  and pace tags `[slow]` and `[fast]`. If you try one and it is *spoken aloud*, delete it: some tags are read out loud.",
 "- There is no documented speed setting, so pace comes from the style prompt and the pauses.", "",
 "## Style prompt (use the same one for every clip)", "", "```", PROMPT, "```", "",
 "Voice: pick a deep, steady one. From memory, not verified here: **Charon** (informative), **Orus** (firm) or **Algenib** (gravelly) suit an announcer.", "",
 "## Pronunciation: why it said \"Claude\"", "",
 "Gemini TTS is a language model, not a rule-based voice, and there is no pronunciation tag. It tends to \"correct\" an unusual word toward a familiar",
 "one, and \"Clue\" in a technology script became \"Claude\". The voice text now spells it **Kloo**, and the style prompt says how to say it.",
 "Run this 15-second test before generating anything else. Listen for three things: the name sounds like \"kloo\", the pauses are real, and **no tag is read aloud**:", "",
 "```", "Kloo. [short pause] Kloo's data. [medium pause] Nine Kloo workflows. [long pause] Culture Forge A.I.", "```", "",
 "If \"Kloo\" is wrong, try these in order: **Kloo-** (no), then **Cloo**, then **Klew**. Use the winner everywhere (find and replace in this file).", "",
 "## Pace (measured, then planned)", "",
 "Clip 1 came out at about **18 s** with the first script, against a 22.7 s slot. This script is longer (more pauses, plus true details taken from the screen",
 "in clips 7, 9 and 10) and is planned to land every clip between 1 and 3 s before its end. Times below assume about 0.375 s a word, from your 18 s",
 "reading, plus the pauses. That is an estimate; **generate clip 1 first** and compare:", "",
 "- Within about 1 s of the *Voice length* shown: carry on.",
 "- More than 1.5 s short: turn every `[short pause]` into `[medium pause]` and every `[medium pause]` into `[long pause]` in that block (the \"stretch dial\"), then regenerate.",
 "- Too long: do the opposite, or delete a few `[short pause]` tags.",
 "- Still off: tell me the real length and I will rescale every block. If the voice ends up much faster or slower than planned, I will also retime the",
 "  Verdict and Layers diagrams so each part appears as the voice says it.", "", "---", ""]
for i, (fn, dur, desc, row, end, slack) in enumerate(rows, 1):
    md += [f"## {i}. `{fn}` — {dur:.1f} s", f"*On screen: {desc}.*", ""]
    for j, (at, e, parts) in enumerate(row):
        label = f" — block {'ABC'[j]}" if len(row) > 1 else ""
        md += [f"**Place at {at:.1f} s{label}** · voice length ≈ {e:.1f} s" + (f" · ends ≈ {at + e:.1f} s" if len(row) > 1 else ""), "", "```", tts(parts), "```", ""]
    md += [f"Ends at ≈ {end:.1f} s of {dur:.1f} s · slack ≈ {slack:.1f} s", "", "---", ""]
open(OUT + 'VOICEOVER.md', 'w').write('\n'.join(md))
cap = ["# CultureForge AI — captions text (real spellings)", "",
       "The same words as `VOICEOVER.md`, with the real spellings and no tags. For burned-in captions or subtitles.", ""]
for i, (fn, dur, desc, row, end, slack) in enumerate(rows, 1):
    cap += [f"**{i}. `{fn}`**", ""] + [clean(p) for _, _, p in row] + [""]
open(OUT + 'CAPTIONS.md', 'w').write('\n'.join(cap))
print(f"{'clip':26} {'len':>5} {'ends':>6} {'slack':>6}")
for fn, dur, desc, row, end, slack in rows: print(f"{fn:26} {dur:5.1f} {end:6.1f} {slack:6.1f}" + ("   <-- TIGHT" if slack < 1.0 else ""))
print('problems:', bad or 'none')
E_ = None
