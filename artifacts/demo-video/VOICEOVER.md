# CultureForge AI — voice-over for Google Gemini TTS

Clip order is the file order in `clips/` (01 → 12, about 3:45). Each block is **one audio file**: paste the text exactly as shown into the
text box, put the style prompt below into the prompt (style instructions) box, generate, and place the audio on the timeline at **Place at**.
Clip 7 has three blocks, because the map needs time to load between them.

## Tags: only `[short pause]`

Your voice **reads `[medium pause]` and `[long pause]` aloud**, so they are gone from this script. The only tag used is `[short pause]`, which your
list confirms exists. Longer gaps are made with ordinary punctuation: a full stop, or a new sentence. Every block follows two rules:

- The only tag is `[short pause]`, always with text on both sides of it, never two tags together.
- If you hear `[short pause]` *spoken*, delete every tag in that block. The full stops still give the voice its breaths.
- Expressive tags from your list (`[sigh]`, `[chuckle]`, `[gasp]` and so on) are left out on purpose: this is a serious product video.

## Style prompt (use the same one for every clip)

```
A deep, confident radio announcer: calm, warm and authoritative, like a documentary narrator introducing a serious new product. Pace: deliberate and unhurried, about 125 words a minute, with a clear breath between sentences. Never rushed. Pronounce the brand name "Kloo" (written Qloo in captions) exactly as "kloo", rhyming with "blue". It is never "Claude" and never "clue". Say "A.I." as the two letters A and I.
```

Voice: pick a deep, steady one.

## Pronunciation: why it said "Claude"

Gemini TTS is a language model, and there is no pronunciation tag. It tends to "correct" an unusual word toward a familiar
one, and "Clue" in a technology script became "Claude". The voice text spells it **Kloo**, and the style prompt says how to say it.
Test this before generating anything else; listen for the name sounding like "kloo" and for no tag being read aloud:

```
Kloo. [short pause] Kloo's data. Nine Kloo workflows. Culture Forge A.I.
```

If "Kloo" is wrong, try these in order: **Cloo**, then **Klew**. Use the winner everywhere (find and replace in this file).

## Pace (measured)

Your clip 1 ran **27 s** against a 22.7 s slot. That script had 47 spoken words, plus 8 more words from tags read aloud, with the 125-words-a-minute
style prompt: about **0.47 s a word**. Every block below is cut to that pace and is planned to end 1.4 to 3.5 s before its clip does. The trims are
real cuts (shorter sentences), not just fewer pauses. Check **clip 1 first**; its voice length should come out near 20.9 s:

- Within about 1 s of the *Voice length* shown: carry on with the rest.
- Longer: in the style prompt change "about 125 words a minute" to "about 140 words a minute", then regenerate.
- Shorter by more than 1.5 s: change it to "about 115 words a minute".
- Still off: tell me the real length of clip 1 and I will rescale every block. Clip 8 (the verdict diagram) is timed to the voice, so tell me its length too and
  I will retime that diagram. Clip 11 (layers) is already timed to this pace.

---

## 1. `01-landing.mp4` — 22.7 s
*On screen: Landing page, slow scroll.*

**Place at 0.4 s** · voice length ≈ 20.9 s

```
Every idea starts as a guess, [short pause] about what people in a place will love. Culture Forge A.I. puts that guess on trial. Describe an idea, [short pause] an audience, [short pause] and a city. We ask Kloo what they love, [short pause] then build directions you can challenge.
```

Ends at ≈ 21.3 s of 22.7 s · slack ≈ 1.4 s

---

## 2. `02-diagram-compare.mp4` — 13.3 s
*On screen: Diagram: ordinary model vs CultureForge on Qloo.*

**Place at 0.5 s** · voice length ≈ 10.5 s

```
Ask a language model about a bakery, [short pause] and you get fluent text with no sources. Here, [short pause] every direction cites Kloo evidence.
```

Ends at ≈ 11.0 s of 13.3 s · slack ≈ 2.3 s

---

## 3. `03-studio.mp4` — 18.0 s
*On screen: Studio, run the example, executive brief.*

**Place at 0.5 s** · voice length ≈ 15.5 s

```
Here's a real brief: [short pause] an artisan bakery in Tokyo, [short pause] for early-morning commuters. This demo replays evidence Kloo returned, [short pause] so it opens instantly. Every claim traces to a Kloo place or tag.
```

Ends at ≈ 16.0 s of 18.0 s · slack ≈ 2.0 s

---

## 4. `04-places.mp4` — 12.0 s
*On screen: Places and signals, Qloo photos and numbers.*

