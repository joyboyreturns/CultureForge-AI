# CultureForge AI — ElevenLabs voice-over (Adam)

Clip order is the file order in `clips/` (01 → 12, about 3:45). Each block below is **one audio file**: paste the text
exactly as shown (the `<break … />` tags are pauses), generate it, then place the audio on the timeline at the
**Place at** time. Clip 7 has three blocks, because the map needs time to load between them.

## Settings for Adam

| Setting | Value |
|---|---|
| Model | **Multilingual v2** (or Turbo v2.5). `<break>` tags work on both. *Not* Eleven v3, which ignores them: there, replace each break with ` ... ` |
| Stability | 60 (steady, announcer-like; lower sounds more dramatic and less consistent between clips) |
| Similarity | 80 |
| Style exaggeration | 10 (higher can make Adam over-act) |
| Speaker boost | On |
| Speed | 1.00 (see "Check the pace" below) |

## Spelling used in the voice text (so Adam says it right)

- **Qloo → "Clue"** (that is how it is pronounced). Use the real spelling in captions: see `CAPTIONS.md`.
- **CultureForge AI → "Culture Forge A.I."**, **IDs → "I.D.s"**.
- Pauses: commas are a short breath; `<break time="0.4s" />` is a clean beat; a longer one (0.8 s) is placed before a key
  idea. There are no filler sounds ("um", "hmm"): on a judging video they read as unsure. Ask if you want them.

## Check the pace first (2 minutes)

The timings below assume Adam at speed 1.00 reads about 143 words a minute. That is an estimate, not a
measurement. Generate **clip 1** and **clip 7 block A**, drop them on the timeline, and compare with the *Voice length* shown:

- Within ±0.5 s: go ahead with the rest.
- Longer than the slot: set Speed to 1.05 (about 5% faster) and regenerate. Do not go above 1.10; it sounds rushed.
- Shorter: set Speed to 0.95, or just leave the extra silence.
- If it is way off, tell me the two lengths and I will rescale every block.

Slack is the silence left at the end of the clip. Every clip keeps at least 0.8 s of slack.

---

## 1. `01-landing.mp4` — 22.7 s
*On screen: Landing page, slow scroll.*

**Place at 0.4 s** · voice length ≈ 21.4 s

```
Every business idea starts as a guess about what people in a place will love. <break time="0.4s" /> Culture Forge A.I. puts that guess on trial. <break time="0.4s" /> Describe an idea, an audience, and a city. <break time="0.4s" /> We ask Clue what that audience gravitates to, then turn those signals into directions you can challenge.
```

Ends at ≈ 21.8 s of 22.7 s · slack ≈ 0.9 s

---

## 2. `02-diagram-compare.mp4` — 13.3 s
*On screen: Diagram: ordinary model vs CultureForge on Qloo.*

**Place at 0.5 s** · voice length ≈ 11.0 s

```
Ask a language model about a bakery, and you get fluent text with no sources. <break time="0.5s" /> Here, every direction must point back to evidence Clue returned.
```

Ends at ≈ 11.5 s of 13.3 s · slack ≈ 1.8 s

---

## 3. `03-studio.mp4` — 18.0 s
*On screen: Studio, run the example, executive brief.*

**Place at 0.5 s** · voice length ≈ 16.5 s

```
Here's a real brief: an artisan bakery in Tokyo, for early-morning commuters. <break time="0.5s" /> This demo replays evidence Clue returned earlier, so it opens instantly. <break time="0.5s" /> Every claim traces to a Clue place or tag, never an invented score.
```

Ends at ≈ 17.0 s of 18.0 s · slack ≈ 1.0 s

---

## 4. `04-places.mp4` — 12.0 s
*On screen: Places and signals, Qloo photos and numbers.*

**Place at 0.5 s** · voice length ≈ 9.6 s

```
Real places Clue returned, with its own photos and numbers. <break time="0.4s" /> The figures are Clue's. The page says what it could not verify.
```

Ends at ≈ 10.1 s of 12.0 s · slack ≈ 1.9 s

---

## 5. `05-directions.mp4` — 11.0 s
*On screen: Two directions with citations and limits.*

**Place at 0.5 s** · voice length ≈ 9.2 s

```
From that evidence, Culture Forge composes directions. <break time="0.4s" /> Each names the places it rests on, what it claims, and what remains unproven.
```

