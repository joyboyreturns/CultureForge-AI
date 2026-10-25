# YouTube upload sheet — CultureForge AI

## Title (pick one, under 70 characters so it is not cut off)

1. **CultureForge AI: a business idea that can be told "no" (Qloo Hackathon)** — recommended
2. CultureForge AI — Evidence-tested business ideas, built on Qloo
3. We built an AI that argues with your business idea (Qloo Agentic Hackathon 2026)

## Description (paste as is; replace nothing, the links are real)

```
CultureForge AI turns a business idea, an audience and a city into directions you can challenge, then tests them against real cultural evidence from Qloo. Every claim cites a Qloo place or tag. The evidence test can say "contested", and in this demo it does.

Built for the Qloo Agentic Hackathon 2026.

Try the live demo: https://cultureforge-ai.tail601a7c.ts.net
Source code: https://github.com/joyboyreturns/CultureForge-AI

What you will see
0:00 The idea: a guess about what a place will love
0:23 Why an ordinary language model is not enough
0:36 A real brief: an artisan bakery in Tokyo
0:54 Places and signals returned by Qloo
1:06 Directions with citations and stated limits
1:17 Under the hood: from a brief to a verdict
1:32 The interest map, and "what happens without this evidence?"
2:08 How the evidence test can say no
2:24 The test runs: the lead direction comes out contested
2:54 The bounded agent: steps run, steps refused
3:20 Three layers kept apart
3:33 Try it yourself

How it stays honest
- No mock data. Every place, tag and number shown was returned by Qloo.
- This video replays evidence Qloo returned earlier, so nothing was invented and no new request was made while recording.
- The verdict is about anchor fit within the retrieved places. It is not a claim about demand, rent or revenue.
- Map pins are address or name matches from OpenStreetMap, not surveyed points.
- A brand-new brief takes about two minutes to research the first time.

Stack: Qloo API (nine workflows), rule-based composer and validator, optional model layer through Vercel AI Gateway, FastAPI, React.

#QlooHackathon #AgenticAI #Qloo #CultureForge
```

(Chapter times assume no title card. If you add the 3 s title card, add 0:03 to every time except the first, which stays 0:00.)

## Captions

- Upload a caption file, not YouTube's auto captions. Auto captions will write "Clue" or "Claude" for Qloo.
- Burned-in captions (from `CAPTIONS.md`) are the safer choice, because many judges watch muted. If you burn them in, you can still upload an .srt as well.
- Use the **real spellings**: Qloo (not Kloo), CultureForge AI, IDs. The `Kloo` spelling is only for the voice generator.
- Check each caption against what is spoken. If you changed any voice text, change the captions to match.
- Keep each caption to two lines, with a minimum of 1.5 s on screen.
- Check once that "Qloo" is spelled the same everywhere, including the thumbnail and title.

## Thumbnail (1280 × 720, under 2 MB, JPG or PNG)

- Left: the words **"Can your idea be told no?"** in 3 to 5 big words. Pick one phrase and keep it.
- Right: the screenshot of the evidence test showing the **contested** verdict (take it from the video, or use `docs/screenshots/evidence-test.jpg`).
- Small line along the bottom: "CultureForge AI · Qloo Hackathon".
- Use the studio's own colours (dark background, peach and lavender accents) and one big headline font. No faces, no arrows, no fake numbers.
- Text must stay readable at phone size.

## Settings

- **Visibility:** Unlisted is enough for a submission link; use Public only if you want it found. Do not leave it Private.
- **Audience:** Not made for kids.
- **Altered content:** Yes. The narration is AI-generated. Tick the "altered or synthetic content" box if it asks. Mention it in the description if you prefer: "Narrated with an AI voice."
- **Category:** Science & Technology.
- **Tags:** CultureForge AI, Qloo, Qloo API, Qloo Hackathon, agentic AI, taste AI, cultural intelligence, business idea validation.
- **Language:** English. **Comments:** allowed (a judge may leave one).
- **Pinned comment:** the demo and repo links again.

## Before you press Upload

1. The demo link in the description opens. Test it from a phone on mobile data, not your home Wi-Fi.
2. The GitHub link opens while logged out.
3. Watch the whole video once with sound, and once muted with captions.
4. The audio ends before each picture does, and nothing is read as "Claude".
5. Add the video link to your Devpost submission, and to `submission.json` if you want it recorded there.
6. The demo server must stay on until judging ends. The link will not work if your PC is off.
