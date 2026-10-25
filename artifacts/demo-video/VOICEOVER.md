# CultureForge AI — voice-over for Google Gemini TTS

For **Gemini Flash TTS**. The tag rules below come from Google's documentation for **Gemini 3.1 Flash TTS**, the newest I could find; you are on 3.8, which I
could not find documentation for, so run the tag test below before relying on anything. The earlier ElevenLabs script is kept as `VOICEOVER_ELEVENLABS.md`; do not mix them,
because ElevenLabs `<break>` tags are not Google's syntax.

Clip order is the file order in `clips/` (01 → 12, about 3:45). Each block is **one audio file**: paste the text exactly as shown into the
text box, put the style prompt below into the prompt (style instructions) box, generate, and place the audio on the timeline at **Place at**.
Clip 7 has three blocks, because the map needs time to load between them.

## Tag rules (from Google's documentation)

- Tags go in **square brackets**, in English, exactly where the effect should happen.
- **Never put two tags next to each other**; there is always text between them. Every block below follows this.
- Pauses used here: `[short pause]` (about 0.25 s), `[medium pause]` (about 0.5 s), `[long pause]` (about 1 s). These lengths come from the Replicate model
  page, not from Google; the first clip will show if they hold.
- Also available, and not used on purpose in a judging video: `[laughs]`, `[whispers]`, `[gasp]`, mood tags such as `[determination]` and `[seriousness]`,
  and pace tags `[slow]` and `[fast]`. If you try one and it is *spoken aloud*, delete it: some tags are read out loud.
- There is no documented speed setting, so pace comes from the style prompt and the pauses.

## Style prompt (use the same one for every clip)

```
A deep, confident radio announcer: calm, warm and authoritative, like a documentary narrator introducing a serious new product. Pace: deliberate and unhurried, about 125 words a minute, with a clear breath between sentences. Never rushed. Pronounce the brand name "Kloo" (written Qloo in captions) exactly as "kloo", rhyming with "blue". It is never "Claude" and never "clue". Say "A.I." as the two letters A and I.
```

Voice: pick a deep, steady one. From memory, not verified here: **Charon** (informative), **Orus** (firm) or **Algenib** (gravelly) suit an announcer.

## Pronunciation: why it said "Claude"

Gemini TTS is a language model, not a rule-based voice, and there is no pronunciation tag. It tends to "correct" an unusual word toward a familiar
one, and "Clue" in a technology script became "Claude". The voice text now spells it **Kloo**, and the style prompt says how to say it.
Run this 15-second test before generating anything else. Listen for three things: the name sounds like "kloo", the pauses are real, and **no tag is read aloud**:

```
Kloo. [short pause] Kloo's data. [medium pause] Nine Kloo workflows. [long pause] Culture Forge A.I.
```

If "Kloo" is wrong, try these in order: **Kloo-** (no), then **Cloo**, then **Klew**. Use the winner everywhere (find and replace in this file).

## Pace (measured, then planned)

Clip 1 came out at about **18 s** with the first script, against a 22.7 s slot. This script is longer (more pauses, plus true details taken from the screen
in clips 7, 9 and 10) and is planned to land every clip between 1 and 3 s before its end. Times below assume about 0.375 s a word, from your 18 s
reading, plus the pauses. That is an estimate; **generate clip 1 first** and compare:

- Within about 1 s of the *Voice length* shown: carry on.
- More than 1.5 s short: turn every `[short pause]` into `[medium pause]` and every `[medium pause]` into `[long pause]` in that block (the "stretch dial"), then regenerate.
- Too long: do the opposite, or delete a few `[short pause]` tags.
- Still off: tell me the real length and I will rescale every block. If the voice ends up much faster or slower than planned, I will also retime the
  Verdict and Layers diagrams so each part appears as the voice says it.

---

## 1. `01-landing.mp4` — 22.7 s
*On screen: Landing page, slow scroll.*

**Place at 0.4 s** · voice length ≈ 21.0 s

```
Every business idea starts as a guess, [short pause] about what people in a place will love. [long pause] Culture Forge A.I. puts that guess on trial. [medium pause] Describe an idea, [short pause] an audience, [short pause] and a city. [medium pause] We ask Kloo what that audience gravitates to, [short pause] then turn those signals into directions you can challenge.
```

Ends at ≈ 21.4 s of 22.7 s · slack ≈ 1.3 s

---

## 2. `02-diagram-compare.mp4` — 13.3 s
*On screen: Diagram: ordinary model vs CultureForge on Qloo.*

**Place at 0.5 s** · voice length ≈ 10.9 s

```
Ask a language model about a bakery, [short pause] and you get fluent text with no sources. [long pause] Here, [short pause] every direction must point back to evidence Kloo returned.
```

Ends at ≈ 11.4 s of 13.3 s · slack ≈ 1.9 s

---

## 3. `03-studio.mp4` — 18.0 s
*On screen: Studio, run the example, executive brief.*

**Place at 0.5 s** · voice length ≈ 15.5 s

```
Here's a real brief: [short pause] an artisan bakery in Tokyo, [short pause] for early-morning commuters. [medium pause] This demo replays evidence Kloo returned earlier, [short pause] so it opens instantly. [medium pause] Every claim traces to a Kloo place or tag, [short pause] never an invented score.
```

Ends at ≈ 16.0 s of 18.0 s · slack ≈ 2.0 s