**Place at 0.5 s** · voice length ≈ 8.8 s

```
Real places Kloo returned, [short pause] with Kloo's own photos and numbers. The page says what it could not verify.
```

Ends at ≈ 9.3 s of 12.0 s · slack ≈ 2.7 s

---

## 5. `05-directions.mp4` — 11.0 s
*On screen: Two directions with citations and limits.*

**Place at 0.5 s** · voice length ≈ 8.9 s

```
From that evidence, [short pause] Culture Forge composes directions. Each names its places, [short pause] its claim, [short pause] and what remains unproven.
```

Ends at ≈ 9.4 s of 11.0 s · slack ≈ 1.6 s

---

## 6. `06-diagram-pipeline.mp4` — 15.3 s
*On screen: Diagram: from a brief to a verdict.*

**Place at 0.7 s** · voice length ≈ 11.1 s

```
Under the hood: [short pause] Kloo returns places, tags and audiences. Rules compose cited directions. A validator rejects any claim without a Kloo I.D.
```

Ends at ≈ 11.8 s of 15.3 s · slack ≈ 3.5 s

---

## 7. `07-map.mp4` — 36.0 s
*On screen: Interest map, pick a venue, remove it.*

**Place at 0.6 s — block A** · voice length ≈ 10.9 s · ends ≈ 11.5 s

```
The same evidence, [short pause] on a real map. Pins come from Kloo's addresses. Nine of ten were placed. [short pause] One wasn't, and says why.
```

**Place at 12.4 s — block B** · voice length ≈ 7.6 s · ends ≈ 20.1 s

```
Pick a venue. [short pause] The panel says how its pin was matched, [short pause] and why it's connected.
```

**Place at 21.0 s — block C** · voice length ≈ 13.6 s · ends ≈ 34.6 s

```
Then the hard question: [short pause] what happens without it? Remove this bakery, [short pause] and the directions are rebuilt from held evidence, [short pause] with no new Kloo request. Changes are shown.
```

Ends at ≈ 34.6 s of 36.0 s · slack ≈ 1.4 s

---

## 8. `08-diagram-verdict.mp4` — 15.3 s
*On screen: Diagram: how the evidence test can say no.*

**Place at 0.4 s** · voice length ≈ 13.4 s

```
A tool that always agrees is decoration. [short pause] This test can say no. Both checks pass: supported. [short pause] One missing: unproven. [short pause] One fails: contested. [short pause] Re-anchor, and test again.
```

Ends at ≈ 13.8 s of 15.3 s · slack ≈ 1.5 s

---

## 9. `09-test.mp4` — 30.5 s
*On screen: Evidence test runs: contested, order changed.*

**Place at 0.6 s** · voice length ≈ 28.1 s

```
Run it on this brief. Kloo ranks the places, [short pause] then compares their tags. The lead direction's anchor, [short pause] The Little Bakery, [short pause] ranks eighth of ten. So the verdict is contested. [short pause] And the order of directions changes. No demographic was named, [short pause] so it uses a default. It's a verdict about anchor fit in this sample, [short pause] not about demand.
```

Ends at ≈ 28.7 s of 30.5 s · slack ≈ 1.8 s

---

## 10. `10-agent.mp4` — 25.7 s
*On screen: Agent steps, refused steps, cited analysis.*

**Place at 0.6 s** · voice length ≈ 23.3 s

```
Behind it, [short pause] a bounded agent plans up to eight steps over approved Kloo workflows. Six ran. [short pause] Two cited things it had not observed, [short pause] so they were refused. The final analysis must cite Kloo I.D.s from this run. Its conclusion is modest: [short pause] only a category-level reading.
```

Ends at ≈ 23.9 s of 25.7 s · slack ≈ 1.8 s

---

## 11. `11-diagram-layers.mp4` — 13.3 s
*On screen: Diagram: three layers kept apart.*

**Place at 0.4 s** · voice length ≈ 11.4 s

```
Three layers, [short pause] kept apart: what Kloo returned, what rules decided, and what a model wrote. If the model fails, [short pause] the rule-based answer stands.
```

Ends at ≈ 11.8 s of 13.3 s · slack ≈ 1.5 s

---

## 12. `12-close.mp4` — 12.2 s
*On screen: Landing hero, cursor to Try the demo.*

**Place at 0.5 s** · voice length ≈ 9.8 s

```
Culture Forge A.I.: [short pause] Kloo's cultural intelligence, [short pause] as evidence that can disagree with your idea. Open source. [short pause] Try the demo.
```

Ends at ≈ 10.3 s of 12.2 s · slack ≈ 1.9 s

---
