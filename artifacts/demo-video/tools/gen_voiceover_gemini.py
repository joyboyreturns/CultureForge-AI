import re
R = 0.47                       # s/word, measured: clip 1 (47 words + 8 spoken tag words) took 27 s with the 125 wpm style prompt
P = {'S': 0.3, 'M': 0.0, 'L': 0.2}    # S = [short pause] (the only tag this voice honours); M = a full stop (no tag); L = a blank line (no tag)
TAG = {'S': '[short pause]', 'M': '', 'L': '\n'}
# Parts: text strings, or 'S' / 'M' / 'L' pauses, or a literal '[tag]' expressive tag (kept to a minimum).
CLIPS = [
 ("01-landing.mp4", 22.7, "Landing page, slow scroll", [(0.4, [
   "Every idea starts as a guess,", 'S', "about what people in a place will love.", 'M',
   "Culture Forge A.I. puts that guess on trial.", 'M',
   "Describe an idea,", 'S', "an audience,", 'S', "and a city.", 'M',
   "We ask Kloo what they love,", 'S', "then build directions you can challenge."])]),
 ("02-diagram-compare.mp4", 13.3, "Diagram: ordinary model vs CultureForge on Qloo", [(0.5, [
   "Ask a language model about a bakery,", 'S', "and you get fluent text with no sources.", 'M',
   "Here,", 'S', "every direction cites Kloo evidence."])]),
 ("03-studio.mp4", 18.0, "Studio, run the example, executive brief", [(0.5, [
   "Here's a real brief:", 'S', "an artisan bakery in Tokyo,", 'S', "for early-morning commuters.", 'M',
   "This demo replays evidence Kloo returned,", 'S', "so it opens instantly.", 'M',
   "Every claim traces to a Kloo place or tag."])]),
 ("04-places.mp4", 12.0, "Places and signals, Qloo photos and numbers", [(0.5, [
   "Real places Kloo returned,", 'S', "with Kloo's own photos and numbers.", 'M',
   "The page says what it could not verify."])]),
 ("05-directions.mp4", 11.0, "Two directions with citations and limits", [(0.5, [
   "From that evidence,", 'S', "Culture Forge composes directions.", 'M',
   "Each names its places,", 'S', "its claim,", 'S', "and what remains unproven."])]),
 ("06-diagram-pipeline.mp4", 15.3, "Diagram: from a brief to a verdict", [(0.7, [
   "Under the hood:", 'S', "Kloo returns places, tags and audiences.", 'M',
   "Rules compose cited directions.", 'M',
   "A validator rejects any claim without a Kloo I.D."])]),
 ("07-map.mp4", 36.0, "Interest map, pick a venue, remove it", [
  (0.6, ["The same evidence,", 'S', "on a real map.", 'M', "Pins come from Kloo's addresses.", 'M',
         "Nine of ten were placed.", 'S', "One wasn't, and says why."]),
  (12.4, ["Pick a venue.", 'S', "The panel says how its pin was matched,", 'S', "and why it's connected."]),
  (21.0, ["Then the hard question:", 'S', "what happens without it?", 'M',
          "Remove this bakery,", 'S', "and the directions are rebuilt from held evidence,", 'S', "with no new Kloo request.", 'M',
          "Changes are shown."])]),
 ("08-diagram-verdict.mp4", 15.3, "Diagram: how the evidence test can say no", [(0.4, [
   "A tool that always agrees is decoration.", 'S', "This test can say no.", 'M',
   "Both checks pass: supported.", 'S',
   "One missing: unproven.", 'S',
   "One fails: contested.", 'S',
   "Re-anchor, and test again."])]),
 ("09-test.mp4", 30.5, "Evidence test runs: contested, order changed", [(0.6, [
   "Run it on this brief.", 'M', "Kloo ranks the places,", 'S', "then compares their tags.", 'M',
   "The lead direction's anchor,", 'S', "The Little Bakery,", 'S', "ranks eighth of ten.", 'M',
   "So the verdict is contested.", 'S', "And the order of directions changes.", 'M',
   "No demographic was named,", 'S', "so it uses a default.", 'M',
   "It's a verdict about anchor fit in this sample,", 'S', "not about demand."])]),
 ("10-agent.mp4", 25.7, "Agent steps, refused steps, cited analysis", [(0.6, [
   "Behind it,", 'S', "a bounded agent plans up to eight steps over approved Kloo workflows.", 'M',
   "Six ran.", 'S', "Two cited things it had not observed,", 'S', "so they were refused.", 'M',
   "The final analysis must cite Kloo I.D.s from this run.", 'M',
   "Its conclusion is modest:", 'S', "only a category-level reading."])]),
 ("11-diagram-layers.mp4", 13.3, "Diagram: three layers kept apart", [(0.4, [
   "Three layers,", 'S', "kept apart:", 'M', "what Kloo returned,", 'M', "what rules decided,", 'M', "and what a model wrote.", 'M',
   "If the model fails,", 'S', "the rule-based answer stands."])]),
 ("12-close.mp4", 12.2, "Landing hero, cursor to Try the demo", [(0.5, [
   "Culture Forge A.I.:", 'S', "Kloo's cultural intelligence,", 'S', "as evidence that can disagree with your idea.", 'M',
   "Open source.", 'S', "Try the demo."])]),
]
def words(t): return len(re.findall(r"[A-Za-z0-9'’\-]+", t.replace('A.I.', 'AI')))
def est(parts): return sum(words(p) * R if (p not in P and not p.startswith('[')) else (P.get(p, 0)) for p in parts)
def tts(parts):
    out = []
    for p in parts:
        if p in P:
            if TAG[p]: out.append(TAG[p])
        else: out.append(p)
    t = ' '.join(out)
    return t.replace(' \n ', '\n')
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
 "Clip order is the file order in `clips/` (01 → 12, about 3:45). Each block is **one audio file**: paste the text exactly as shown into the",
 "text box, put the style prompt below into the prompt (style instructions) box, generate, and place the audio on the timeline at **Place at**.",
 "Clip 7 has three blocks, because the map needs time to load between them.", "",
 "## Tags: only `[short pause]`", "",
 "Your voice **reads `[medium pause]` and `[long pause]` aloud**, so they are gone from this script. The only tag used is `[short pause]`, which your",
 "list confirms exists. Longer gaps are made with ordinary punctuation: a full stop, or a new sentence. Every block follows two rules:",
 "",
 "- The only tag is `[short pause]`, always with text on both sides of it, never two tags together.",
 "- If you hear `[short pause]` *spoken*, delete every tag in that block. The full stops still give the voice its breaths.",
 "- Expressive tags from your list (`[sigh]`, `[chuckle]`, `[gasp]` and so on) are left out on purpose: this is a serious product video.", "",
 "## Style prompt (use the same one for every clip)", "", "```", PROMPT, "```", "",
 "Voice: pick a deep, steady one.", "",
 "## Pronunciation: why it said \"Claude\"", "",
 "Gemini TTS is a language model, and there is no pronunciation tag. It tends to \"correct\" an unusual word toward a familiar",
 "one, and \"Clue\" in a technology script became \"Claude\". The voice text spells it **Kloo**, and the style prompt says how to say it.",
 "Test this before generating anything else; listen for the name sounding like \"kloo\" and for no tag being read aloud:", "",
 "```", "Kloo. [short pause] Kloo's data. Nine Kloo workflows. Culture Forge A.I.", "```", "",
 "If \"Kloo\" is wrong, try these in order: **Cloo**, then **Klew**. Use the winner everywhere (find and replace in this file).", "",
 "## Pace (measured)", "",
 "Your clip 1 ran **27 s** against a 22.7 s slot. That script had 47 spoken words, plus 8 more words from tags read aloud, with the 125-words-a-minute",
 "style prompt: about **0.47 s a word**. Every block below is cut to that pace and is planned to end 1.4 to 3.5 s before its clip does. The trims are",
 "real cuts (shorter sentences), not just fewer pauses. Check **clip 1 first**; its voice length should come out near 20.9 s:", "",
 "- Within about 1 s of the *Voice length* shown: carry on with the rest.",
 "- Longer: in the style prompt change \"about 125 words a minute\" to \"about 140 words a minute\", then regenerate.",
 "- Shorter by more than 1.5 s: change it to \"about 115 words a minute\".",
 "- Still off: tell me the real length of clip 1 and I will rescale every block. Clip 8 (the verdict diagram) is timed to the voice, so tell me its length too and",
 "  I will retime that diagram. Clip 11 (layers) is already timed to this pace.", "", "---", ""]
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