---

## 4. `04-places.mp4` — 12.0 s
*On screen: Places and signals, Qloo photos and numbers.*

**Place at 0.5 s** · voice length ≈ 9.8 s

```
Real places Kloo returned, [short pause] with its own photos and numbers. [long pause] The figures are Kloo's. [short pause] The page says what it could not verify.
```

Ends at ≈ 10.2 s of 12.0 s · slack ≈ 1.8 s

---

## 5. `05-directions.mp4` — 11.0 s
*On screen: Two directions with citations and limits.*

**Place at 0.5 s** · voice length ≈ 9.1 s

```
From that evidence, [short pause] Culture Forge composes directions. [medium pause] Each names the places it rests on, [short pause] what it claims, [short pause] and what remains unproven.
```

Ends at ≈ 9.6 s of 11.0 s · slack ≈ 1.4 s

---

## 6. `06-diagram-pipeline.mp4` — 15.3 s
*On screen: Diagram: from a brief to a verdict.*

**Place at 0.7 s** · voice length ≈ 13.0 s

```
Under the hood: [short pause] Kloo returns places, tags, [short pause] and audiences. [medium pause] Rules compose cited directions. [medium pause] An optional model step comes last, [short pause] and a validator rejects any claim without a Kloo I.D.
```

Ends at ≈ 13.7 s of 15.3 s · slack ≈ 1.6 s

---

## 7. `07-map.mp4` — 36.0 s
*On screen: Interest map, pick a venue, remove it.*

**Place at 0.6 s — block A** · voice length ≈ 11.2 s · ends ≈ 11.8 s

```
Now, [short pause] the same evidence on a real map. [medium pause] Venues are pinned from the addresses Kloo returned. [medium pause] Nine of ten were placed. [short pause] One wasn't, and says why.
```

**Place at 12.4 s — block B** · voice length ≈ 7.6 s · ends ≈ 20.0 s

```
Pick a venue, [short pause] and the panel says how its pin was matched, [short pause] and why it's connected to this audience.
```

**Place at 21.0 s — block C** · voice length ≈ 13.1 s · ends ≈ 34.1 s

```
Then ask the hard question: [short pause] what happens without it? [long pause] Remove this bakery, [short pause] and the directions are rebuilt from held evidence, [short pause] with no new Kloo request. [medium pause] What changed is shown.
```

Ends at ≈ 34.1 s of 36.0 s · slack ≈ 1.9 s

---

## 8. `08-diagram-verdict.mp4` — 15.3 s
*On screen: Diagram: how the evidence test can say no.*

**Place at 0.4 s** · voice length ≈ 13.4 s

```
A tool that always agrees is decoration. [short pause] This test has three outcomes. [medium pause] Both checks pass: [short pause] supported. [short pause] A check is missing: [short pause] unproven. [short pause] A check fails: [short pause] contested. [short pause] Re-anchor, [short pause] and test again.
```

Ends at ≈ 13.8 s of 15.3 s · slack ≈ 1.5 s

---

## 9. `09-test.mp4` — 30.5 s
*On screen: Evidence test runs: contested, order changed.*

**Place at 0.6 s** · voice length ≈ 27.5 s

```
Let's run it on this brief. [medium pause] Kloo ranks the places, [short pause] then compares their tags. [medium pause] The lead direction's anchor, [short pause] The Little Bakery, [short pause] ranks eighth of ten. [medium pause] So the verdict is, [medium pause] contested. [short pause] And the order of directions changes. [long pause] The brief named no demographic, [short pause] so the test uses a default one. [medium pause] It's a verdict about anchor fit in this sample, [short pause] not about demand.
```

Ends at ≈ 28.1 s of 30.5 s · slack ≈ 2.4 s

---

## 10. `10-agent.mp4` — 25.7 s
*On screen: Agent steps, refused steps, cited analysis.*

**Place at 0.6 s** · voice length ≈ 22.6 s

```
Behind it, [short pause] a bounded agent plans up to eight steps over approved Kloo workflows: [short pause] tags, audiences, comparisons. [medium pause] Six ran. [short pause] Two cited things it had not observed, [short pause] so they were refused. [medium pause] The final analysis must cite Kloo I.D.s from this run. [medium pause] Its conclusion is modest: [short pause] the evidence supports only a category-level reading.
```

Ends at ≈ 23.2 s of 25.7 s · slack ≈ 2.5 s

---

## 11. `11-diagram-layers.mp4` — 13.3 s
*On screen: Diagram: three layers kept apart.*

**Place at 0.4 s** · voice length ≈ 11.1 s

```
Three layers, [short pause] kept apart: [medium pause] what Kloo returned, [medium pause] what rules decided, [medium pause] and what a model wrote. [medium pause] If the model fails, [short pause] the rule-based answer stands.
```

Ends at ≈ 11.5 s of 13.3 s · slack ≈ 1.8 s

---

## 12. `12-close.mp4` — 12.2 s
*On screen: Landing hero, cursor to Try the demo.*

**Place at 0.5 s** · voice length ≈ 9.8 s

```
Culture Forge A.I.: [short pause] Kloo's cultural intelligence, [short pause] as evidence that can disagree with your idea. [medium pause] Open source. [short pause] Nine Kloo workflows. [short pause] Try the demo.
```

Ends at ≈ 10.2 s of 12.2 s · slack ≈ 1.9 s

---