Ends at ≈ 9.7 s of 11.0 s · slack ≈ 1.3 s

---

## 6. `06-diagram-pipeline.mp4` — 15.3 s
*On screen: Diagram: from a brief to a verdict.*

**Place at 0.7 s** · voice length ≈ 13.2 s

```
Under the hood: Clue returns places, tags, and audiences. <break time="0.3s" /> Rules compose cited directions. <break time="0.3s" /> An optional model step comes last, and a validator rejects any claim without a Clue I.D.
```

Ends at ≈ 13.9 s of 15.3 s · slack ≈ 1.4 s

---

## 7. `07-map.mp4` — 36.0 s
*On screen: Interest map, pick a venue, remove it.*

**Place at 0.6 s — block A** · voice length ≈ 7.5 s · ends ≈ 8.1 s

```
Now, the same evidence on a real map. <break time="0.8s" /> Venues are pinned from the addresses Clue returned.
```

**Place at 11.6 s — block B** · voice length ≈ 8.7 s · ends ≈ 20.3 s

```
Pick a venue, <break time="0.3s" /> and the panel says exactly how its pin was matched, and why it's connected to this audience.
```

**Place at 21.0 s — block C** · voice length ≈ 13.2 s · ends ≈ 34.2 s

```
Then ask the hard question: what happens without it? <break time="0.6s" /> Remove this bakery, and the directions are rebuilt from held evidence, with no new Clue request. <break time="0.4s" /> What changed is shown.
```

Ends at ≈ 34.2 s of 36.0 s · slack ≈ 1.8 s

---

## 8. `08-diagram-verdict.mp4` — 15.3 s
*On screen: Diagram: how the evidence test can say no.*

**Place at 0.4 s** · voice length ≈ 13.9 s

```
A tool that always agrees is decoration. This test has three outcomes. <break time="0.4s" /> Both checks pass: supported. <break time="0.3s" /> A check is missing: unproven. <break time="0.3s" /> A check fails: contested. <break time="0.3s" /> Re-anchor, and test again.
```

Ends at ≈ 14.3 s of 15.3 s · slack ≈ 1.0 s

---

## 9. `09-test.mp4` — 30.5 s
*On screen: Evidence test runs: contested, order changed.*

**Place at 0.6 s** · voice length ≈ 23.6 s

```
Let's run it on this brief. <break time="0.6s" /> Clue ranks the places, then compares their tags. <break time="0.5s" /> The lead direction's anchor lands in the bottom third of the places Clue ranked, so the verdict is <break time="0.3s" /> contested. And the order of directions changes. <break time="0.8s" /> It's a verdict about anchor fit in this sample, not about demand.
```

Ends at ≈ 24.2 s of 30.5 s · slack ≈ 6.3 s

---

## 10. `10-agent.mp4` — 25.7 s
*On screen: Agent steps, refused steps, cited analysis.*

**Place at 0.6 s** · voice length ≈ 21.2 s

```
Behind it, a bounded agent plans up to eight steps over approved Clue workflows: tags, audiences, comparisons. <break time="0.5s" /> A step that cites anything it hasn't observed is refused, and shown as refused. <break time="0.5s" /> The final analysis must cite Clue I.D.s from this run, and says what remains unproven.
```

Ends at ≈ 21.8 s of 25.7 s · slack ≈ 3.9 s

---

## 11. `11-diagram-layers.mp4` — 13.3 s
*On screen: Diagram: three layers kept apart.*

**Place at 0.4 s** · voice length ≈ 11.5 s

```
Three layers, kept apart: <break time="0.3s" /> what Clue returned, <break time="0.3s" /> what rules decided, <break time="0.3s" /> and what a model wrote. <break time="0.5s" /> If the model fails, the rule-based answer stands.
```

Ends at ≈ 11.9 s of 13.3 s · slack ≈ 1.4 s

---

## 12. `12-close.mp4` — 12.2 s
*On screen: Landing hero, cursor to Try the demo.*

**Place at 0.5 s** · voice length ≈ 9.6 s

```
Culture Forge A.I.: Clue's cultural intelligence, as evidence that can disagree with your idea. <break time="0.4s" /> Open source. Nine Clue workflows. Try the demo.
```

Ends at ≈ 10.1 s of 12.2 s · slack ≈ 2.1 s

---
