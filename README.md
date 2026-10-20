# CultureForge AI

An interactive prototype for turning a founder’s audience and business idea into cultural signals and concept directions. Mock mode works without Qloo access. When configured, the FastAPI backend can use the official Qloo Hackathon Kit CLI for live aggregate cultural signals.

## Stack

- React, TypeScript, Vite, Tailwind CSS
- FastAPI with Pydantic request/response contracts
- `CultureProvider` abstraction with `MockCultureProvider` and optional `QlooHarnessProvider`

The Qloo adapter uses the public `qloo exec find_tags` and `qloo exec recommend` workflows; it does not invent endpoints or query fields. The adapter makes at most two Qloo calls per uncached generation and caches results in memory for 24 hours. Mock concepts are generated from a shared catalog for food and beverage, retail, hospitality, wellness, and entertainment. Explicit audience keywords select a family, creative, mindful, value, professional, discovery, or general mock lens. That lens changes concept names, offerings, delivery choices, cultural hypotheses, and experience blueprints. Unmatched audiences use the supplied brief without inferred preferences. Location, objectives, and budget inform the pilot notes and illustrative pilot cost bands. Qloo signals, when live, are shown separately from these mock concepts. Scenario comparisons remain illustrative.

Keep credentials in the backend environment or Qloo CLI's private configuration. Never put a Qloo key in Vite client variables, source control, or command arguments.

## Run locally

Requires Node.js 18+ and Python 3.10+.

```bash
npm install
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start the API in one terminal:

```bash
uvicorn backend.main:app --reload --port 8000
```

Start the frontend in a second terminal:

```bash
npm run dev
```

Open the local Vite URL printed by the dev server. Vite proxies `/api` to FastAPI. If the API is unavailable, the frontend uses labeled sample data.

## Optional live Qloo signals

Install the official harness (Node.js 22.19+ and `@qloo/qloo-harness` 0.1.26+), then configure its private credential store:

```bash
npm install --global @qloo/qloo-harness
qloo setup --qloo
qloo --version
```

Run the backend in Qloo mode:

```bash
CULTUREFORGE_PROVIDER=qloo uvicorn backend.main:app --reload --port 8000
```

The harness can also read `QLOO_API_KEY` from the backend process environment. Do not expose this variable through `VITE_*` variables. With no key and the default `auto` provider mode, the backend uses mock data. If a configured Qloo request fails, the API returns an error; it does not silently relabel the response as live or substitute mock data.

## Prototype journey

1. Overview landing page → **Start creating**.
2. Enter business type, audience, location, budget, and objectives.
3. Review the agent progress sequence.
4. Select among three concept proposals and inspect fit scores and supporting sample signals.
5. Compare scenarios by changing the target audience and applying the draft.

Mock-mode signals and all concept-fit scores, narratives, and scenario deltas are illustrative demo content, not validated business advice. In live mode, only the separate cultural signal list comes from Qloo. Qloo outputs describe aggregate affinities, not individual preferences or guaranteed behavior. See the [Qloo Hackathon Kit](https://github.com/qloo/qloo-hackathon-kit) API access and safe-use guidance before using live data.

## Studio interface

The interface includes persistent dark and light themes, a guided demo, a saved-concept collection (stored locally in the browser), concept blueprint dialogs, a concept comparison matrix, evidence tabs, and a Markdown brief export. The scenario lab includes audience presets and adjustable preference sliders; its scores are an explicitly illustrative model. Theme and saved concepts persist across reloads, while exploration data stays in memory for the prototype.

The landing page provides separate Product, Case Studies, and Contact views. Its background video is bundled locally at `assets/cultureforge-background.mp4` so playback does not depend on the original remote URL.

## Check mock generation

Run `npm run test:mock` after installing frontend dependencies and the Python requirements. It checks 120 backend/frontend parity cases across five business types, eight audience briefs, and three budget bands, along with category-specific concepts, mock provenance, and pilot-budget limits. Both runtimes use `shared/mockCatalog.json`; the backend generator is in `backend/mock_generator.py` and the offline generator is in `src/mockData.ts`.

Typography now uses 14–16px body and control text with larger card headings. Longer concept descriptions flow naturally, medium-width cards use a wider image/text layout, and mobile scenarios stack audience summaries vertically.
